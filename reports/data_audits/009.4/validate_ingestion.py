"""Offline independent Task 009.4 source reconciliation and preservation audit.

Run from repository root: uv run python reports/data_audits/009.4/validate_ingestion.py
Uses only retained official research responses; never reacquires source data.
"""

import csv
import hashlib
import io
import json
from urllib.parse import parse_qs, urlsplit
from pathlib import Path

import pandas as pd

from ingestion.boe import verify_bundle
from ingestion.nomis_umb import ingest

OUT = Path("reports/data_audits/009.4")
RAW = Path("data/raw/umb-009-3-investigation")
SNAPSHOT = "2026-11-22-task009-4"
PRODUCT = Path("data/processed/nomis_umb") / f"snapshot={SNAPSHOT}"


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {str(p): checksum(p) for p in Path("data").rglob("*") if p.is_file()}


# These fields describe ordering/pagination inside one request, not an observation.
REQUEST_FIELDS = frozenset(
    {
        "DATE_SORTORDER",
        "GEOGRAPHY_SORTORDER",
        "ITEM_SORTORDER",
        "MEASURES_SORTORDER",
        "RECORD_COUNT",
        "RECORD_OFFSET",
    }
)
MEASURES = frozenset({"20100", "20701"})


def observation_key(row):
    """ITEM distinguishes unemployment counts from rates sharing a measure code."""
    return (row["DATE_CODE"], row["GEOGRAPHY"], row["ITEM"], row["MEASURES"])


def observation_index(records):
    result = {}
    for row in records:
        key = observation_key(row)
        assert key not in result, f"Duplicate source observation: {key}"
        result[key] = row
    return result


def validate_request_records(records, url):
    """Validate request-local metadata separately from cross-request equality."""
    parsed = urlsplit(url)
    assert parsed.scheme == "https" and parsed.netloc == "www.nomisweb.co.uk"
    assert parsed.path == "/api/v01/dataset/NM_127_1.data.csv"
    params = parse_qs(parsed.query)
    assert params["geography"] == ["2092957699TYPE424"]
    assert set(params["measures"][0].split(",")) == MEASURES
    items = set(params["item"][0].split(","))
    assert items <= {"1", "2"} and "2" in items
    periods = set(params["date"][0].split(","))
    assert records and {r["DATE_CODE"] for r in records} == periods
    observation_index(records)
    for offset, row in enumerate(records):
        assert row["RECORD_COUNT"] == str(len(records)), "Invalid request record count"
        assert row["RECORD_OFFSET"] == str(offset), "Invalid request record offset"
        assert row["DATE"] == row["DATE_CODE"]
        assert row["ITEM"] in items and row["MEASURES"] in MEASURES
        assert row["GEOGRAPHY_TYPECODE"] == "424"
        assert row["URN"].lower().startswith("nm-127d1d"), "Wrong source dataset URN"
    return dict(
        url=url,
        rows=len(records),
        item_codes=sorted(items),
        measure_codes=sorted(MEASURES),
        pagination_validated=True,
    )


def compare_representatives(primary, representatives):
    """Compare approved ITEM 2 observations; retain counts solely as evidence."""
    indexed = observation_index(primary)
    observation_index(representatives)
    selected = [r for r in representatives if r["ITEM"] == "2"]
    assert {
        r["MEASURES"] for r in selected
    } == MEASURES, "Missing representative rate/confidence measure"
    compared = []
    for row in selected:
        assert row["MEASURES"] in MEASURES
        key = observation_key(row)
        assert key in indexed, f"Representative observation absent: {key}"
        actual = indexed[key]
        expected_values = {k: v for k, v in row.items() if k not in REQUEST_FIELDS}
        actual_values = {k: v for k, v in actual.items() if k not in REQUEST_FIELDS}
        different = sorted(
            k
            for k in set(expected_values) | set(actual_values)
            if expected_values.get(k) != actual_values.get(k)
        )
        assert (
            actual_values == expected_values
        ), f"Source observation differs: {key}; fields={different}"
        compared.append(
            dict(
                key=list(key),
                source_urn=row["URN"],
                source_value_text=row["OBS_VALUE"],
                request_fields_differing=sorted(
                    k for k in REQUEST_FIELDS if row.get(k) != actual.get(k)
                ),
            )
        )
    return dict(
        compared=compared,
        count_rows_excluded=sum(r["ITEM"] == "1" for r in representatives),
        excluded_equivalence_fields=sorted(REQUEST_FIELDS),
    )


def main():
    baseline = json.loads((OUT / "preservation-before.json").read_text())
    assert all(
        Path(p).is_file() and checksum(Path(p)) == value
        for p, value in baseline["files"].items()
    )
    bundles = list(RAW.glob("*/manifest.json"))
    for p in bundles:
        verify_bundle(p.parent)
    for layer in ("raw", "validated", "processed"):
        for p in (Path("data") / layer / "nomis_umb").rglob("manifest.json"):
            verify_bundle(p.parent)
    frame = pd.read_parquet(PRODUCT / "observations.parquet")
    coverage = pd.read_parquet(PRODUCT / "coverage.parquet")
    rates = pd.read_parquet(PRODUCT / "rates.parquet")
    evidence = json.loads(
        Path("reports/data_audits/009.3/validation-evidence.json").read_text()
    )
    original = []
    requests = []
    source_manifests = {}
    for p in sorted(RAW.glob("history*/response.bin")):
        records = list(csv.DictReader(io.StringIO(p.read_text(encoding="utf-8-sig"))))
        original.extend(records)
        manifest = verify_bundle(p.parent)
        request = validate_request_records(records, manifest["identity"]["url"])
        request.update(source=p.parent.name, sha256=checksum(p))
        requests.append(request)
        production = Path("data/raw/nomis_umb") / f"snapshot={SNAPSHOT}" / p.parent.name
        source_manifests[p.parent.name] = verify_bundle(production)
        assert checksum(production / "response.bin") == checksum(p)
    key = lambda r: (r["DATE"], r["GEOGRAPHY"], r["MEASURES"])
    source = {key(r): r for r in original}
    assert (
        len(source)
        == len(original)
        == len(frame)
        == evidence["source_observation_rows"]
    )
    actual = {
        (r.period_code, r.source_geography_id, r.measure): r for r in frame.itertuples()
    }
    assert set(actual) == set(source)
    for k, row in source.items():
        result = actual[k]
        assert json.loads(result.source_record_json) == row
        manifest = source_manifests[result.source_request_name]
        assert result.source_sha256 == manifest["source_sha256"]
        assert result.source_url == manifest["identity"]["url"]
        assert result.retrieved_at == manifest["retrieval"]["retrieved_at"]
        assert result.source_snapshot_id == SNAPSHOT
        assert result.source_value_text == row["OBS_VALUE"]
        assert result.gss_code == row["GEOGRAPHY_CODE"]
        assert result.observation_status == row["OBS_STATUS"]
        assert result.confidentiality_flag == row["OBS_CONF"]
        if row["OBS_VALUE"]:
            assert result.value == float(row["OBS_VALUE"])
        else:
            assert pd.isna(result.value)
    pairs = rates.set_index(["period_code", "source_geography_id"])
    for k, row in source.items():
        value = pairs.loc[k[:2]]
        prefix = "rate" if k[2] == "20100" else "confidence"
        assert value[prefix + "_source_text"] == row["OBS_VALUE"]
        assert value[prefix + "_obs_status"] == row["OBS_STATUS"]
        assert value[prefix + "_obs_conf"] == row["OBS_CONF"]
    columns = {
        "source_areas": "source_authorities",
        "exact_cohort_matches": "exact_cohort_rows",
        "numeric_cohort_rates": "numeric_cohort_rates",
        "numeric_cohort_confidence": "numeric_cohort_confidence",
    }
    prior = {r["date_code"]: r for r in evidence["coverage_by_period"]}
    assert set(coverage.period_code) == set(prior)
    for row in coverage.to_dict("records"):
        old = prior[row["period_code"]]
        for new, original_name in columns.items():
            assert row[new] == old[original_name]
        for new, old_name in [
            ("unmatched_target_codes_json", "missing_cohort_codes"),
            ("unmatched_source_codes_json", "unmatched_source_codes"),
            ("missing_numeric_cohort_rate_codes_json", "missing_rate_codes"),
            (
                "missing_numeric_cohort_confidence_codes_json",
                "missing_confidence_codes",
            ),
        ]:
            assert sorted(json.loads(row[new])) == sorted(old[old_name])
    assert frame.observation_status.value_counts().to_dict() == evidence["raw_statuses"]
    representative = evidence["latest_hartlepool_official_records"]
    independent = RAW / "latest_counts"
    representative_manifest = verify_bundle(independent)
    representative_records = list(
        csv.DictReader(
            io.StringIO((independent / "response.bin").read_text(encoding="utf-8-sig"))
        )
    )
    independent_provenance = validate_request_records(
        representative_records, representative_manifest["identity"]["url"]
    )
    independent_provenance["response_sha256"] = checksum(independent / "response.bin")
    representative_index = observation_index(representative_records)
    for row in representative:
        assert representative_index[observation_key(row)] == row
    comparison = compare_representatives(original, representative)
    # Same comparison across the entire independently requested latest-period extract.
    latest_comparison = compare_representatives(original, representative_records)
    for path in PRODUCT.glob("*.parquet"):
        validated = (
            Path("data/validated/nomis_umb") / f"snapshot={SNAPSHOT}" / path.name
        )
        pd.testing.assert_frame_equal(pd.read_parquet(path), pd.read_parquet(validated))
    resumed_baseline = json.loads(
        (OUT / "resumption-preservation-before.json").read_text()
    )
    for path, value in {
        **resumed_baseline["files"],
        **resumed_baseline["existing_audit_evidence"],
    }.items():
        assert checksum(Path(path)) == value, f"Preservation failure: {path}"
    before = inventory()

    def offline_only(_):
        raise AssertionError("Offline rerun attempted a network request")

    ingest(Path.cwd() / "data", SNAPSHOT, downloader=offline_only, sleep=lambda _: None)
    after = inventory()
    assert before == after
    latest = coverage.iloc[-1].to_dict()
    result = dict(
        status="PASS WITH CONDITIONS",
        conditions=[
            "Unharmonised source geography",
            "Incomplete historical publication availability",
            "Source missingness and uncertainty gaps retained",
        ],
        source_observations=len(frame),
        source_areas=int(latest["source_areas"]),
        periods=len(coverage),
        all_source_records_reconciled=len(source),
        processed_measure_pairs_reconciled=len(source),
        representative_official_records_reconciled=len(comparison["compared"]),
        representative_comparison=comparison,
        independent_latest_rate_confidence_cells=len(latest_comparison["compared"]),
        independent_latest_count_cells_excluded=latest_comparison[
            "count_rows_excluded"
        ],
        independent_request_provenance=independent_provenance,
        original_failure_evidence_preserved=True,
        resumed_data_files_unchanged=len(resumed_baseline["files"]),
        per_period_coverage_reconciled=len(coverage),
        source_requests=requests,
        verified_research_bundles=len(bundles),
        raw_statuses=evidence["raw_statuses"],
        numeric_rate_range=[
            int(coverage.numeric_cohort_rates.min()),
            int(coverage.numeric_cohort_rates.max()),
        ],
        numeric_confidence_range=[
            int(coverage.numeric_cohort_confidence.min()),
            int(coverage.numeric_cohort_confidence.max()),
        ],
        latest_coverage=latest,
        prior_files_unchanged=len(baseline["files"]),
        offline_rerun_files_unchanged=len(before),
        original_checkout="Untouched; separate original pre-remediation checkout is not a push source",
        preservation_scope="All data files present in clean checkout before this resumed ingestion; excluded original checkout datasets were not imported",
    )
    (OUT / "validation-evidence.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"source_requests", "latest_coverage"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
