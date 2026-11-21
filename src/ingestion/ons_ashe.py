"""Versioned ONS ASHE residence earnings; no geographic or vintage selection."""

from __future__ import annotations

import argparse
import collections
import http.client
import io
import json
import logging
import math
import re
import time
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

import openpyxl
import pandas as pd
import xlrd

from ingestion.boe import safe_http_headers, sha, verify_bundle
from ingestion.ons_pipr import load_geography_reference
from ingestion.source_io import (
    IngestionError,
    identifier,
    publish_tables,
    raw_source,
    storage_root,
)

VERSION = "ons-ashe-v1"
DATASET = "ons_ashe"
SOURCE_PATH = "/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8/"
USER_AGENT = "RentalForecasting-ASHE-Ingestion/1.0 (public statistical data)"
MARKERS = {"x", "..", ":", "-", ".", ""}
LOG = logging.getLogger(__name__)


def source_url(url: str) -> str:
    parsed = urlsplit(url)
    uri = parse_qs(parsed.query).get("uri", [])
    if (
        parsed.scheme != "https"
        or parsed.netloc != "www.ons.gov.uk"
        or parsed.path != "/file"
        or parsed.fragment
        or len(uri) != 1
        or not uri[0].startswith(SOURCE_PATH)
        or not uri[0].endswith(".zip")
        or ".." in uri[0].split("/")
    ):
        raise IngestionError("Expected an official ASHE Table 8 ZIP URL")
    return url


def fetch(url: str, *, sleep=time.sleep, opener=urlopen) -> tuple[bytes, dict]:
    """Serial caller; bounded retries honour seconds/date Retry-After up to 60s.

    A longer publisher wait stops this invocation rather than retrying early.
    HTTP 403 is terminal. No credentials or session headers are stored.
    """
    source_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    attempts = []
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with opener(Request(url, headers=headers), timeout=60) as response:
                source_url(response.url)
                if response.status != 200:
                    raise IngestionError("Unexpected source response status")
                body = response.read(128_000_001)
                length = response.headers.get("Content-Length")
                if (
                    not body
                    or len(body) > 128_000_000
                    or (length and int(length) != len(body))
                ):
                    raise IngestionError("Empty, oversized or incomplete ASHE response")
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
                        f"ASHE access denied/failed: HTTP {status}"
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
                    "ASHE download failed after three attempts"
                ) from exc
            LOG.warning(
                "Retrying ASHE source after %s seconds (attempt %s/3)",
                wait,
                attempt + 1,
            )
            sleep(wait)
    raise AssertionError("unreachable")


def load_inventory(path: Path) -> list[dict]:
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))["editions"]
        if not entries:
            raise ValueError("empty inventory")
        ids, urls = set(), set()
        for entry in entries:
            key = identifier(entry["edition_id"])
            url = source_url(entry["url"])
            year = entry["observation_year"]
            if (
                key in ids
                or url in urls
                or type(year) is not int
                or not 1990 <= year <= 2100
            ):
                raise ValueError("duplicate/invalid edition")
            if parse_qs(urlsplit(url).query)["uri"][0].split("/")[-2] != key:
                raise ValueError("edition identity differs from source URL")
            if (
                not entry["label"]
                or str(year) not in entry["label"]
                or str(year) not in key
            ):
                raise ValueError("edition year mismatch")
            if entry["status"] not in {
                "provisional",
                "revised",
                "methodological",
                "other",
            }:
                raise ValueError("invalid edition status")
            if (
                entry["status"] in {"provisional", "revised"}
                and entry["status"] not in entry["label"].lower()
            ):
                raise ValueError("edition label/status mismatch")
            stamp = entry.get("publication_date")
            if stamp and (
                datetime.strptime(stamp, "%Y-%m-%d").year < year
                or not entry.get("publication_evidence_url")
            ):
                raise ValueError("invalid publication evidence")
            ids.add(key)
            urls.add(url)
        return entries
    except (KeyError, ValueError, TypeError) as exc:
        raise IngestionError(f"Invalid ASHE edition inventory: {exc}") from exc


class Workbook:
    """Read only source values/styles; no Excel calculation or formula evaluation."""

    def __init__(self, name: str, body: bytes):
        self.modern = name.lower().endswith(".xlsx")
        try:
            if self.modern:
                self.book = openpyxl.load_workbook(
                    io.BytesIO(body), data_only=False, keep_links=False
                )
                self.names = self.book.sheetnames
            else:
                self.book = xlrd.open_workbook(file_contents=body, formatting_info=True)
                self.names = self.book.sheet_names()
        except Exception as exc:
            raise IngestionError(f"Cannot read ASHE workbook: {name}") from exc

    def rows(self, sheet):
        if self.modern:
            return [
                [cell.value for cell in row] for row in self.book[sheet].iter_rows()
            ]
        sheet = self.book.sheet_by_name(sheet)
        return [sheet.row_values(i) for i in range(sheet.nrows)]

    def style(self, sheet, row, column):
        if self.modern:
            cell = self.book[sheet].cell(row, column)
            color = cell.fill.fgColor
            return dict(
                style_id=cell.style_id,
                pattern=cell.fill.patternType,
                color_type=color.type,
                color=color.rgb if color.type == "rgb" else color.index,
                number_format=cell.number_format,
            )
        cell = self.book.sheet_by_name(sheet).cell(row - 1, column - 1)
        xf = self.book.xf_list[cell.xf_index]
        bg = xf.background
        return dict(
            style_id=cell.xf_index,
            pattern=bg.fill_pattern,
            palette_index=bg.pattern_colour_index,
            palette_rgb=self.book.colour_map.get(bg.pattern_colour_index),
            number_format=self.book.format_map[xf.format_key].format_str,
        )


def text(value):
    return "" if value is None else str(value)


def cell_value(value, *, cv=False):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value) or value < 0:
            raise IngestionError("Invalid negative/non-finite annual pay or CV")
        return float(value), None, "numeric"
    marker = text(value).strip()
    if marker not in MARKERS:
        raise IngestionError(f"Unexpected ASHE value/marker: {marker!r}")
    return None, marker, "missing" if marker in {"", "."} else "source_marker"


def parse_workbook(
    name: str, body: bytes, year: int, *, cv=False
) -> tuple[list, list, dict]:
    book = Workbook(name, body)
    if "All" not in book.names:
        raise IngestionError("Missing All worksheet")
    rows = book.rows("All")
    title = " | ".join(text(v) for v in rows[0] if v not in (None, ""))
    lower = title.lower()
    # Two independently reviewed XLS editions have this exact split title:
    # they omit year, currency and even the CV descriptor. Table number/member
    # identity and the verified annual-pay contract supply that evidence.
    known_split = (
        year in {2022, 2023}
        and title
        == f"Table 8.7{'b' if cv else 'a'} Annual pay - Gross | For all employee jobs(a): United Kingdom"
    )
    if not all(s in lower for s in ("annual pay", "gross", "all employee jobs")) or (
        "£" not in title and not known_split
    ):
        raise IngestionError("Wrong annual/gross/All/GBP workbook definition")
    if not known_split and cv != ("coefficients of variation" in lower):
        raise IngestionError("Pay/CV workbook identity mismatch")
    if not re.search(rf"8\s*\.7{'b' if cv else 'a'}\b", title):
        raise IngestionError("Wrong ASHE table identifier")
    years = re.findall(r"\b20\d{2}\b", title)
    if (years and years != [str(year)]) or str(year) not in name:
        raise IngestionError("Workbook/edition observation year mismatch")
    headings = [
        i
        for i, row in enumerate(rows)
        if len(row) > 3 and row[:2] == ["Description", "Code"] and row[3] == "Median"
    ]
    footers = [
        i
        for i, row in enumerate(rows)
        if row and re.match(r"a\s+Employees on adult rates", text(row[0]))
    ]
    if len(headings) != 1 or len(footers) != 1 or headings[0] >= footers[0]:
        raise IngestionError(
            "Missing/ambiguous table header or annual eligibility footnote"
        )
    header, end = headings[0], footers[0]
    population_conflict = "more than a year" not in text(rows[end][0])
    if population_conflict:
        annual_notes = [
            text(v)
            for sheet in book.names
            if "note" in sheet.lower()
            for row in book.rows(sheet)
            for v in row
            if "Annual estimates" in text(v)
            and "same job for more than a year" in text(v)
        ]
        if not (
            known_split
            and annual_notes
            and "not affected by absence" in text(rows[end][0])
        ):
            raise IngestionError("Annual employee population changed")
        # Source inconsistency, not a correction: preserve both notes and flag
        # it explicitly. No absence restriction is applied to annual estimates.
    data, identities = [], set()
    for index, row in enumerate(rows[header + 1 : end], header + 2):
        if not any(v not in (None, "") for v in row):
            continue
        if len(row) < 4 or not isinstance(row[0], str) or not row[0].strip():
            raise IngestionError("Invalid source observation row")
        code = text(row[1]).strip().lstrip("'")
        if code and not re.fullmatch(r"[A-Z0-9]{1,9}", code):
            raise IngestionError("Unexpected source geography code")
        identity = (code, row[0])
        if identity in identities:
            raise IngestionError("Duplicate source code/name identity")
        identities.add(identity)
        value, marker, state = cell_value(row[3], cv=cv)
        data.append(
            dict(
                source_row=index,
                source_name=row[0],
                source_code_raw=text(row[1]),
                source_code=code,
                value=value,
                marker=marker,
                value_state=state,
                source_value_text=text(row[3]),
                jobs_source_text=text(row[2]),
                style_json=json.dumps(book.style("All", index, 4), sort_keys=True),
            )
        )
    if not data:
        raise IngestionError("Empty ASHE table")
    notes = []
    for sheet in book.names:
        selected = (
            book.rows(sheet)
            if "note" in sheet.lower()
            else rows[end:] if sheet == "All" else []
        )
        first = 1 if "note" in sheet.lower() else end + 1
        notes.extend(
            dict(
                sheet=sheet,
                source_row=i,
                cells_json=json.dumps(row, ensure_ascii=False, default=str),
            )
            for i, row in enumerate(selected, first)
            if any(v not in (None, "") for v in row)
        )
    return (
        data,
        notes,
        dict(
            workbook=name,
            workbook_sha256=sha(body),
            title=title,
            sheets=book.names,
            header_row=header + 1,
            median_column="D",
            unit="percent" if cv else "GBP/year",
            unit_evidence=(
                "Task009.1_verified_split_schema_and_table_identity"
                if known_split
                else "source_title_and_table_identity"
            ),
            population_note_conflict=population_conflict,
            year_evidence=(
                "header_and_filename"
                if years
                else "inventory_and_filename_split_header"
            ),
        ),
    )


def parse_archive(
    body: bytes, entry: dict, cohort: dict
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 512_000_000:
                raise IngestionError("Oversized expanded ASHE archive")
            if (
                len(archive.namelist()) != len(set(archive.namelist()))
                or archive.testzip()
            ):
                raise IngestionError("Duplicate/corrupt ZIP members")
            members = []
            for suffix in ("a", "b"):
                candidates = [
                    n
                    for n in archive.namelist()
                    if re.search(rf"8\s*\.7{suffix}\b", n)
                    and re.search(r"Annual pay.*Gross", n, re.I)
                    and n.lower().endswith((".xls", ".xlsx"))
                ]
                if len(candidates) != 1:
                    raise IngestionError("Missing/ambiguous annual pay or CV workbook")
                member = candidates[0]
                prefix = Path(member).name.lower()
                if (prefix.startswith("prov") and entry["status"] == "revised") or (
                    prefix.startswith("revised") and entry["status"] == "provisional"
                ):
                    raise IngestionError(
                        "Workbook edition status conflicts with inventory"
                    )
                if archive.getinfo(member).file_size > 32_000_000:
                    raise IngestionError("Oversized ASHE workbook")
                members.append(member)
            pay, pay_notes, pay_proof = parse_workbook(
                members[0], archive.read(members[0]), entry["observation_year"]
            )
            cv, cv_notes, cv_proof = parse_workbook(
                members[1], archive.read(members[1]), entry["observation_year"], cv=True
            )
    except (zipfile.BadZipFile, KeyError, EOFError) as exc:
        raise IngestionError("Invalid/incomplete ASHE ZIP") from exc
    cv_lookup = {(r["source_code"], r["source_name"]): r for r in cv}
    if set(cv_lookup) != {(r["source_code"], r["source_name"]) for r in pay}:
        raise IngestionError("Pay/CV source identities do not align")
    result = []
    for row in pay:
        quality = cv_lookup[(row["source_code"], row["source_name"])]
        result.append(
            dict(
                source_row=row["source_row"],
                cv_source_row=quality["source_row"],
                source_name=row["source_name"],
                source_code_raw=row["source_code_raw"],
                source_code=row["source_code"],
                cv_source_code_raw=quality["source_code_raw"],
                annual_gross_median_gbp=row["value"],
                pay_source_text=row["source_value_text"],
                pay_marker=row["marker"],
                pay_state=row["value_state"],
                median_cv_percent=quality["value"],
                cv_source_text=quality["source_value_text"],
                cv_marker=quality["marker"],
                cv_state=quality["value_state"],
                pay_style_json=row["style_json"],
                cv_style_json=quality["style_json"],
                jobs_source_text=row["jobs_source_text"],
                exact_cohort_match=row["source_code"] in cohort,
                approved_name=cohort.get(row["source_code"]),
                source_name_differs=(
                    row["source_code"] in cohort
                    and row["source_name"].strip() != cohort[row["source_code"]]
                ),
            )
        )
    frame = pd.DataFrame(result)
    matched = frame[frame.exact_cohort_match]
    counts = collections.Counter(r["source_code"] for r in pay if r["source_code"])
    report = dict(
        edition_id=entry["edition_id"],
        observation_year=entry["observation_year"],
        source_rows=len(frame),
        coded_rows=int(frame.source_code.ne("").sum()),
        exact_cohort_matches=len(matched),
        numeric_cohort_medians=int(matched.annual_gross_median_gbp.notna().sum()),
        cohort_pay_markers=dict(collections.Counter(matched.pay_marker.dropna())),
        source_pay_markers=dict(collections.Counter(frame.pay_marker.dropna())),
        source_cv_markers=dict(collections.Counter(frame.cv_marker.dropna())),
        missing_cohort_codes=sorted(set(cohort) - set(matched.source_code)),
        source_codes_not_in_cohort=sorted(set(frame.source_code) - set(cohort) - {""}),
        name_differences=matched[matched.source_name_differs][
            ["source_code", "source_name", "approved_name"]
        ].to_dict("records"),
        legacy_code_collisions={c: n for c, n in counts.items() if n > 1},
        pay=pay_proof,
        cv=cv_proof,
    )
    if any(re.fullmatch(r"[A-Z]\d{8}", c) for c in report["legacy_code_collisions"]):
        raise IngestionError("Duplicate modern geography code")
    notes = pd.DataFrame(
        [dict(workbook=members[0], **n) for n in pay_notes]
        + [dict(workbook=members[1], **n) for n in cv_notes]
    )
    return frame, notes, report


def cached_source(cache: Path, url: str):
    """Explicit optional import; verify bundle checksums and exact official URL."""
    for path in sorted(cache.rglob("manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("identity", {}).get("url") != url:
            continue
        manifest = verify_bundle(path.parent)
        meta = manifest.get("retrieval", manifest)
        if meta.get("status") == 200:
            body = (path.parent / "response.bin").read_bytes()
            return body, dict(meta, acquisition="verified_local_official_response")
    raise IngestionError("No verified successful official ZIP found in supplied cache")


def ingest(
    root: Path,
    snapshot: str,
    *,
    inventory: Path = Path("configs/ons_ashe_editions.json"),
    reference: Path = Path("configs/ons_lad_apr2025_v2.csv"),
    source_cache: Path | None = None,
    downloader=fetch,
    sleep=time.sleep,
) -> dict:
    identifier(snapshot)
    entries = load_inventory(inventory)
    cohort = load_geography_reference(reference).eligible_names
    identity = dict(
        dataset=DATASET,
        snapshot_id=snapshot,
        inventory_sha256=sha(inventory.read_bytes()),
        geography_reference_sha256=sha(reference.read_bytes()),
        transformation_version=VERSION,
    )
    for layer in ("validated", "processed"):
        target = root / layer / DATASET / f"snapshot={snapshot}"
        if target.exists() and verify_bundle(target)["identity"] != identity:
            raise IngestionError("Immutable ASHE output request conflict")
    frames, notes, reports, sources = [], [], [], {}

    def acquire(url):
        if source_cache is not None:
            return cached_source(source_cache, url)
        sleep(1.5)
        return downloader(url)

    for entry in entries:
        key = entry["edition_id"]
        body, provenance = raw_source(
            root, DATASET, snapshot, key, entry["url"], acquire
        )
        frame, workbook_notes, report = parse_archive(body, entry, cohort)
        year = entry["observation_year"]
        attributes = dict(
            observation_year=year,
            reference_period_start=f"{year-1}-04-06",
            reference_period_end=f"{year}-04-05",
            source_edition_id=key,
            source_edition_label=entry["label"],
            source_edition_status=entry["status"],
            source_release_date=entry.get("publication_date"),
            publication_evidence_url=entry.get("publication_evidence_url"),
            availability_evidence=(
                "verified_release_date_not_exact_timestamp"
                if entry.get("publication_date")
                else "historical_availability_unverified"
            ),
            source_url=entry["url"],
            source_snapshot_id=snapshot,
            source_sha256=provenance["source_sha256"],
            retrieved_at=provenance["retrieval"]["retrieved_at"],
        )
        for name, value in attributes.items():
            frame[name] = value
            workbook_notes[name] = value
        frame["pay_workbook"] = report["pay"]["workbook"]
        frame["cv_workbook"] = report["cv"]["workbook"]
        frame["pay_workbook_sha256"] = report["pay"]["workbook_sha256"]
        frame["cv_workbook_sha256"] = report["cv"]["workbook_sha256"]
        frame["source_sheet"] = "All"
        frame["population_note_conflict"] = (
            report["pay"]["population_note_conflict"]
            or report["cv"]["population_note_conflict"]
        )
        frame["unit"] = "GBP/year"
        for field in ("annual_gross_median_gbp", "median_cv_percent"):
            frame[field] = pd.to_numeric(frame[field]).astype("float64")
        frames.append(frame)
        notes.append(workbook_notes)
        reports.append(report)
        sources[key] = provenance
    observations = pd.concat(frames, ignore_index=True)
    if observations.duplicated(["source_edition_id", "source_row"]).any():
        raise IngestionError("Duplicate edition/source-row key")
    coverage = pd.DataFrame(
        [
            dict(
                observation_year=r["observation_year"],
                source_edition_id=r["edition_id"],
                source_rows=r["source_rows"],
                coded_rows=r["coded_rows"],
                exact_cohort_matches=r["exact_cohort_matches"],
                numeric_cohort_medians=r["numeric_cohort_medians"],
                missing_cohort_codes_json=json.dumps(r["missing_cohort_codes"]),
                cohort_pay_markers_json=json.dumps(
                    r["cohort_pay_markers"], sort_keys=True
                ),
            )
            for r in reports
        ]
    )
    tables = dict(
        observations=observations,
        workbook_notes=pd.concat(notes, ignore_index=True),
        coverage=coverage,
    )
    info = dict(
        identity=identity,
        transformation_version=VERSION,
        sources=sources,
        validation=reports,
        exact_point_in_time=False,
        vintage_policy="Preserve all editions; modelling selection unapproved",
        geography_policy="Preserve original rows; harmonisation deferred to preprocessing",
        annual_population="Adult-rate employee jobs held for more than a year; annual pay includes absence-affected pay",
        licence_url="https://www.ons.gov.uk/help/terms-conditions",
        attribution="Source: Office for National Statistics; Crown copyright; OGL v3.0",
    )
    return publish_tables(root, DATASET, snapshot, tables, tables, info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    parser.add_argument(
        "--inventory", type=Path, default=Path("configs/ons_ashe_editions.json")
    )
    parser.add_argument(
        "--geography-reference",
        type=Path,
        default=Path("configs/ons_lad_apr2025_v2.csv"),
    )
    parser.add_argument(
        "--source-cache",
        type=Path,
        help="Optional directory of checksummed official response bundles",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        result = ingest(
            storage_root(args.config),
            args.snapshot_id,
            inventory=args.inventory,
            reference=args.geography_reference,
            source_cache=args.source_cache,
        )
        print(
            json.dumps(
                dict(
                    processed_path=result["processed_path"],
                    editions=len(result["validation"]),
                    source_rows=sum(r["source_rows"] for r in result["validation"]),
                ),
                indent=2,
            )
        )
    except (IngestionError, OSError, ValueError) as exc:
        parser.exit(1, f"ASHE ingestion failed: {exc}\n")


if __name__ == "__main__":
    main()
