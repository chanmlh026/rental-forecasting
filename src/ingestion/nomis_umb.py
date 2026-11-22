"""Immutable primary Nomis UMB source capture; no modelling or harmonisation."""

from __future__ import annotations

import argparse
import calendar
import csv
import io
import json
import math
import re
import time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
import http.client

import pandas as pd

from ingestion.boe import IngestionError, publish, safe_http_headers, sha, verify_bundle
from ingestion.ons_pipr import load_geography_reference
from ingestion.source_io import identifier, publish_tables, storage_root

DATASET = "nomis_umb"
VERSION = "nomis-umb-v1"
HOST = "https://www.nomisweb.co.uk"
BASE = HOST + "/api/v01/dataset/NM_127_1"
GEOGRAPHY_LABEL = "local authorities: district / unitary (as of April 2023)"
MONTHS = dict(
    zip("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), range(1, 13))
)
METADATA_URLS = {
    "definition": BASE + "/def.sdmx.json",
    "item": BASE + "/item.def.sdmx.json",
    "measures": BASE + "/measures.def.sdmx.json",
    "dates": BASE + "/time.def.sdmx.json",
    "geography_current": BASE + "/geography/2092957699TYPE424.def.sdmx.json",
    "overview": BASE + ".overview.json",
    "time_metadata": BASE + "/time.metadata.json",
    "item_metadata": BASE + "/item.metadata.json",
    "measures_metadata": BASE + "/measures.metadata.json",
    "dataset": HOST + "/datasets/umb",
    "copyright": HOST + "/home/copyright.asp",
    "terms": HOST + "/home/terms.asp",
}
REQUIRED = {
    "DATE",
    "DATE_CODE",
    "DATE_NAME",
    "GEOGRAPHY",
    "GEOGRAPHY_CODE",
    "GEOGRAPHY_NAME",
    "GEOGRAPHY_TYPE",
    "GEOGRAPHY_TYPECODE",
    "ITEM",
    "ITEM_NAME",
    "MEASURES",
    "MEASURES_NAME",
    "OBS_VALUE",
    "OBS_STATUS",
    "OBS_STATUS_NAME",
    "OBS_CONF",
    "OBS_CONF_NAME",
    "URN",
    "RECORD_COUNT",
    "RECORD_OFFSET",
}


def source_url(url: str) -> str:
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or p.netloc != "www.nomisweb.co.uk"
        or p.fragment
        or p.username
        or p.password
        or not p.path.startswith(
            ("/api/v01/dataset/NM_127_1", "/datasets/umb", "/home/")
        )
    ):
        raise IngestionError("Expected the official unauthenticated Nomis HTTPS source")
    if any(
        k.lower()
        in {"uid", "token", "key", "apikey", "api_key", "password", "signature"}
        for k in parse_qs(p.query)
    ):
        raise IngestionError("Credentials are not permitted in Nomis source requests")
    return url


def retrieval_metadata(meta: dict) -> dict:
    """Allowlist fields as well as headers, including injected-downloader metadata."""
    allowed = {
        "url",
        "resolved_url",
        "status",
        "retrieval_started_at",
        "retrieved_at",
        "acquisition",
        "source_cache_manifest_sha256",
    }
    result = {k: v for k, v in meta.items() if k in allowed}
    for k in ("url", "resolved_url"):
        if result.get(k):
            source_url(result[k])
    for k in ("request_headers", "response_headers"):
        if k in meta:
            result[k] = safe_http_headers(meta[k])
    if "prior_attempts" in meta:
        result["prior_attempts"] = [
            retrieval_metadata(m) for m in meta["prior_attempts"]
        ]
    return result


def fetch(url: str, *, opener=urlopen, sleep=time.sleep) -> tuple[bytes, dict]:
    source_url(url)
    headers = {
        "User-Agent": "RentalForecasting-UMB/1.0 (public aggregate statistics)",
        "Accept-Encoding": "identity",
    }
    attempts = []
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with opener(Request(url, headers=headers), timeout=60) as response:
                source_url(response.url)
                if response.status != 200:
                    raise IngestionError("Unexpected Nomis response status")
                body = response.read(32_000_001)
                length = response.headers.get("Content-Length")
                if (
                    not body
                    or len(body) > 32_000_000
                    or (length and int(length) != len(body))
                ):
                    raise IngestionError(
                        "Empty, oversized or incomplete Nomis response"
                    )
                return body, retrieval_metadata(
                    dict(
                        url=url,
                        resolved_url=response.url,
                        status=200,
                        request_headers=headers,
                        response_headers=dict(response.headers),
                        retrieval_started_at=started,
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                        prior_attempts=attempts,
                    )
                )
        except (OSError, URLError, http.client.HTTPException) as exc:
            status = exc.code if isinstance(exc, HTTPError) else None
            if status is not None and status not in {429, 500, 502, 503, 504}:
                raise IngestionError(f"Nomis access failed with HTTP {status}") from exc
            wait = float(2**attempt)
            if isinstance(exc, HTTPError):
                retry = exc.headers.get("Retry-After")
                if retry:
                    try:
                        wait = float(retry)
                    except ValueError:
                        try:
                            when = parsedate_to_datetime(retry)
                            if when.tzinfo is None:
                                raise ValueError("No HTTP-date timezone")
                            wait = (when - datetime.now(timezone.utc)).total_seconds()
                        except (ValueError, TypeError, OverflowError) as e:
                            raise IngestionError(
                                "Invalid Nomis Retry-After; stop"
                            ) from e
                    if not math.isfinite(wait) or wait > 60:
                        raise IngestionError(
                            "Nomis requests a longer wait; retry later"
                        )
                    wait = max(0.0, wait)
            attempts.append(
                dict(
                    status=status,
                    retrieval_started_at=started,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                )
            )
            if attempt == 2:
                raise IngestionError(
                    "Nomis transport failed after three attempts"
                ) from exc
            sleep(wait)
    raise AssertionError("unreachable")


def periods() -> list[str]:
    return [
        f"{y:04d}-{m:02d}"
        for y in range(2004, 2027)
        for m in (3, 6, 9, 12)
        if "2004-12" <= f"{y:04d}-{m:02d}" <= "2026-06"
    ]


def load_contract(path: Path) -> dict:
    expected = dict(
        dataset_id="NM_127_1",
        item="2",
        rate_measure="20100",
        confidence_measure="20701",
        geography_selector="2092957699TYPE424",
        geography_typecode="424",
        geography_label=GEOGRAPHY_LABEL,
        first_period="2004-12",
        last_period="2026-06",
        period_count=87,
        chunk_periods=20,
    )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise IngestionError("Invalid UMB source contract") from exc
    if value != expected:
        raise IngestionError(
            "UMB contract changed; a historical/family extension requires approval"
        )
    return value


def annotation(record: dict) -> dict:
    return {
        a["annotationtitle"]: a["annotationtext"]
        for a in record.get("annotations", {}).get("annotation", [])
    }


def codelist(body: bytes, name: str) -> list[dict]:
    try:
        d = json.loads(body)
        if d["structure"]["header"]["id"] != "NM_127_1":
            raise ValueError("dataset")
        lists = d["structure"]["codelists"]["codelist"]
        if len(lists) != 1 or lists[0]["id"] != "CL_127_1_" + name:
            raise ValueError("codelist")
        values = lists[0]["code"]
        if len({str(x["value"]) for x in values}) != len(values):
            raise ValueError("duplicate codes")
        return values
    except (ValueError, KeyError, TypeError) as exc:
        raise IngestionError(f"Invalid UMB {name} metadata") from exc


def reference_period(code: str, label: str) -> tuple[str, str]:
    m = re.fullmatch(r"([A-Z][a-z]{2}) (\d{4})[-\u2013]([A-Z][a-z]{2}) (\d{4})", label)
    if not re.fullmatch(r"\d{4}-(03|06|09|12)", code) or m is None:
        raise IngestionError(
            "Invalid quarterly end-month or rolling annual period label"
        )
    try:
        sm, sy, em, ey = MONTHS[m[1]], int(m[2]), MONTHS[m[3]], int(m[4])
        if f"{ey:04d}-{em:02d}" != code or ey * 12 + em - (sy * 12 + sm) != 11:
            raise ValueError("not an overlapping 12-month period")
        return (
            date(sy, sm, 1).isoformat(),
            date(ey, em, calendar.monthrange(ey, em)[1]).isoformat(),
        )
    except (KeyError, ValueError) as exc:
        raise IngestionError("Invalid rolling annual reference period") from exc


def parse_metadata(
    bodies: dict[str, bytes],
) -> tuple[pd.DataFrame, dict, pd.DataFrame, dict]:
    try:
        definition = json.loads(bodies["definition"])["structure"]["keyfamilies"][
            "keyfamily"
        ]
        if (
            len(definition) != 1
            or definition[0]["id"] != "NM_127_1"
            or definition[0]["name"]["value"].lower()
            != "model-based estimates of unemployment"
        ):
            raise ValueError("dataset definition")
        if {x["conceptref"] for x in definition[0]["components"]["dimension"]} != {
            "GEOGRAPHY",
            "ITEM",
            "MEASURES",
            "FREQ",
        }:
            raise ValueError("dimensions")
        items = {str(x["value"]): x for x in codelist(bodies["item"], "ITEM")}
        if items["2"]["description"]["value"] != "Unemployment rate (model based)":
            raise ValueError("item")
        measures = {
            str(x["value"]): x["description"]["value"].lower()
            for x in codelist(bodies["measures"], "MEASURES")
        }
        if measures.get("20100") != "value" or measures.get("20701") != "confidence":
            raise ValueError("measures")
        overview = json.loads(bodies["overview"])["overview"]
        if str(overview.get("restricted")).lower() != "false":
            raise ValueError("restricted source")
        dates = {str(x["value"]): x for x in codelist(bodies["dates"], "TIME")}
        if not set(periods()) <= set(dates):
            raise ValueError("approved periods missing")
        roster = {}
        gss_codes = set()
        for x in codelist(bodies["geography_current"], "GEOGRAPHY"):
            a = annotation(x)
            if (
                str(a["TypeCode"]) != "424"
                or a["TypeName"] != GEOGRAPHY_LABEL
                or not re.fullmatch(r"E\d{8}", a["GeogCode"])
            ):
                raise ValueError("geography family")
            if a["GeogCode"] in gss_codes:
                raise ValueError("duplicate source GSS code")
            gss_codes.add(a["GeogCode"])
            roster[str(x["value"])] = dict(
                code=a["GeogCode"], name=x["description"]["value"]
            )
        if not roster:
            raise ValueError("empty geography")
        entries = (
            json.loads(bodies["time_metadata"])["metadata"]
            .get("entries", {})
            .get("entry", [])
        )
        if isinstance(entries, dict):
            entries = [entries]
        revision_rows, mapped = [], {}
        for entry in entries:
            flags = ["source_publication_timezone_unverified"]
            start, end = str(entry.get("periodstart", "")), str(
                entry.get("periodend", "")
            )
            try:
                sd, ed = date.fromisoformat(start), date.fromisoformat(end)
                key = ed.strftime("%Y-%m")
                if ed.day != calendar.monthrange(ed.year, ed.month)[1]:
                    flags.append("metadata_period_end_not_month_end")
                if key in dates and (
                    sd.isoformat(),
                    ed.isoformat(),
                ) != reference_period(key, dates[key]["description"]["value"]):
                    flags.append("metadata_period_differs_from_reference_label")
            except (ValueError, IngestionError):
                key = ""
                flags.append("unresolved_or_placeholder_period_metadata")
            if key:
                mapped.setdefault(key, []).append(entry)
            revisions = entry.get("revisions", {}).get("revision", [])
            if isinstance(revisions, dict):
                revisions = [revisions]
            for i, revision in enumerate(revisions):
                revision_rows.append(
                    dict(
                        metadata_id=str(entry.get("id", "")),
                        metadata_period_start_raw=start,
                        metadata_period_end_raw=end,
                        period_code_from_metadata_end=key,
                        revision_index=i,
                        released_raw=str(revision.get("released", "")),
                        scheduled_raw=str(revision.get("scheduled", "")),
                        status=str(revision.get("status", "")),
                        certainty=str(revision.get("certainty", "")),
                        version_text=str(revision.get("version", "")),
                        source_metadata_json=json.dumps(entry, sort_keys=True),
                        revision_json=json.dumps(revision, sort_keys=True),
                        flags_json=json.dumps(flags),
                    )
                )
        rows = []
        for code in periods():
            x = dates[code]
            label = x["description"]["value"]
            start, end = reference_period(code, label)
            a = annotation(x)
            flags = ["source_publication_timezone_unverified"]
            if any(
                "apsStartDate" in str(v) or "apsEndDate" in str(v) for v in a.values()
            ):
                flags.append("placeholder_period_annotations")
            if code not in mapped:
                flags.append("no_matched_historical_time_metadata")
            rows.append(
                dict(
                    period_code=code,
                    period_label=label,
                    reference_period_start=start,
                    reference_period_end=end,
                    period_bounds_basis="validated_source_reference_label",
                    source_annotations_json=json.dumps(a, sort_keys=True),
                    source_time_metadata_json=json.dumps(
                        mapped.get(code, []), sort_keys=True
                    ),
                    source_revision_released_raw=str(
                        a.get("CurrentRevisionReleased", "")
                    ),
                    flags_json=json.dumps(flags),
                )
            )
        info = dict(
            source_dataset_version=str(definition[0]["version"]),
            source_dataset_annotations=annotation(definition[0]),
            source_overview=overview,
            advertised_periods_outside_contract=sorted(set(dates) - set(periods())),
            time_metadata_entries=len(entries),
            generic_units_not_rate_specific=True,
            item_metadata_notfound=json.loads(bodies["item_metadata"])
            .get("metadata", {})
            .get("notfound"),
            generic_measure_metadata_not_selected_item_definition=True,
        )
        rev_columns = [
            "metadata_id",
            "metadata_period_start_raw",
            "metadata_period_end_raw",
            "period_code_from_metadata_end",
            "revision_index",
            "released_raw",
            "scheduled_raw",
            "status",
            "certainty",
            "version_text",
            "source_metadata_json",
            "revision_json",
            "flags_json",
        ]
        return (
            pd.DataFrame(rows),
            roster,
            pd.DataFrame(revision_rows, columns=rev_columns),
            info,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise IngestionError(
            "UMB source identity/definition metadata failed validation"
        ) from exc


def parse_value(raw: str, status: str) -> tuple[float | None, str]:
    if not raw.strip():
        return None, "missing"
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None, "source_marker"
    if not number.is_finite() or not math.isfinite(float(number)):
        raise IngestionError("Non-finite Nomis numeric value")
    if status == "Q":
        raise IngestionError(
            "Numeric value conflicts with source missing-data status Q"
        )
    return float(number), "numeric"


def parse_chunk(
    body: bytes,
    requested: list[str],
    period_table: pd.DataFrame,
    roster: dict,
    provenance: dict,
    source_name: str,
) -> list[dict]:
    try:
        reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
        if (
            not reader.fieldnames
            or len(set(reader.fieldnames)) != len(reader.fieldnames)
            or not REQUIRED <= set(reader.fieldnames)
        ):
            raise ValueError("schema")
        rows = list(reader)
        expected = len(requested) * len(roster) * 2
        if not rows or len(rows) != expected or len(rows) > 25000:
            raise ValueError("incomplete or truncated request")
        bounds = period_table.set_index("period_code").to_dict("index")
        records = []
        keys = set()
        for i, r in enumerate(rows):
            if (
                None in r
                or any(v is None for v in r.values())
                or r["RECORD_COUNT"] != str(expected)
                or r["RECORD_OFFSET"] != str(i)
            ):
                raise ValueError("response completeness")
            code, gid, measure = r["DATE"], r["GEOGRAPHY"], r["MEASURES"]
            if (
                code not in requested
                or r["DATE_CODE"] != code
                or r["DATE_NAME"] != bounds[code]["period_label"]
            ):
                raise ValueError("period")
            if gid not in roster or (r["GEOGRAPHY_CODE"], r["GEOGRAPHY_NAME"]) != (
                roster[gid]["code"],
                roster[gid]["name"],
            ):
                raise ValueError("geography identity")
            if (
                r["GEOGRAPHY_TYPECODE"] != "424"
                or r["GEOGRAPHY_TYPE"] != GEOGRAPHY_LABEL
            ):
                raise ValueError("geographic vintage")
            if (
                r["ITEM"] != "2"
                or r["ITEM_NAME"] != "Unemployment rate (model based)"
                or measure not in {"20100", "20701"}
            ):
                raise ValueError("item/measure")
            if r["MEASURES_NAME"] != {"20100": "Value", "20701": "Confidence"}[
                measure
            ] or not r["URN"].lower().startswith("nm-127d1d"):
                raise ValueError("source identity")
            key = (code, gid, measure)
            if key in keys:
                raise ValueError("duplicate observation")
            keys.add(key)
            value, kind = parse_value(r["OBS_VALUE"], r["OBS_STATUS"])
            records.append(
                dict(
                    period_code=code,
                    period_label=r["DATE_NAME"],
                    reference_period_start=bounds[code]["reference_period_start"],
                    reference_period_end=bounds[code]["reference_period_end"],
                    source_geography_id=gid,
                    gss_code=r["GEOGRAPHY_CODE"],
                    source_name=r["GEOGRAPHY_NAME"],
                    source_geography_family="TYPE424",
                    source_geography_type=r["GEOGRAPHY_TYPE"],
                    item="2",
                    measure=measure,
                    value=value,
                    source_value_text=r["OBS_VALUE"],
                    value_kind=kind,
                    observation_status=r["OBS_STATUS"],
                    observation_status_name=r["OBS_STATUS_NAME"],
                    confidentiality_flag=r["OBS_CONF"],
                    confidentiality_name=r["OBS_CONF_NAME"],
                    source_urn=r["URN"],
                    source_record_json=json.dumps(r, sort_keys=True),
                    source_request_name=source_name,
                    source_url=provenance["identity"]["url"],
                    source_sha256=provenance["source_sha256"],
                    retrieved_at=provenance["retrieval"]["retrieved_at"],
                    source_snapshot_id=provenance["identity"]["snapshot_id"],
                )
            )
        if keys != {
            (p, g, m) for p in requested for g in roster for m in ("20100", "20701")
        }:
            raise ValueError("incomplete observation keys")
        return records
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise IngestionError(f"UMB CSV validation failed: {exc}") from exc


def outputs(
    records: list[dict],
    period_table: pd.DataFrame,
    roster: dict,
    revisions: pd.DataFrame,
    cohort: dict,
    metadata: pd.DataFrame,
) -> tuple[dict, list[dict]]:
    observations = (
        pd.DataFrame(records)
        .sort_values(["period_code", "source_geography_id", "measure"])
        .reset_index(drop=True)
    )
    observations["value"] = pd.to_numeric(observations.value).astype("float64")
    if observations.duplicated(
        ["period_code", "source_geography_id", "item", "measure"]
    ).any():
        raise IngestionError("Duplicate observation across source requests")
    observations["exact_cohort_code_match"] = observations.gss_code.isin(cohort)
    rates = []
    coverage = []
    for code, group in observations.groupby("period_code", sort=True):
        rate = group[group.measure == "20100"]
        conf = group[group.measure == "20701"]
        ci = conf.set_index("source_geography_id").to_dict("index")
        for r in rate.to_dict("records"):
            c = ci[r["source_geography_id"]]
            rates.append(
                {
                    **{
                        k: r[k]
                        for k in [
                            "period_code",
                            "period_label",
                            "reference_period_start",
                            "reference_period_end",
                            "source_geography_id",
                            "gss_code",
                            "source_name",
                            "source_geography_family",
                            "source_geography_type",
                            "source_snapshot_id",
                            "exact_cohort_code_match",
                        ]
                    },
                    "unemployment_rate_percent": r["value"],
                    "rate_source_text": r["source_value_text"],
                    "rate_value_kind": r["value_kind"],
                    "confidence_margin_percentage_points": c["value"],
                    "confidence_source_text": c["source_value_text"],
                    "confidence_value_kind": c["value_kind"],
                    "rate_obs_status": r["observation_status"],
                    "confidence_obs_status": c["observation_status"],
                    "rate_obs_conf": r["confidentiality_flag"],
                    "confidence_obs_conf": c["confidentiality_flag"],
                    "rate_source_urn": r["source_urn"],
                    "confidence_source_urn": c["source_urn"],
                    "source_url": r["source_url"],
                    "source_sha256": r["source_sha256"],
                    "retrieved_at": r["retrieved_at"],
                }
            )
        selected = rate[rate.exact_cohort_code_match]
        selected_conf = conf[conf.exact_cohort_code_match]
        coverage.append(
            dict(
                period_code=code,
                period_label=rate.iloc[0].period_label,
                source_areas=len(rate),
                source_observations=len(group),
                exact_cohort_matches=len(selected),
                numeric_cohort_rates=int(selected.value.notna().sum()),
                numeric_cohort_confidence=int(selected_conf.value.notna().sum()),
                numeric_source_rates=int(rate.value.notna().sum()),
                numeric_source_confidence=int(conf.value.notna().sum()),
                missing_numeric_cohort_rate_codes_json=json.dumps(
                    sorted(selected.loc[selected.value.isna(), "gss_code"])
                ),
                missing_numeric_cohort_confidence_codes_json=json.dumps(
                    sorted(selected_conf.loc[selected_conf.value.isna(), "gss_code"])
                ),
                unmatched_target_codes_json=json.dumps(
                    sorted(set(cohort) - set(rate.gss_code))
                ),
                unmatched_source_codes_json=json.dumps(
                    sorted(set(rate.gss_code) - set(cohort))
                ),
                observation_status_counts_json=json.dumps(
                    group.observation_status.value_counts().to_dict(), sort_keys=True
                ),
            )
        )
    names = {v: k for k, v in cohort.items()}
    geo = []
    source_codes = {x["code"] for x in roster.values()}
    for gid, x in roster.items():
        exact = x["code"] in cohort
        geo.append(
            dict(
                record_kind="published_source_area",
                source_geography_id=gid,
                source_code=x["code"],
                source_name=x["name"],
                exact_cohort_code_match=exact,
                same_name_target_code=names.get(x["name"], ""),
                relationship=(
                    "exact_code_match"
                    if exact
                    else (
                        "same_name_different_code"
                        if x["name"] in names
                        else "outside_target_cohort"
                    )
                ),
                target_name=cohort.get(x["code"], ""),
                mapping_applied=False,
            )
        )
    for code in sorted(set(cohort) - source_codes):
        geo.append(
            dict(
                record_kind="target_without_exact_source_code",
                source_geography_id="",
                source_code="",
                source_name="",
                exact_cohort_code_match=False,
                same_name_target_code=code,
                relationship="target_code_unmatched_not_source_missingness",
                target_name=cohort[code],
                mapping_applied=False,
            )
        )
    tables = dict(
        observations=observations,
        rates=pd.DataFrame(rates),
        coverage=pd.DataFrame(coverage),
        periods=period_table,
        geography_audit=pd.DataFrame(geo),
        revisions=revisions,
        metadata=metadata,
    )
    return tables, coverage


def cached_source(cache: Path, url: str) -> tuple[bytes, dict]:
    for path in sorted(cache.rglob("manifest.json")):
        source = json.loads(path.read_text(encoding="utf-8"))
        if source.get("identity", {}).get("url") != url:
            continue
        meta = verify_bundle(path.parent)
        if meta.get("status", meta.get("retrieval", {}).get("status")) != 200:
            continue
        body = (path.parent / "response.bin").read_bytes()
        retrieval = retrieval_metadata(meta.get("retrieval", meta))
        return body, {
            **retrieval,
            "acquisition": "verified_local_official_response",
            "source_cache_manifest_sha256": sha(path.read_bytes()),
        }
    raise IngestionError(
        "Required official response is absent from the explicit UMB source cache"
    )


def acquire(
    root: Path,
    snapshot: str,
    name: str,
    url: str,
    downloader,
    source_cache: Path | None,
    sleep,
) -> tuple[bytes, dict]:
    source_url(url)
    directory = root / "raw" / DATASET / f"snapshot={snapshot}" / identifier(name)
    identity = dict(dataset=DATASET, snapshot_id=snapshot, source=name, url=url)
    if directory.exists():
        manifest = verify_bundle(directory)
        if manifest.get("identity") != identity:
            raise IngestionError("Immutable UMB raw request conflict")
    else:
        if source_cache is not None and name not in {"terms"}:
            body, meta = cached_source(source_cache, url)
        else:
            sleep(1.5)
            body, meta = downloader(url)
        meta = retrieval_metadata(meta)
        if not body or meta.get("status") != 200 or not meta.get("retrieved_at"):
            raise IngestionError("Failed/incomplete UMB source acquisition")
        try:
            stamp = datetime.fromisoformat(meta["retrieved_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("No retrieval timezone")
        except (ValueError, TypeError) as exc:
            raise IngestionError("Invalid UTC retrieval evidence") from exc
        publish(
            directory,
            {"response.bin": body},
            dict(
                identity=identity,
                retrieval=meta,
                source_sha256=sha(body),
                request_parameters=parse_qs(urlsplit(url).query),
            ),
        )
        manifest = verify_bundle(directory)
    body = (directory / "response.bin").read_bytes()
    if manifest.get("source_sha256") != sha(body):
        raise IngestionError("UMB source checksum metadata conflict")
    return body, manifest


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data.strip())


def ingest(
    root: Path,
    snapshot: str,
    *,
    contract: Path = Path("configs/nomis_umb_contract.json"),
    reference: Path = Path("configs/ons_lad_apr2025_v2.csv"),
    source_cache: Path | None = None,
    downloader=fetch,
    sleep=time.sleep,
) -> dict:
    identifier(snapshot)
    cfg = load_contract(contract)
    cohort = load_geography_reference(reference).eligible_names
    identity = dict(
        dataset=DATASET,
        snapshot_id=snapshot,
        contract_sha256=sha(contract.read_bytes()),
        geography_reference_sha256=sha(reference.read_bytes()),
        transformation_version=VERSION,
    )
    for layer in ("validated", "processed"):
        target = root / layer / DATASET / f"snapshot={snapshot}"
        if target.exists() and verify_bundle(target).get("identity") != identity:
            raise IngestionError("Immutable UMB output request conflict")
    bodies = {}
    sources = {}
    for name, url in METADATA_URLS.items():
        bodies[name], sources[name] = acquire(
            root, snapshot, name, url, downloader, source_cache, sleep
        )
    period_table, roster, revisions, metadata_info = parse_metadata(bodies)
    parser = PlainText()
    parser.feed(bodies["copyright"].decode("utf-8-sig"))
    copyright_text = " ".join(parser.parts)
    if (
        "Open Government Licence" not in copyright_text
        or "Office for National Statistics" not in copyright_text
    ):
        raise IngestionError("Nomis reuse/attribution evidence requires review")
    step = min(cfg["chunk_periods"], 25000 // (len(roster) * 2))
    if step < 1:
        raise IngestionError("Source geography exceeds one-period API capacity")
    records = []
    for i in range(0, len(periods()), step):
        requested = periods()[i : i + step]
        name = f"history{i//step+1:02d}"
        params = dict(
            geography=cfg["geography_selector"],
            date=",".join(requested),
            item="2",
            measures="20100,20701",
            ExcludeMissingValues="false",
            ExcludeZeroValues="false",
        )
        url = BASE + ".data.csv?" + urlencode(params)
        body, meta = acquire(root, snapshot, name, url, downloader, source_cache, sleep)
        sources[name] = meta
        records.extend(parse_chunk(body, requested, period_table, roster, meta, name))
    # An online publication crossing a request window cannot silently become one snapshot.
    end_body, end_meta = acquire(
        root,
        snapshot,
        "overview_after",
        METADATA_URLS["overview"],
        downloader,
        source_cache,
        sleep,
    )
    sources["overview_after"] = end_meta
    bodies["overview_after"] = end_body
    end_overview = json.loads(end_body)["overview"]
    for key in ("lastupdated", "lastrevised"):
        if metadata_info["source_overview"].get(key) != end_overview.get(key):
            raise IngestionError(
                "Nomis release changed during snapshot; use a new snapshot ID"
            )
    metadata = []
    for name, body in bodies.items():
        if ".json" in METADATA_URLS.get(name, METADATA_URLS["overview"]):
            content = json.dumps(json.loads(body), sort_keys=True)
            kind = "source_json"
        else:
            parser = PlainText()
            parser.feed(body.decode("utf-8-sig"))
            content = " ".join(parser.parts)
            kind = "source_document_text"
        metadata.append(
            dict(
                source=name,
                kind=kind,
                content=content,
                url=sources[name]["identity"]["url"],
                source_sha256=sources[name]["source_sha256"],
                retrieved_at=sources[name]["retrieval"]["retrieved_at"],
            )
        )
    tables, coverage = outputs(
        records, period_table, roster, revisions, cohort, pd.DataFrame(metadata)
    )
    info = dict(
        identity=identity,
        transformation_version=VERSION,
        source_contract=cfg,
        sources=sources,
        metadata=metadata_info,
        validation=dict(
            periods=len(period_table),
            source_areas=len(roster),
            observations=len(records),
            rate_rows=len(tables["rates"]),
            coverage_by_period=coverage,
            source_markers=tables["observations"].value_kind.value_counts().to_dict(),
        ),
        time_interpretation="Quarterly publication of overlapping 12-month periods; no monthly aggregation",
        source_timestamp_timezone="unverified; source release/revision strings retained verbatim",
        exact_point_in_time=False,
        vintage_policy="Retain snapshots; no model-input vintage selected",
        geography_policy="Original TYPE424 codes; exact-code audit only; no mapping",
        population="Economically active residents aged 16 and over; published model-based rate",
        licence_url=METADATA_URLS["copyright"],
        terms_url=METADATA_URLS["terms"],
        attribution="Source: Office for National Statistics; Crown copyright; Open Government Licence",
        reference_baseline="Task 009.3; 296 areas/87 periods/51504 rows are findings, not future count thresholds",
    )
    return publish_tables(root, DATASET, snapshot, tables, tables, info)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot-id", required=True)
    p.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    p.add_argument(
        "--contract", type=Path, default=Path("configs/nomis_umb_contract.json")
    )
    p.add_argument(
        "--geography-reference",
        type=Path,
        default=Path("configs/ons_lad_apr2025_v2.csv"),
    )
    p.add_argument("--source-cache", type=Path)
    args = p.parse_args()
    result = ingest(
        storage_root(args.config),
        args.snapshot_id,
        contract=args.contract,
        reference=args.geography_reference,
        source_cache=args.source_cache,
    )
    print(
        json.dumps(
            {
                "dataset": DATASET,
                "snapshot_id": args.snapshot_id,
                "processed_path": result["processed_path"],
                "validation": {
                    k: v
                    for k, v in result["validation"].items()
                    if k != "coverage_by_period"
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
