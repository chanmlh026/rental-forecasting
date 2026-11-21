"""Offline cross-check of Task 009.1 research artifacts; no production writes."""

import collections
import json
import re
from pathlib import Path

from ingestion.boe import safe_http_headers, verify_bundle

OUT = Path("reports/data_audits/009.1")
RAW = Path("data/raw/ashe-009-1-investigation")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    access = read(OUT / "access-evidence.json")
    coverage = read(OUT / "coverage-quality-evidence.json")["editions"]
    fields = read(OUT / "field-evidence.json")
    extracts = read(RAW / "selected-field-extracts.json")
    assert len(access) == len(coverage) == len(fields) == len(extracts) == 37
    assert {r["year"] for r in coverage} == set(range(2002, 2027))
    snapshots = 0
    for manifest_path in RAW.glob("*/manifest.json"):
        manifest = verify_bundle(manifest_path.parent)
        for attempt in [manifest]:
            headers = attempt.get("response_headers", {})
            assert headers == safe_http_headers(headers)
            assert not any(re.search(r"cookie|authorization|token|session", k, re.I) for k in headers)
        snapshots += 1
    for record, result, extract in zip(access, coverage, extracts):
        assert record["metadata"]["status"] == 200
        directory = record.get("raw_directory") or re.sub(r"[^a-zA-Z0-9_.-]", "_", record["url"].rsplit("/", 1)[-1])
        manifest = verify_bundle(RAW / directory)
        assert result["source_zip_sha256"] == manifest["checksums"]["response.bin"]
        # Legacy codes 68/69 are reused for London aggregates and LAs.
        # Check source row identities without deduplicating those observations.
        pay = {(r["code"], r["name"]): r for r in extract["rows"]}
        cv = {(r["code"], r["name"]): r for r in extract["cv_rows"]}
        assert len(pay) == len(extract["rows"])
        assert len(cv) == len(extract["cv_rows"])
        assert set(pay) == set(cv)
        assert all(code in {"68", "69"} for code in result["duplicate_source_codes"])
        assert result["numeric_cohort_medians"] + sum(result["cohort_markers"].values()) == result["exact_cohort_matches"]
        assert result["exact_cohort_matches"] + result["missing_cohort_count"] == 294
        assert sum(result["numeric_matched_cv_bands"].values()) == result["numeric_cohort_medians"]
    comparisons = []
    for year in range(2016, 2026):
        editions = [e for e in extracts if e["year"] == year]
        assert len(editions) == 2
        provisional, revised = editions
        assert "provisional" in provisional["edition"] and "revised" in revised["edition"]
        left = {r["code"]: r for r in provisional["rows"]}
        right = {r["code"]: r for r in revised["rows"]}
        common = set(left) & set(right)
        numeric = [c for c in common if isinstance(left[c]["median"], (int, float)) and isinstance(right[c]["median"], (int, float))]
        comparisons.append(dict(year=year, provisional=provisional["source"], revised=revised["source"],
            common_source_codes=len(common), provisional_only_codes=sorted(set(left)-set(right)),
            revised_only_codes=sorted(set(right)-set(left)), numeric_in_both=len(numeric),
            changed_numeric_medians=sum(left[c]["median"] != right[c]["median"] for c in numeric),
            changed_marker_or_numeric_status=sum(isinstance(left[c]["median"], (int, float)) != isinstance(right[c]["median"], (int, float)) for c in common)))
    (OUT / "revision-evidence.json").write_text(json.dumps(comparisons, indent=2)+"\n", encoding="utf-8")
    result = dict(status="pass", editions=37, observation_years=25,
        immutable_raw_bundles_verified=snapshots, paired_pay_cv_code_sets_identical=True,
        duplicate_source_row_identities=0,
        editions_with_legacy_code_collisions=sum(bool(r["duplicate_source_codes"]) for r in coverage),
        modern_gss_code_duplicates=0, cohort_and_cv_counts_reconcile=True,
        safe_header_allowlist_verified=True, production_outputs_written=False,
        revision_comparison_scope="All source-coded geographies, including counties; exact codes within paired editions only; no model-input vintage selection",
        successful_zip_status_counts=dict(collections.Counter(r["metadata"]["status"] for r in access)),
        preserved_prior_attempt_status_counts=dict(collections.Counter(p["status"] for r in access for p in r.get("previous_attempts", []))))
    (OUT / "validation-evidence.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("Revision comparisons:", [(r["year"], r["changed_numeric_medians"], r["changed_marker_or_numeric_status"]) for r in comparisons])


if __name__ == "__main__":
    main()
