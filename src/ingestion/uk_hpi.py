"""Official all-property UK HPI snapshots and exact-code cohort coverage."""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import pandas as pd

from ingestion.ons_pipr import load_geography_reference
from ingestion.source_io import IngestionError, fetch, publish_tables, raw_source, sha, storage_root

VERSION = "uk-hpi-ingestion-v1"
ABOUT_URL = "https://www.gov.uk/government/publications/about-the-uk-house-price-index/about-the-uk-house-price-index"


class ReleasePage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.times, self.meta, self.text = [], [], {}, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "time" and attrs.get("datetime"):
            self.times.append(attrs["datetime"])
        if tag == "meta" and attrs.get("name"):
            self.meta[attrs["name"]] = attrs.get("content", "")

    def handle_data(self, data):
        self.text.append(data)


def release_contract(body: bytes, month: str) -> dict:
    page = ReleasePage()
    page.feed(body.decode("utf-8"))
    urls = {}
    for key, filename in {"full": f"UK-HPI-full-file-{month}.csv",
                          "revisions_england": f"Revisions-England-{month}.csv"}.items():
        matches = {url for url in page.links if urlsplit(url).hostname == "publicdata.landregistry.gov.uk"
                   and urlsplit(url).path.endswith("/" + filename)}
        if len(matches) != 1:
            raise IngestionError(f"Missing/ambiguous official download link: {key}")
        urls[key] = matches.pop()
    stamp = page.meta.get("govuk:first_published_at")
    if not stamp:
        dates = {value[:10] for value in page.times}
        if len(dates) == 1:
            stamp = dates.pop()
        else:
            published = re.findall(r"Published\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", " ".join(page.text))
            if len(set(published)) != 1:
                raise IngestionError("Missing/ambiguous official release date")
            stamp = datetime.strptime(published[0], "%d %B %Y").date().isoformat()
    try:
        release_date = datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise IngestionError("Invalid publisher release date") from exc
    if release_date.strftime("%Y-%m") < month:
        raise IngestionError("Release date precedes reference period")
    return {"urls": urls, "source_release_date": release_date.isoformat(),
            "source_release_date_text": stamp}


def summary_base(body: bytes) -> str:
    page = ReleasePage()
    page.feed(body.decode("utf-8"))
    bases = set(re.findall(r"January\s+(\d{4})\s*(?:=|equals)\s*100", " ".join(page.text)))
    if len(bases) != 1:
        raise IngestionError("Missing/ambiguous index base in official HPI summary")
    return bases.pop() + "-01"


def numeric_column(frame: pd.DataFrame, column: str) -> pd.Series:
    source = frame[column]
    numeric = pd.to_numeric(source.replace("", None), errors="coerce")
    invalid = (source.ne("") & numeric.isna()) | (numeric.notna() & (~np.isfinite(numeric) | numeric.le(0)))
    if invalid.any():
        raise IngestionError(f"Invalid all-property numeric values: {column}")
    return numeric.astype("float64")


def parse_hpi(body: bytes, reference_month: str, base_month: str,
              cohort: dict[str, str]) -> tuple[dict[str, pd.DataFrame], dict]:
    try:
        text = body.decode("utf-8-sig")
        rows = csv.reader(io.StringIO(text, newline=""))
        header = next(rows)
        if len(header) != len(set(header)) or not {"Date", "AreaCode", "RegionName", "AveragePrice", "Index"}.issubset(header):
            raise IngestionError("Missing/duplicate HPI source columns")
        for row in rows:
            if row and len(row) != len(header):
                raise IngestionError("Incomplete or malformed HPI CSV row")
        source = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
        if source.empty:
            raise IngestionError("Empty HPI observations")
        dates = pd.to_datetime(source.Date, format="%d/%m/%Y", errors="raise")
        if dates.dt.day.ne(1).any():
            raise IngestionError("HPI reference dates must be month labels")
        if not source.AreaCode.str.fullmatch(r"[ENSWK]\d{8}").all() or source.RegionName.str.strip().eq("").any():
            raise IngestionError("Missing/invalid source geography")
        if source.assign(month=dates.dt.strftime("%Y-%m")).duplicated(["AreaCode", "month"]).any():
            raise IngestionError("Duplicate/conflicting HPI area-month observations")
        price, index = numeric_column(source, "AveragePrice"), numeric_column(source, "Index")
        if dates.max().strftime("%Y-%m") != reference_month:
            raise IngestionError("Incomplete source or wrong release reference month")
        at_base = dates.dt.strftime("%Y-%m").eq(base_month) & index.notna()
        if not at_base.any() or index[at_base].ne(100).any():
            raise IngestionError("HPI index base conflicts with source summary")
        observations = pd.DataFrame(dict(observation_month=dates.dt.strftime("%Y-%m"),
            source_reference_date=dates.dt.date, area_code=source.AreaCode,
            source_area_name=source.RegionName, average_price_gbp=price,
            house_price_index=index, source_price_text=source.AveragePrice,
            source_index_text=source.Index, index_base_month=base_month,
            in_approved_cohort=source.AreaCode.isin(cohort)))
        observations["cohort_area_name"] = observations.area_code.map(cohort)
        observations["source_name_differs"] = observations.in_approved_cohort & observations.source_area_name.ne(observations.cohort_area_name)
        observations = observations.sort_values(["area_code", "observation_month"]).reset_index(drop=True)
        matched = observations[observations.in_approved_cohort].copy()
        # This is a coverage grid, never fabricated source observations.
        english_la = observations[observations.area_code.str.match(r"E0[6789]")]
        if english_la.empty:
            raise IngestionError("No English Local Authority observations")
        months = pd.period_range(english_la.observation_month.min(), reference_month, freq="M").astype(str)
        grid = pd.MultiIndex.from_product([sorted(cohort), months], names=["area_code", "observation_month"]).to_frame(index=False)
        presence = matched[["area_code", "observation_month"]].copy()
        presence["source_row_present"] = True
        presence["price_present"] = matched.average_price_gbp.notna()
        presence["index_present"] = matched.house_price_index.notna()
        coverage = grid.merge(presence, on=["area_code", "observation_month"], how="left", validate="one_to_one")
        for col in ("source_row_present", "price_present", "index_present"):
            coverage[col] = coverage[col].fillna(False).astype(bool)
        coverage["cohort_area_name"] = coverage.area_code.map(cohort)
        coverage["both_measures_present"] = coverage.price_present & coverage.index_present
        monthly = coverage.groupby("observation_month", as_index=False).agg(
            expected_authorities=("area_code", "size"), matched_authorities=("source_row_present", "sum"),
            complete_measure_authorities=("both_measures_present", "sum"))
        authorities = coverage.groupby(["area_code", "cohort_area_name"], as_index=False).agg(
            expected_months=("observation_month", "size"), observed_months=("source_row_present", "sum"),
            complete_measure_months=("both_measures_present", "sum"))
        inventory = observations.groupby(["area_code", "source_area_name"], as_index=False).agg(
            first_month=("observation_month", "min"), last_month=("observation_month", "max"),
            observed_months=("observation_month", "size"), price_count=("average_price_gbp", "count"),
            index_count=("house_price_index", "count"))
        metadata = dict(source_rows=len(source), source_columns=header,
            observation_start=observations.observation_month.min(), observation_end=reference_month,
            source_areas=int(observations.area_code.nunique()), cohort_size=len(cohort),
            cohort_codes_matched=int(matched.area_code.nunique()), cohort_rows=len(matched),
            unmatched_cohort_codes=sorted(set(cohort) - set(matched.area_code)),
            missing_cohort_area_months=int((~coverage.source_row_present).sum()),
            incomplete_cohort_measure_cells=int((~coverage.price_present).sum() + (~coverage.index_present).sum()),
            source_missing_prices=int(price.isna().sum()), source_missing_indices=int(index.isna().sum()),
            index_base_month=base_month,
            source_name_differences=matched.loc[matched.source_name_differs, ["area_code", "source_area_name", "cohort_area_name"]].drop_duplicates().to_dict("records"),
            unmatched_source_areas=inventory[~inventory.area_code.isin(cohort)].to_dict("records"))
        return {"source_table": source, "observations": observations, "cohort": matched,
                "cohort_coverage": coverage, "monthly_coverage": monthly,
                "authority_coverage": authorities, "geography_inventory": inventory}, metadata
    except (ValueError, TypeError, UnicodeError, StopIteration, csv.Error) as exc:
        raise IngestionError(f"Invalid HPI CSV source: {exc}") from exc


def parse_revisions(body: bytes) -> pd.DataFrame:
    """Retain the England publication-label matrix as audit data, not features."""
    measures = {"Average price": "GBP", "Annual growth (%)": "%", "Number of transactions": "count"}
    records, measure, months = [], None, None
    try:
        for row in csv.reader(io.StringIO(body.decode("utf-8-sig"), newline="")):
            if not row or not any(row):
                continue
            if row[0] in measures and not any(row[1:]):
                measure, months = row[0], None
                continue
            if row[0] == "Publication date" and measure:
                months = [datetime.strptime(cell, "%d/%m/%Y").strftime("%Y-%m") for cell in row[1:] if cell]
                if len(months) != len(set(months)):
                    raise IngestionError("Duplicate revision reference months")
                continue
            if not measure or not months:
                raise IngestionError("Unknown revision-table structure")
            publication_month = datetime.strptime(row[0], "%d/%m/%Y").strftime("%Y-%m")
            if len(row[1:]) != len(months):
                raise IngestionError("Incomplete revision-table row")
            for month, text in zip(months, row[1:]):
                value = None if text == "" else float(text)
                if value is not None and not np.isfinite(value):
                    raise IngestionError("Non-finite revision value")
                records.append(dict(area_code="E92000001", measure=measure, unit=measures[measure],
                    observation_month=month, source_publication_label=row[0],
                    source_publication_month=publication_month, source_value_text=text, value=value,
                    publication_evidence="publisher_month_label_not_verified_release_date"))
        frame = pd.DataFrame(records)
        if frame.empty or frame.duplicated(["measure", "observation_month", "source_publication_label"]).any():
            raise IngestionError("Empty/duplicate revision matrix")
        return frame
    except (ValueError, UnicodeError, csv.Error) as exc:
        raise IngestionError(f"Invalid revision matrix: {exc}") from exc


def ingest(root: Path, snapshot: str, month: str, geography_reference: Path,
           downloader=fetch) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise IngestionError("Expected release reference YYYY-MM")
    reference = datetime.strptime(month, "%Y-%m")
    slug = reference.strftime("%B-%Y").lower()
    release_url = "https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-" + slug
    summary_url = f"https://www.gov.uk/government/statistics/uk-house-price-index-for-{slug}/uk-house-price-index-summary-{slug}"
    sources = {}
    page, sources["release_page"] = raw_source(root, "uk_hpi", snapshot, "release-page", release_url, downloader)
    contract = release_contract(page, month)
    summary, sources["release_summary"] = raw_source(root, "uk_hpi", snapshot, "release-summary", summary_url, downloader)
    base = summary_base(summary)
    source, sources["full"] = raw_source(root, "uk_hpi", snapshot, "full", contract["urls"]["full"], downloader)
    revisions, sources["revisions_england"] = raw_source(root, "uk_hpi", snapshot,
        "revisions-england", contract["urls"]["revisions_england"], downloader)
    geography = load_geography_reference(geography_reference)
    tables, report = parse_hpi(source, month, base, geography.eligible_names)
    tables["revisions_england"] = parse_revisions(revisions)
    for name, table in tables.items():
        if name == "source_table":
            continue
        table["source_snapshot_id"] = snapshot
        table["source_release_date"] = contract["source_release_date"]
        table["source_reference_month"] = month
        origin = "revisions_england" if name == "revisions_england" else "full"
        table["source_sha256"] = sources[origin]["source_sha256"]
        table["retrieved_at"] = sources[origin]["retrieval"]["retrieved_at"]
    report["revision_cells"] = len(tables["revisions_england"])
    report["revision_nonmissing_cells"] = int(tables["revisions_england"].value.notna().sum())
    report["revision_scope"] = "England aggregate; does not establish Local Authority vintages"
    info = dict(identity={"dataset": "uk_hpi", "snapshot_id": snapshot, "reference_month": month,
        "geography_reference_sha256": sha(geography_reference.read_bytes())},
        transformation_version=VERSION, source_contract=contract, sources=sources, validation=report,
        exact_point_in_time=False, geography_reference_version=geography.version,
        vintage_policy="Preserve each release; no earliest-value selection or geography mapping",
        licence_url=ABOUT_URL + "#7-republishing-data",
        attribution="Contains HM Land Registry data; Crown copyright and database right 2020; OGL v3.0")
    validated = {name: tables[name] for name in ("source_table", "observations", "revisions_england")}
    processed = {name: table for name, table in tables.items() if name != "source_table"}
    return publish_tables(root, "uk_hpi", snapshot, validated, processed, info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--reference-month", default="2026-09")
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    parser.add_argument("--geography-reference", type=Path, default=Path("configs/ons_lad_apr2025_v2.csv"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        result = ingest(storage_root(args.config), args.snapshot_id, args.reference_month, args.geography_reference)
        report = result["validation"]
        print(json.dumps({"processed_path": result["processed_path"], "coverage": {k: v for k, v in report.items() if k not in {"unmatched_source_areas", "source_columns"}}}, indent=2))
    except (IngestionError, OSError, ValueError) as exc:
        parser.exit(1, f"UK HPI ingestion failed: {exc}\n")


if __name__ == "__main__":
    main()
