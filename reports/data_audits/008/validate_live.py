"""Task 008 official-source reconciliation; raw comparisons stay outside Git."""

import csv
import io
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import pandas as pd

from ingestion import ons_inflation, uk_hpi
from ingestion.source_io import raw_source, safe_http_metadata, sha, verify_bundle

ROOT = Path("data")
SNAPSHOT = "2026-11-21-task008"
PRIOR_HPI = "2026-11-21-task008-hpi-2026-08"
REFERENCE = Path("configs/ons_lad_apr2025_v2.csv")


def offline(url):
    raise AssertionError("Existing snapshot attempted a new download")


def fingerprint():
    return {p.as_posix(): sha(p.read_bytes()) for layer in ("raw", "validated", "processed")
        for dataset in ("ons_inflation", "uk_hpi")
        for p in (ROOT / layer / dataset).rglob("*") if p.is_file()}


def main():
    before = fingerprint()
    cpi = ons_inflation.ingest(ROOT, SNAPSHOT, downloader=offline)
    hpi = uk_hpi.ingest(ROOT, SNAPSHOT, "2026-09", REFERENCE, downloader=offline)
    previous = uk_hpi.ingest(ROOT, PRIOR_HPI, "2026-08", REFERENCE, downloader=offline)
    assert before == fingerprint()
    result = {"task": "008", "offline_reruns_unchanged": True,
        "existing_snapshot_files_checked": len(before), "inflation": [], "comparison_sources": {}}
    observations = pd.read_parquet(Path(cpi["processed_path"]) / "observations.parquet")
    for code in ons_inflation.SERIES:
        url = "https://www.ons.gov.uk/generator?" + urlencode({"format": "csv", "uri": ons_inflation.series_path(code)})
        body, provenance = raw_source(ROOT, "task008_audit", SNAPSHOT, code + "-csv", url)
        result["comparison_sources"][code] = provenance
        rows = list(csv.reader(io.StringIO(body.decode("utf-8-sig"), newline="")))
        header = {row[0]: row[1] for row in rows if len(row) == 2 and not re.match(r"\d{4}", row[0])}
        assert header["CDID"] == code
        monthly = {ons_inflation.parse_month(row[0]): row[1] for row in rows if len(row) == 2 and re.fullmatch(r"\d{4} [A-Z]{3}", row[0])}
        current = observations[(observations.series_id == code) & (observations.source_version_id == "current")]
        assert current.set_index("observation_month").source_value_text.to_dict() == monthly
        prior = observations[(observations.series_id == code) & (observations.source_version_id != "current")]
        comparison = current.merge(prior, on="observation_month", suffixes=("_new", "_old"), validate="one_to_one")
        report = next(r for r in cpi["validation"] if r["series_id"] == code and r["source_version_id"] == "current")
        result["inflation"].append({k: report[k] for k in ("series_id", "observation_start", "observation_end", "observation_count", "missing_months", "missing_values")})
        result["inflation"][-1].update(
            matched_csv_months=len(monthly), prior_version=prior.source_version_id.iloc[0],
            prior_release_date=str(prior.source_release_date.iloc[0]), prior_months=len(prior),
            overlapping_revised_values=int((comparison.source_value_text_new != comparison.source_value_text_old).sum()),
            current_release_date=str(current.source_release_date.iloc[0]),
            unit=current.unit.iloc[0], index_base_year=current.index_base_year.iloc[0],
            selected_examples=current.iloc[[0, -2, -1]][["observation_month", "source_value_text"]].to_dict("records"))

    hpi_path = Path(hpi["processed_path"])
    all_hpi = pd.read_parquet(hpi_path / "observations.parquet")
    # Independent attribute exports are linked from the retained official release page.
    release = ROOT / "raw/uk_hpi" / f"snapshot={SNAPSHOT}" / "release-page/response.bin"
    page = uk_hpi.ReleasePage()
    page.feed(release.read_text(encoding="utf-8"))
    for filename, column, output in (("Average-prices-2026-09.csv", "AveragePrice", "source_price_text"),
                                     ("Indices-2026-09.csv", "Index", "source_index_text")):
        urls = {url for url in page.links if urlsplit(url).hostname == "publicdata.landregistry.gov.uk" and urlsplit(url).path.endswith("/" + filename)}
        assert len(urls) == 1
        body, provenance = raw_source(ROOT, "task008_audit", SNAPSHOT, column, urls.pop())
        result["comparison_sources"][column] = provenance
        data = pd.read_csv(io.BytesIO(body), dtype=str, keep_default_na=False)
        data = data.rename(columns={"Area_Code": "AreaCode", "Average_Price": "AveragePrice"})
        date_format = "%Y-%m-%d" if data.Date.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all() else "%d/%m/%Y"
        data["observation_month"] = pd.to_datetime(data.Date, format=date_format).dt.strftime("%Y-%m")
        comparison = all_hpi.merge(data, left_on=["area_code", "observation_month"],
            right_on=["AreaCode", "observation_month"], validate="one_to_one")
        assert len(comparison) == len(data) == len(all_hpi)
        assert (pd.to_numeric(comparison[column]) == pd.to_numeric(comparison[output])).all()
        result[column + "_independent_rows_matched"] = len(comparison)

    cohort = pd.read_parquet(hpi_path / "cohort.parquet")
    old_cohort = pd.read_parquet(Path(previous["processed_path"]) / "cohort.parquet")
    prior_all = pd.read_parquet(Path(previous["processed_path"]) / "observations.parquet")
    changes = cohort.merge(old_cohort, on=["area_code", "observation_month"], suffixes=("_new", "_old"), validate="one_to_one")
    result["hpi"] = hpi["validation"]
    result["hpi"]["cohort_observation_start"] = cohort.observation_month.min()
    result["hpi"]["cohort_observation_end"] = cohort.observation_month.max()
    result["hpi"]["cohort_months"] = cohort.observation_month.nunique()
    inventory = pd.read_parquet(hpi_path / "geography_inventory.parquet")
    inventory["missing_calendar_months"] = [
        pd.Period(end, freq="M").ordinal - pd.Period(start, freq="M").ordinal + 1 - observed
        for start, end, observed in zip(inventory.first_month, inventory.last_month, inventory.observed_months)]
    result["hpi"]["source_series_with_calendar_gaps"] = inventory.loc[
        inventory.missing_calendar_months.gt(0), ["area_code", "source_area_name", "first_month", "last_month", "missing_calendar_months"]].to_dict("records")
    result["hpi"]["area_codes_with_multiple_source_names"] = int(inventory.groupby("area_code").size().gt(1).sum())
    result["hpi"]["codes_added_since_prior_release"] = sorted(set(all_hpi.area_code) - set(prior_all.area_code))
    result["hpi"]["codes_removed_since_prior_release"] = sorted(set(prior_all.area_code) - set(all_hpi.area_code))
    result["hpi"]["release_date"] = hpi["source_contract"]["source_release_date"]
    result["hpi"]["prior_release_reference"] = "2026-08"
    result["hpi"]["prior_cohort_rows"] = len(old_cohort)
    result["hpi"]["overlapping_cohort_rows"] = len(changes)
    result["hpi"]["revised_price_rows"] = int((changes.source_price_text_new != changes.source_price_text_old).sum())
    result["hpi"]["revised_index_rows"] = int((changes.source_index_text_new != changes.source_index_text_old).sum())
    result["hpi"]["selected_examples"] = cohort[(cohort.area_code.isin(["E06000001", "E08000038", "E09000033"])) & (cohort.observation_month.isin(["1995-01", "2026-09"]))][["area_code", "source_area_name", "observation_month", "source_price_text", "source_index_text"]].to_dict("records")
    # Large per-area inventories are retained in ignored Parquet; commit concise aggregate evidence.
    result["hpi"].pop("unmatched_source_areas")
    result["hpi_sources"] = hpi["sources"]
    result["prior_hpi_sources"] = previous["sources"]
    result["inflation_sources"] = cpi["sources"]
    result["limitations"] = [
        "Current and latest advertised prior ONS versions retained; full historical archive not reconstructed.",
        "Two HPI release snapshots and England aggregate revision matrix do not establish complete LA publication histories.",
        "Exact public release times, historical geography compatibility and forecast-cutoff eligibility are not inferred.",
    ]
    Path("reports/data_audits/008/validation-evidence.json").write_text(
        json.dumps(safe_http_metadata(result), indent=2) + "\n", encoding="utf-8")
    print("Four ONS CSV comparisons and both HPI attribute exports reconciled; all source snapshots and outputs unchanged on offline reruns.")


if __name__ == "__main__":
    main()
