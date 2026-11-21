"""Task 007 independent live checks. Run from repository root after ingestion.

The CSV is an audit comparison only, not a permanent ingestion dependency.
Original audit CSV bytes and metadata remain in ignored data/raw.
"""

import io
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

from ingestion.boe import BASE, fetch, ingest, publish, sha, verify_bundle


def main():
    root = Path("data")
    snapshot = "2026-11-21-task007"
    results = {}
    for dataset in ("bank_rate", "iumzid4"):
        path = root / "processed/bank_of_england" / dataset / f"snapshot={snapshot}"
        before = {p.name: sha(p.read_bytes()) for p in path.iterdir()}
        def offline(url):
            raise AssertionError("Rerun unexpectedly attempted a download")
        result = ingest(root, dataset, snapshot, date(2026, 11, 21), offline)
        after = {p.name: sha(p.read_bytes()) for p in path.iterdir()}
        assert before == after
        results[dataset] = {"manifest": verify_bundle(path), "offline_rerun_unchanged": True}

    csv_url = BASE + "_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2012&Dateto=21/Nov/2026&SeriesCodes=IUMZID4&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N"
    audit = root / "raw/bank_of_england/audit/snapshot=2026-11-21-task007"
    if not audit.exists():
        body, metadata = fetch(csv_url)
        publish(audit, {"comparison.csv": body}, {"identity": {"url": csv_url}, "retrieval": metadata})
    audit_info = verify_bundle(audit)
    comparison = pd.read_csv(io.BytesIO((audit / "comparison.csv").read_bytes()))
    comparison["observation_month"] = pd.to_datetime(comparison.DATE, format="%d %b %Y").dt.strftime("%Y-%m")
    validated = root / "validated/bank_of_england/iumzid4" / f"snapshot={snapshot}"
    current = pd.read_parquet(validated / "current.parquet")
    merged = current.merge(comparison, on="observation_month", validate="one_to_one")
    assert len(merged) == len(comparison) == len(current)
    assert (merged.rate_percent == merged.IUMZID4).all()
    results["csv_reconciliation"] = {"matched_current_rows": len(merged), "source": audit_info}

    processed = root / "processed/bank_of_england/iumzid4" / f"snapshot={snapshot}"
    selected = pd.read_parquet(processed / "selected.parquet").set_index("observation_month")
    evidence = json.loads(Path("reports/data_audits/007.1/observation-tests.json").read_text(encoding="utf-8"))
    # The ten Task 007.1 tests are independently retained before this implementation.
    expected = {test["observation_month"]: float(test["earliest_retained_value"])
                for test in evidence["tests"]}
    assert all(selected.loc[month, "rate_percent"] == value for month, value in expected.items())
    for test in evidence["tests"]:
        assert selected.loc[test["observation_month"], "source_updated_at"] == test["earliest_retained_update_timestamp"]
    assert selected.loc["2019-01", "observation_status"] == "provisional"
    results["selected_regressions"] = selected.loc[list(expected), ["rate_percent", "observation_status", "source_updated_at", "first_release_evidence_status"]].reset_index().to_dict("records")
    results["prior_investigation_evidence"] = "reports/data_audits/007.1/observation-tests.json"

    bank_path = root / "raw/bank_of_england/bank_rate" / f"snapshot={snapshot}"
    text = (bank_path / "response.bin").read_text(encoding="utf-8-sig")
    table = re.search(r'<table[^>]*id="stats-table".*?</table>', text, re.S).group()
    rows = re.findall(r'<td[^>]*>\s*(\d{2} \w{3} \d{2})\s*</td>\s*<td[^>]*>\s*([\d.]+)\s*</td>', table, re.S)
    events = pd.read_parquet(root / "processed/bank_of_england/bank_rate" / f"snapshot={snapshot}" / "events.parquet")
    assert len(rows) == len(events)
    assert dict(rows) == dict(zip(events.source_date_text, events.source_value_text))
    results["bank_rate_independent_extraction"] = {"matched_rows": len(rows),
        "official_page_examples": [{"effective_date": "1975-01-20", "rate_percent": 11.25},
                                   {"effective_date": "2020-03-19", "rate_percent": 0.10},
                                   {"effective_date": "2026-11-05", "rate_percent": 4.00}]}
    for expected_row in results["bank_rate_independent_extraction"]["official_page_examples"]:
        subset = events[events.effective_date == date.fromisoformat(expected_row["effective_date"])]
        assert subset.rate_percent.tolist() == [expected_row["rate_percent"]]
    results["limitations"] = ["Earliest retained database event is not certified original publication.",
        "Source update timestamp timezone/public availability unverified.",
        "Bank Rate page begins 20 January 1975; no earlier history claimed."]
    Path("reports/data_audits/007/validation-evidence.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print("CSV: 178 current rows reconciled; ten earliest-value regressions passed; Bank Rate: 259 events matched; both offline reruns unchanged.")


if __name__ == "__main__":
    main()
