"""Immutable native MHCLG PS1/PS2 planning statistics, without model features."""

from __future__ import annotations
import argparse
import calendar
import csv
import http.client
import io
import json
import logging
import math
import re
import time
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
import pandas as pd
from ingestion.boe import IngestionError, publish, safe_http_headers, sha, verify_bundle
from ingestion.ons_pipr import load_geography_reference
from ingestion.source_io import identifier, publish_tables, storage_root

DATASET = "mhclg_planning"
VERSION = "mhclg-planning-v1"
USER_AGENT = "RentalForecasting-MHCLG/1.0 (public aggregate statistics)"
LOG = logging.getLogger(__name__)
PAGE = "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics"
RELEASE = "https://www.gov.uk/government/statistics/planning-applications-in-england-april-to-june-2026"
DOCUMENT_URLS = {
    PAGE,
    RELEASE,
    RELEASE + "/planning-applications-in-england-april-to-june-2026-technical-notes",
    RELEASE
    + "/planning-applications-in-england-april-to-june-2026-statistical-release",
    "https://www.gov.uk/help/terms-conditions",
    "https://www.gov.uk/robots.txt",
}


def official_url(url):
    p = urlsplit(url)
    if p.scheme != "https" or p.query or p.fragment or p.username or p.password:
        raise IngestionError("Expected unauthenticated official planning HTTPS URL")
    if p.netloc == "www.gov.uk":
        if url not in DOCUMENT_URLS:
            raise IngestionError("Unexpected planning document URL")
    elif p.netloc == "assets.publishing.service.gov.uk":
        if not re.fullmatch(
            r"/media/[A-Za-z0-9_-]+/(PS[12][A-Za-z0-9_.-]*[.]csv|District_Matters_-_Data_dictionary[.]pdf)",
            p.path,
        ):
            raise IngestionError("Unexpected planning asset identity")
    else:
        raise IngestionError("Unofficial planning host")
    return url


class OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, *, sleep=time.sleep, opener=None) -> tuple[bytes, dict]:
    """Serial caller; bounded retries honour seconds/date Retry-After up to 60s.

    A longer publisher wait stops this invocation rather than retrying early.
    HTTP 403 is terminal. No credentials or session headers are stored.
    """
    official_url(url)
    opener = opener or build_opener(OfficialRedirect()).open
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    attempts = []
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with opener(Request(url, headers=headers), timeout=60) as response:
                official_url(response.url)
                if response.status != 200:
                    raise IngestionError("Unexpected source response status")
                body = response.read(128_000_001)
                length = response.headers.get("Content-Length")
                if (
                    not body
                    or len(body) > 128_000_000
                    or (length and int(length) != len(body))
                ):
                    raise IngestionError(
                        "Empty, oversized or incomplete MHCLG planning response"
                    )
                return body, dict(
                    url=url,
                    resolved_url=response.url,
                    status=200,
                    request_headers=headers,
                    response_headers=safe_http_headers(response.headers),
                    retrieval_started_at=started,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    prior_attempts=attempts,
                )
        except (OSError, URLError, http.client.HTTPException) as exc:
            status = exc.code if isinstance(exc, HTTPError) else None
            wait = 2**attempt
            record = dict(
                status=status,
                retrieval_started_at=started,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
            if isinstance(exc, HTTPError):
                record["response_headers"] = safe_http_headers(exc.headers)
                retry = exc.headers.get("Retry-After")
                exc.close()
                if status not in {429, 500, 502, 503, 504}:
                    raise IngestionError(
                        f"MHCLG planning access denied/failed: HTTP {status}"
                    ) from exc
                if retry:
                    try:
                        wait = (
                            int(retry)
                            if retry.isdigit()
                            else math.ceil(
                                (
                                    parsedate_to_datetime(retry)
                                    - datetime.now(timezone.utc)
                                ).total_seconds()
                            )
                        )
                        wait = max(0, wait)
                    except (TypeError, ValueError, OverflowError) as error:
                        raise IngestionError(
                            "Invalid publisher Retry-After; stop"
                        ) from error
                    if wait > 60:
                        raise IngestionError(
                            "Publisher Retry-After exceeds 60s; stop and resume later"
                        ) from exc
            attempts.append(record)
            if attempt == 2:
                raise IngestionError(
                    "MHCLG planning download failed after three attempts"
                ) from exc
            LOG.warning(
                "Retrying MHCLG planning source after %s seconds (attempt %s/3)",
                wait,
                attempt + 1,
            )
            sleep(wait)
    raise AssertionError("unreachable")


def acquire(root, snapshot, name, url, downloader=fetch):
    official_url(url)
    directory = (
        root / "raw" / DATASET / f"snapshot={identifier(snapshot)}" / identifier(name)
    )
    identity = dict(dataset=DATASET, snapshot_id=snapshot, source=name, url=url)
    if directory.exists():
        meta = verify_bundle(directory)
        if meta.get("identity") != identity:
            raise IngestionError("Immutable MHCLG planning request conflict")
    else:
        time.sleep(1.0)
        body, meta = downloader(url)
        if not body or meta.get("status") != 200 or not meta.get("retrieved_at"):
            raise IngestionError("Failed/incomplete MHCLG planning source response")
        publish(
            directory,
            {"response.bin": body},
            dict(identity=identity, retrieval=meta, source_sha256=sha(body)),
        )
        meta = verify_bundle(directory)
    body = (directory / "response.bin").read_bytes()
    if meta.get("source_sha256") != sha(body):
        raise IngestionError("MHCLG planning raw checksum metadata conflict")
    return body, meta


def load_inventory(path):
    try:
        contract = json.loads(Path(path).read_text(encoding="utf-8"))
        sources = contract["sources"]
        documents = contract["documents"]
        names = [s["edition_id"] for s in sources] + list(documents)
        if not sources or len(names) != len(set(names)):
            raise ValueError("Duplicate or empty inventory")
        for name in names:
            identifier(name)
        for doc in list(documents.values()) + sources:
            official_url(doc["url"])
            if not re.fullmatch(r"[0-9a-f]{64}", doc["source_sha256"]):
                raise ValueError("Invalid source checksum")
        for source in sources:
            columns = source["columns"]
            if source["table"] not in {"PS1", "PS2"} or source["kind"] not in {
                "full",
                "recent",
            }:
                raise ValueError("Unknown planning source")
            if (
                columns[:4] != ["Region", "LPANM", "LPACD", "Quarter"]
                or len(columns) != len(set(columns))
                or not all(columns)
            ):
                raise ValueError("Invalid planning columns")
            if any(
                c.startswith("source_")
                or c.startswith("exact_")
                or c.startswith("period_")
                for c in columns
            ):
                raise ValueError("Reserved source columns")
            required = (
                {
                    "Applications received",
                    "Applications decided",
                    "Applications withdrawn",
                }
                if source["table"] == "PS1"
                else {
                    action + "; " + category + " (all)"
                    for action in ["Total decisions", "Total granted", "Total refused"]
                    for category in ["major dwellings", "minor dwellings"]
                }
            )
            if not required.issubset(columns):
                raise ValueError("Required original planning measures missing")
            if "F_Year" not in columns or not source["preamble"]:
                raise ValueError("Missing original metadata")
        return contract
    except (KeyError, ValueError, TypeError) as exc:
        raise IngestionError("Invalid planning inventory") from exc


def quarter_period(text):
    m = re.fullmatch(r"([0-9]{4}) Q([1-4])", text)
    if not m:
        raise IngestionError("Invalid original reporting quarter")
    year, quarter = map(int, m.groups())
    month = quarter * 3
    return (
        date(year, month - 2, 1).isoformat(),
        date(year, month, calendar.monthrange(year, month)[1]).isoformat(),
    )


def parse_source(body, source, meta, cohort):
    """Retain every native field and parse count columns without filling gaps."""
    try:
        reader = csv.reader(io.StringIO(body.decode("cp1252")), strict=True)
        for expected in source["preamble"]:
            if next(reader) != expected:
                raise IngestionError("Planning source preamble changed")
        columns = next(reader)
        if columns != source["columns"]:
            raise IngestionError("Planning source schema changed")
        rows, line_ends = [], []
        for row in reader:
            if len(row) != len(columns):
                raise IngestionError("Ragged planning source row")
            rows.append(row)
            line_ends.append(reader.line_num)
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise IngestionError("Invalid/truncated planning CSV") from exc
    if not rows:
        raise IngestionError("Empty planning source")
    raw = pd.DataFrame(rows, columns=columns)
    duplicate_payload = raw.duplicated(columns, keep=False)
    authority_collision = raw.duplicated(["LPACD", "Quarter"], keep=False)
    if raw.LPACD.eq("").any() or raw.LPANM.eq("").any():
        raise IngestionError("Missing original planning authority identifier")
    periods = {q: quarter_period(q) for q in raw.Quarter.unique()}
    for key, value in {
        "source_edition_id": source["edition_id"],
        "source_table": source["table"],
        "source_kind": source["kind"],
        "source_url": source["url"],
        "source_sha256": sha(body),
        "source_retrieved_at": meta["retrieval"]["retrieved_at"],
        "source_record": range(
            len(source["preamble"]) + 2, len(source["preamble"]) + 2 + len(raw)
        ),
        "source_line_end": line_ends,
        "source_authority_period_collision": authority_collision,
        "source_duplicate_payload": duplicate_payload,
        "source_code_is_gss": raw.LPACD.str.fullmatch(r"E[0-9]{8}"),
        "period_start": raw.Quarter.map(lambda q: periods[q][0]),
        "period_end": raw.Quarter.map(lambda q: periods[q][1]),
        "exact_cohort_code_match": raw.LPACD.isin(cohort),
    }.items():
        raw[key] = value
    numeric = raw.copy()
    measures = [c for c in columns[4:] if c != "F_Year"]
    for c in measures:
        valid = raw[c].str.fullmatch(r"-?[0-9]+")
        if (~valid & ~raw[c].isin(["..", ""])).any():
            raise IngestionError("Unknown planning numeric value/quality marker: " + c)
        numeric[c] = pd.to_numeric(raw[c].where(valid), errors="raise").astype(
            "float64"
        )
    return raw, numeric


def audit_tables(raw, numeric, source, cohort):
    measures = [c for c in source["columns"][4:] if c != "F_Year"]
    coverage = []
    for period, group in raw.groupby("Quarter", sort=True):
        codes = set(group.LPACD)
        matched = group[group.exact_cohort_code_match]
        item = dict(
            edition_id=source["edition_id"],
            table=source["table"],
            period=period,
            source_rows=len(group),
            source_codes=len(codes),
            exact_cohort_matches=matched.LPACD.nunique(),
            exact_cohort_source_rows=len(matched),
            missing_gss_code_rows=int((~group.source_code_is_gss).sum()),
            authority_period_collision_rows=int(
                group.source_authority_period_collision.sum()
            ),
            duplicate_payload_rows=int(group.source_duplicate_payload.sum()),
            unmatched_target_codes_json=json.dumps(sorted(set(cohort) - codes)),
            noncohort_source_codes_json=json.dumps(sorted(codes - set(cohort))),
            source_missing_cells=int(group[measures].isin(["..", ""]).sum().sum()),
            numeric_source_cells=int(
                numeric.loc[group.index, measures].notna().sum().sum()
            ),
        )
        for name, col in [
            ("major_residential_granted", "Total granted; major dwellings (all)"),
            ("minor_residential_granted", "Total granted; minor dwellings (all)"),
            ("applications_decided", "Applications decided"),
        ]:
            if col in measures:
                item[name + "_numeric_cohort"] = int(
                    matched.loc[
                        numeric.loc[matched.index, col].notna(), "LPACD"
                    ].nunique()
                )
        coverage.append(item)
    geography = raw[
        [
            "LPACD",
            "LPANM",
            "Region",
            "Quarter",
            "source_record",
            "exact_cohort_code_match",
            "source_authority_period_collision",
            "source_duplicate_payload",
            "source_code_is_gss",
        ]
    ].copy()
    geography["edition_id"] = source["edition_id"]
    geography["mapping_applied"] = False
    schema = [
        dict(
            edition_id=source["edition_id"],
            source_column=i + 1,
            source_label=c,
            value_type="count" if c in measures else "original_identifier_or_period",
            unit=(
                "applications_decisions_or_actions_as_labelled_not_dwelling_units"
                if c in measures
                else "source_text"
            ),
            original_non_numeric_tokens_json=(
                json.dumps(
                    raw[c][~raw[c].str.fullmatch(r"-?[0-9]+")].value_counts().to_dict(),
                    sort_keys=True,
                )
                if c in measures
                else "{}"
            ),
        )
        for i, c in enumerate(source["columns"])
    ]
    return coverage, geography, schema


def ingest(
    root,
    snapshot,
    *,
    inventory=Path("configs/mhclg_planning_sources.json"),
    reference=Path("configs/ons_lad_apr2025_v2.csv"),
    downloader=fetch,
):
    root = Path(root)
    identifier(snapshot)
    contract = load_inventory(inventory)
    cohort = load_geography_reference(reference).eligible_names
    identity = dict(
        dataset=DATASET,
        snapshot_id=snapshot,
        inventory_sha256=sha(Path(inventory).read_bytes()),
        geography_reference_sha256=sha(Path(reference).read_bytes()),
        transformation_version=VERSION,
    )
    for layer in ["validated", "processed"]:
        target = root / layer / DATASET / ("snapshot=" + snapshot)
        if target.exists() and verify_bundle(target).get("identity") != identity:
            raise IngestionError("Immutable planning output identity conflict")
    tables, sources, documents, coverage, geos, schema = {}, {}, [], [], [], []
    for name, doc in contract["documents"].items():
        body, meta = acquire(root, snapshot, name, doc["url"], downloader)
        sources[name] = meta
        if sha(body) != doc["source_sha256"]:
            raise IngestionError(
                "Planning source document changed; review a new snapshot"
            )
        text = (
            body.decode("utf-8-sig")
            if not doc["url"].endswith(".pdf")
            else "PDF retained in immutable raw bundle"
        )
        dates = {}
        for field in ["first-published-at", "public-updated-at", "updated-at"]:
            match = re.search(
                r'<meta name="govuk:' + field + r'" content="([^"]+)">', text
            )
            dates[field] = match.group(1) if match else None
        documents.append(
            dict(
                source=name,
                source_url=doc["url"],
                source_sha256=sha(body),
                first_published_at=dates["first-published-at"],
                public_updated_at=dates["public-updated-at"],
                internal_updated_at=dates["updated-at"],
                retrieved_at=meta["retrieval"]["retrieved_at"],
                content=text,
            )
        )
    if not any(
        d["source"] == "terms" and "Open Government Licence" in d["content"]
        for d in documents
    ):
        raise IngestionError("Planning licence evidence requires review")
    counts = {}
    for source in contract["sources"]:
        key = source["edition_id"]
        body, meta = acquire(root, snapshot, key, source["url"], downloader)
        sources[key] = meta
        if sha(body) != source["source_sha256"]:
            raise IngestionError(
                "Planning CSV changed; retain snapshot and review inventory"
            )
        raw, numeric = parse_source(body, source, meta, cohort)
        tables[key + "_source"] = raw
        tables[key + "_values"] = numeric
        cov, geo, structure = audit_tables(raw, numeric, source, cohort)
        coverage.extend(cov)
        geos.append(geo)
        schema.extend(structure)
        measures = [c for c in source["columns"][4:] if c != "F_Year"]
        counts[key] = dict(
            authority_quarter_rows=len(raw),
            count_fields=len(measures),
            source_cells=len(raw) * len(measures),
            numeric_cells=int(numeric[measures].notna().sum().sum()),
            missing_markers=int(raw[measures].isin(["..", ""]).sum().sum()),
            authority_period_collision_rows=int(
                raw.source_authority_period_collision.sum()
            ),
            duplicate_payload_rows=int(raw.source_duplicate_payload.sum()),
            missing_gss_code_rows=int((~raw.source_code_is_gss).sum()),
            first_period=min(raw.Quarter),
            last_period=max(raw.Quarter),
            quarters=raw.Quarter.nunique(),
        )
    tables.update(
        coverage=pd.DataFrame(coverage),
        geography_audit=pd.concat(geos, ignore_index=True),
        schema=pd.DataFrame(schema),
        documents=pd.DataFrame(documents),
    )
    info = dict(
        identity=identity,
        sources=sources,
        source_contract=contract,
        validation=counts,
        source_value_policy="All native count fields parsed; all source strings/identifiers/financial-year labels retained separately; no fills or corrections",
        geography_policy="Original LPA identifiers and responsibilities; exact code audit only, no harmonisation",
        quality_policy="Original .. and blank markers preserved; publisher imputation/revision notes retained; absent cell-level flags do not establish unimputed values",
        publication_policy="Current release documents retained separately; historical first publication/correction dates not inferred from reporting quarter, file name or retrieval",
        exact_point_in_time=False,
        licence="Crown copyright / MHCLG; OGL v3.0 with attribution and exceptions; no third-party local extract rights inferred",
    )
    return publish_tables(root, DATASET, snapshot, tables, tables, info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    parser.add_argument(
        "--inventory", type=Path, default=Path("configs/mhclg_planning_sources.json")
    )
    parser.add_argument(
        "--geography-reference",
        type=Path,
        default=Path("configs/ons_lad_apr2025_v2.csv"),
    )
    args = parser.parse_args()
    info = ingest(
        storage_root(args.config),
        args.snapshot_id,
        inventory=args.inventory,
        reference=args.geography_reference,
    )
    print(json.dumps({k: info[k] for k in ["validation", "processed_path"]}, indent=2))


if __name__ == "__main__":
    main()
