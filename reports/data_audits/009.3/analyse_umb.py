"""Offline UMB research aggregates; never writes production tables or features."""

import collections
import csv
import io
import json
import math
from html.parser import HTMLParser
from pathlib import Path

from ingestion.boe import safe_http_headers, verify_bundle
from investigate_umb import RAW, OUT


def read(name):
    return json.loads((RAW / name / "response.bin").read_text(encoding="utf-8-sig"))


def csv_rows(name):
    body = (RAW / name / "response.bin").read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(body)))
    assert rows and None not in rows[0]
    return rows


def numeric(row):
    return row["OBS_VALUE"] != "" and math.isfinite(float(row["OBS_VALUE"]))


def codes(name):
    return read(name)["structure"]["codelists"]["codelist"][0]["code"]


def annotations(record):
    return {
        a["annotationtitle"]: a["annotationtext"]
        for a in record.get("annotations", {}).get("annotation", [])
    }


def summary(rows, cohort):
    rates = [r for r in rows if r["MEASURES"] == "20100"]
    confidence = [r for r in rows if r["MEASURES"] == "20701"]
    selected = [r for r in rates if r["GEOGRAPHY_CODE"] in cohort]
    selected_conf = [r for r in confidence if r["GEOGRAPHY_CODE"] in cohort]
    values = [float(r["OBS_VALUE"]) for r in selected if numeric(r)]
    conf_values = [float(r["OBS_VALUE"]) for r in selected_conf if numeric(r)]
    return dict(
        source_authorities=len(rates),
        exact_cohort_rows=len(selected),
        numeric_cohort_rates=sum(numeric(r) for r in selected),
        numeric_cohort_confidence=sum(numeric(r) for r in selected_conf),
        missing_cohort_codes=sorted(
            set(cohort) - {r["GEOGRAPHY_CODE"] for r in selected}
        ),
        missing_rate_codes=[r["GEOGRAPHY_CODE"] for r in selected if not numeric(r)],
        missing_confidence_codes=[
            r["GEOGRAPHY_CODE"] for r in selected_conf if not numeric(r)
        ],
        source_missing_rates=[
            dict(
                code=r["GEOGRAPHY_CODE"],
                name=r["GEOGRAPHY_NAME"],
                status=r["OBS_STATUS"],
            )
            for r in rates
            if not numeric(r)
        ],
        unmatched_source_codes=sorted(
            {r["GEOGRAPHY_CODE"] for r in rates} - set(cohort)
        ),
        cohort_rate_range=[min(values), max(values)] if values else None,
        published_confidence_field_range=(
            [min(conf_values), max(conf_values)] if conf_values else None
        ),
        statuses=dict(collections.Counter(r["OBS_STATUS"] for r in rows)),
        name_differences=[
            dict(
                code=r["GEOGRAPHY_CODE"],
                source_name=r["GEOGRAPHY_NAME"],
                approved_name=cohort[r["GEOGRAPHY_CODE"]],
            )
            for r in selected
            if r["GEOGRAPHY_NAME"] != cohort[r["GEOGRAPHY_CODE"]]
        ],
    )


def main():
    reference = list(
        csv.DictReader(
            Path("configs/ons_lad_apr2025_v2.csv").open(encoding="utf-8-sig")
        )
    )
    cohort = {
        r["gss_code"]: r["local_authority_name"]
        for r in reference
        if r["target_eligible"] == "true"
    }
    assert len(cohort) == 294
    periods = codes("dates")
    month_indices = [int(p["value"][:4]) * 12 + int(p["value"][5:]) for p in periods]
    assert all(b - a == 3 for a, b in zip(month_indices, month_indices[1:]))
    rows, requests = [], []
    for path in sorted(RAW.glob("history*/manifest.json")):
        meta = verify_bundle(path.parent)
        assert meta["status"] == 200
        chunk = csv_rows(path.parent.name)
        assert len(chunk) == int(chunk[0]["RECORD_COUNT"])
        assert [int(r["RECORD_OFFSET"]) for r in chunk] == list(range(len(chunk)))
        assert len(chunk) <= 25000
        requests.append(
            dict(
                url=meta["identity"]["url"],
                rows=len(chunk),
                source_sha256=meta["checksums"]["response.bin"],
            )
        )
        rows.extend(chunk)
    assert len(rows) == 296 * len(periods) * 2 == 51504
    keys = [(r["DATE"], r["GEOGRAPHY"], r["ITEM"], r["MEASURES"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert {r["ITEM"] for r in rows} == {"2"}
    assert {r["ITEM_NAME"] for r in rows} == {"Unemployment rate (model based)"}
    assert {r["GEOGRAPHY_TYPECODE"] for r in rows} == {"424"}
    assert {r["OBS_CONF"] for r in rows} == {"F"}
    assert all(r["OBS_STATUS"] == ("A" if numeric(r) else "Q") for r in rows)
    assert all(0 <= float(r["OBS_VALUE"]) <= 100 for r in rows if numeric(r))
    period_results = []
    for period in periods:
        selected = [r for r in rows if r["DATE"] == period["value"]]
        assert len(selected) == 296 * 2
        assert {r["DATE_NAME"] for r in selected} == {period["description"]["value"]}
        period_results.append(
            dict(
                date_code=period["value"],
                reference_period=period["description"]["value"],
                source_period_annotations=annotations(period),
                **summary(selected, cohort),
            )
        )
    legacy = csv_rows("legacy_sample")
    legacy_results = [
        dict(
            date_code=period,
            **summary([r for r in legacy if r["DATE"] == period], cohort),
        )
        for period in sorted({r["DATE"] for r in legacy})
    ]
    # Separate diagnostic counts, never used to derive the unemployment rate.
    latest = csv_rows("latest_counts")
    lookup = {(r["GEOGRAPHY_CODE"], r["ITEM"], r["MEASURES"]): r for r in latest}
    examples = [
        lookup[("E06000001", item, measure)]
        for item in ("1", "2")
        for measure in ("20100", "20701")
    ]
    assert [r["OBS_VALUE"] for r in examples] == ["2300", "600", "5.5", "1.6"]

    class OfficialTable(HTMLParser):
        def __init__(self):
            super().__init__()
            self.values, self.active = [], False

        def handle_starttag(self, tag, attrs):
            if tag == "td" and "cDc" in dict(attrs).get("class", "").split():
                self.active = True

        def handle_endtag(self, tag):
            if tag == "td":
                self.active = False

        def handle_data(self, data):
            if self.active:
                self.values.append(data.strip().replace(",", ""))

    independent = OfficialTable()
    independent.feed(
        (RAW / "independent_table/response.bin").read_text(encoding="utf-8")
    )
    assert independent.values == [r["OBS_VALUE"] for r in examples]
    for record in latest:
        if record["ITEM"] == "2":
            counterpart = next(
                r
                for r in rows
                if r["DATE"] == record["DATE"]
                and r["GEOGRAPHY"] == record["GEOGRAPHY"]
                and r["MEASURES"] == record["MEASURES"]
            )
            assert record["OBS_VALUE"] == counterpart["OBS_VALUE"]
            assert record["OBS_STATUS"] == counterpart["OBS_STATUS"]
    bundles = 0
    for path in RAW.glob("*/manifest.json"):
        meta = verify_bundle(path.parent)
        assert meta.get("response_headers", {}) == safe_http_headers(
            meta.get("response_headers", {})
        )
        bundles += 1
    overview = read("overview")["overview"]
    time_dim = next(
        d for d in overview["dimensions"]["dimension"] if d["concept"] == "time"
    )
    revision_records = []
    for period in time_dim["codes"]["code"]:
        revisions = period.get("revisions", {}).get("revision", [])
        if isinstance(revisions, dict):
            revisions = [revisions]
        revision_records.append(
            dict(
                date_code=period["value"],
                reference_period=period["name"],
                revisions=revisions,
            )
        )
    metadata = read("time_metadata")["metadata"]["entries"]["entry"]
    result = dict(
        status="pass",
        purpose="Research only; direct GSS comparison, no harmonisation, ratios or model-input vintage selection",
        dataset="NM_127_1 / UMB",
        source_geography_family="English district/unitary as of April 2023 (TYPE424)",
        item_rate=2,
        measure_value=20100,
        measure_confidence=20701,
        advertised_periods=len(periods),
        source_observation_rows=len(rows),
        complete_request_counts=True,
        unique_keys=True,
        verified_raw_bundles=bundles,
        raw_statuses=dict(collections.Counter(r["OBS_STATUS"] for r in rows)),
        full_history_requests=requests,
        coverage_by_period=period_results,
        older_geography_type464_sample=legacy_results,
        latest_hartlepool_official_records=examples,
        independent_latest_count_query_rate_rows_match=True,
        independent_official_html_table_matches_csv=True,
        date_inventory_quarterly_continuity_verified=True,
        source_overview={
            k: overview[k]
            for k in (
                "firstreleased",
                "lastupdated",
                "lastrevised",
                "nextupdate",
                "restricted",
                "status",
                "units",
            )
        },
        metadata_entry_count=len(metadata),
        metadata_placeholder_entries=[
            m
            for m in metadata
            if "aps" in m.get("periodstart", "") or "aps" in m.get("periodend", "")
        ],
        source_time_metadata=metadata,
        revision_inventory=revision_records,
    )
    (OUT / "validation-evidence.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "PASS",
        len(rows),
        "rows;",
        len(periods),
        "periods;",
        bundles,
        "verified immutable bundles",
    )
    print(
        "Coverage changes:",
        sorted(
            {
                (
                    r["exact_cohort_rows"],
                    r["numeric_cohort_rates"],
                    r["numeric_cohort_confidence"],
                    tuple(r["missing_cohort_codes"]),
                )
                for r in period_results
            }
        ),
    )
    print("Latest:", json.dumps(period_results[-1], indent=2))
    print(
        "Legacy:",
        [
            (
                r["date_code"],
                r["exact_cohort_rows"],
                r["numeric_cohort_rates"],
                r["numeric_cohort_confidence"],
            )
            for r in legacy_results
        ],
    )


if __name__ == "__main__":
    main()
