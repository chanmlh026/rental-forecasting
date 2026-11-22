"""Independent offline XML-cell reconciliation; no production parsing/mapping reuse.

Run from the repository root with retained official raw files and production outputs.
"""

import hashlib
import io
import json
import posixpath
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

from ingestion.boe import safe_http_headers, verify_bundle
from ingestion.ons_population import ingest

OUT = Path("reports/data_audits/010")
SNAPSHOT = "2026-11-22-task010"
RAW = Path("data/raw/ons_population") / f"snapshot={SNAPSHOT}"
PRODUCT = Path("data/processed/ons_population") / f"snapshot={SNAPSHOT}"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {str(p): checksum(p) for p in Path("data").rglob("*") if p.is_file()}


def workbook_tables(path):
    """Resolve original ZIP relationships/shared strings without openpyxl."""
    result = {}
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = [
                "".join(n.itertext())
                for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(
                    "x:si", NS
                )
            ]
        relationships = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        }
        sheets = ET.fromstring(archive.read("xl/workbook.xml")).findall(
            "x:sheets/x:sheet", NS
        )
        for sheet in sheets:
            name = sheet.attrib["name"]
            if name not in {"MYE3", "MYE4", "MYE5"} and not name.startswith("MYEB3"):
                continue
            target = relationships[
                sheet.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
            ]
            target = (
                target.lstrip("/")
                if target.startswith("/")
                else posixpath.normpath("xl/" + target)
            )
            rows = {}
            for row in ET.fromstring(archive.read(target)).findall(
                "x:sheetData/x:row", NS
            ):
                cells = {}
                for cell in row.findall("x:c", NS):
                    coord = cell.attrib["r"]
                    column = re.match(r"[A-Z]+", coord)[0]
                    value = cell.find("x:v", NS)
                    text = "" if value is None or value.text is None else value.text
                    kind = cell.attrib.get("t", "n")
                    if kind == "s":
                        text = shared[int(text)]
                    elif kind == "inlineStr":
                        text = "".join(cell.find("x:is", NS).itertext())
                    formula = cell.find("x:f", NS)
                    cells[column] = dict(
                        cell=coord,
                        text=text,
                        kind=kind,
                        style=int(cell.attrib.get("s", 0)),
                        formula="" if formula is None else (formula.text or ""),
                    )
                rows[int(row.attrib["r"])] = cells
            result[name] = rows
    return result


def field_definition(sheet, header, end_year):
    """Independent source-label rules; values and net measures are never derived."""
    if sheet == "MYE3":
        h = header.lower().split()
        if (
            len(h) == 3
            and h[0] in {"internal", "international"}
            and h[1] == "migration"
            and h[2] in {"inflow", "outflow", "net"}
        ):
            return h[0] + "_" + h[2], end_year, "persons"
    elif sheet == "MYE4" and re.fullmatch(r"Mid-20[0-9]{2}", header):
        return "population", int(header[-4:]), "persons"
    elif sheet == "MYE5":
        if header == "Area (sq km)":
            return "land_area", None, "square_kilometres"
        if re.fullmatch(r"20[0-9]{2} people per sq[.] km2?", header):
            return "published_density", int(header[:4]), "persons_per_square_kilometre"
    else:
        parts = header.rsplit("_", 1)
        allowed = {
            "population",
            "internal_in",
            "internal_out",
            "internal_net",
            "international_in",
            "international_out",
            "international_net",
        }
        if (
            len(parts) == 2
            and parts[0] in allowed
            and re.fullmatch(r"20[0-9]{2}", parts[1])
        ):
            suffix = (
                parts[0].replace("_in", "_inflow")
                if parts[0].endswith("_in")
                else (
                    parts[0].replace("_out", "_outflow")
                    if parts[0].endswith("_out")
                    else parts[0]
                )
            )
            return suffix, int(parts[1]), "persons"
    return None


def main():
    baseline = json.loads(
        (OUT / "preservation-before.json").read_text(encoding="utf-8")
    )
    for path, value in baseline["files"].items():
        assert checksum(Path(path)) == value, f"Prior file changed: {path}"
    contract = json.loads(
        Path("configs/ons_population_sources.json").read_text(encoding="utf-8")
    )
    evidence = json.loads(
        (OUT / "source-investigation.json").read_text(encoding="utf-8")
    )
    info = verify_bundle(PRODUCT)
    for layer in ("validated", "processed"):
        directory = Path("data") / layer / "ons_population" / f"snapshot={SNAPSHOT}"
        verify_bundle(directory)
    for p in RAW.glob("*/manifest.json"):
        verify_bundle(p.parent)
        raw = json.loads(p.read_text(encoding="utf-8"))
        for name in ("request_headers", "response_headers"):
            if name in raw["retrieval"]:
                assert (
                    safe_http_headers(raw["retrieval"][name]) == raw["retrieval"][name]
                )
    frame = pd.read_parquet(PRODUCT / "observations.parquet")
    assert not frame.duplicated(
        ["edition_id", "source_sheet", "source_code", "measure", "reference_year"]
    ).any()
    indexed = {
        (r.edition_id, r.source_sheet, r.source_cell): r for r in frame.itertuples()
    }
    assert len(indexed) == len(frame)
    all_keys = set()
    edition_results = []
    source_populations = {}
    reference = json.loads(json.dumps({}))
    geo = pd.read_csv("configs/ons_lad_apr2025_v2.csv", dtype=str)
    # Use the approved reference loader only for the cohort, never for source values.
    from ingestion.ons_pipr import load_geography_reference

    cohort = load_geography_reference(
        Path("configs/ons_lad_apr2025_v2.csv")
    ).eligible_names
    for edition in contract["editions"]:
        name = edition["edition_id"]
        path = RAW / name / "response.bin"
        manifest = verify_bundle(path.parent)
        assert checksum(path) == edition["source_sha256"] == manifest["source_sha256"]
        assert manifest["identity"]["url"] == edition["url"]
        assert manifest["retrieval"]["status"] == 200
        tables = workbook_tables(path)
        cell_count = 0
        for table in edition["tables"]:
            sheet = table["sheet"]
            rows = tables[sheet]
            hr = table["header_row"]
            headers = rows[hr]
            for rn, cells in rows.items():
                if rn <= hr:
                    continue
                code = cells.get("A", {}).get("text", "")
                if not re.fullmatch(r"[EKNSW][0-9]{8}", code):
                    continue
                for column, header in headers.items():
                    definition = field_definition(
                        sheet, header["text"], edition["latest_reference_year"]
                    )
                    if definition is None:
                        continue
                    measure, year, unit = definition
                    coordinate = f"{column}{rn}"
                    source = cells.get(
                        column,
                        dict(cell=coordinate, text="", kind="n", style=0, formula=""),
                    )
                    key = (name, sheet, coordinate)
                    assert key not in all_keys
                    all_keys.add(key)
                    assert key in indexed, f"Missing source cell: {key}"
                    actual = indexed[key]
                    assert (
                        actual.source_code,
                        actual.source_name,
                        actual.source_geography_type,
                    ) == (code, cells["B"]["text"], cells["C"]["text"]), key
                    assert actual.measure == measure and actual.unit == unit, key
                    assert (
                        pd.isna(actual.reference_year)
                        if year is None
                        else actual.reference_year == year
                    ), key
                    assert (
                        actual.source_header == header["text"]
                        and actual.source_value_text == source["text"]
                    ), key
                    assert (
                        actual.source_formula == source["formula"]
                        and actual.source_style_id == source["style"]
                    ), key
                    numeric = source["kind"] == "n" and bool(source["text"])
                    assert (
                        actual.value == float(source["text"])
                        if numeric
                        else pd.isna(actual.value)
                    ), key
                    assert (
                        actual.source_sha256 == edition["source_sha256"]
                        and actual.source_url == edition["url"]
                    ), key
                    assert (
                        actual.retrieved_at == manifest["retrieval"]["retrieved_at"]
                        and actual.source_snapshot_id == SNAPSHOT
                    ), key
                    assert actual.exact_cohort_code_match == (code in cohort), key
                    if measure.startswith(("internal_", "international_")):
                        assert (actual.period_start, actual.period_end) == (
                            f"{year-1}-07-01",
                            f"{year}-06-30",
                        ), key
                    if measure == "population" and sheet == "MYE4":
                        source_populations[(name, code, year)] = source["text"]
                    cell_count += 1
        edition_frame = frame[frame.edition_id == name]
        edition_results.append(
            dict(
                edition_id=name,
                source_cells_reconciled=cell_count,
                source_sheets=len(edition["tables"]),
                geography_codes=edition_frame.source_code.nunique(),
                population_years=sorted(
                    edition_frame.loc[
                        edition_frame.measure == "population", "reference_year"
                    ]
                    .dropna()
                    .astype(int)
                    .unique()
                    .tolist()
                ),
                migration_years=sorted(
                    edition_frame.loc[
                        edition_frame.measure.str.startswith(
                            ("internal_", "international_")
                        ),
                        "reference_year",
                    ]
                    .dropna()
                    .astype(int)
                    .unique()
                    .tolist()
                ),
            )
        )
    assert all_keys == set(indexed), "Unexpected extra ingested cells"
    coverage = pd.read_parquet(PRODUCT / "coverage.parquet")
    for row in coverage.itertuples():
        group = frame[
            (frame.edition_id == row.edition_id)
            & (frame.source_sheet == row.source_sheet)
            & (frame.measure == row.measure)
        ]
        group = (
            group[group.reference_year.isna()]
            if pd.isna(row.reference_year)
            else group[group.reference_year == row.reference_year]
        )
        selected = group[group.source_code.isin(cohort)]
        assert (len(group), len(selected), selected.value.notna().sum()) == (
            row.source_areas,
            row.exact_cohort_matches,
            row.numeric_cohort_values,
        )
        assert sorted(set(cohort) - set(group.source_code)) == json.loads(
            row.unmatched_target_codes_json
        )
    prior = json.loads(
        Path(
            "reports/data_audits/006.2/predictor-exploration-evidence.json"
        ).read_text()
    )
    for sheet, measure in [
        ("MYE4", "population"),
        ("MYE5", "published_density"),
        ("MYE3", "internal_inflow"),
    ]:
        group = coverage[
            (coverage.edition_id == "summary2025")
            & (coverage.source_sheet == sheet)
            & (coverage.measure == measure)
        ]
        assert group.exact_cohort_matches.eq(
            prior["measurements"][sheet]["cohort_rows"]
        ).all()
        assert group.numeric_cohort_values.eq(292).all()
    # Same-vintage, same-geography LA population and migration observations must agree.
    within_vintage = []
    for year in (2022, 2023, 2024, 2025):
        summary = "summary" + str(year) + ("_2023" if year == 2022 else "")
        detail = "detail" + str(year)
        a = frame[
            (frame.edition_id == summary) & (frame.source_sheet.isin(["MYE3", "MYE4"]))
        ]
        b = frame[
            (frame.edition_id == detail) & (frame.source_geography_vintage == "2023")
        ]
        merged = a.merge(
            b,
            on=["source_code", "measure", "reference_year"],
            suffixes=("_summary", "_detail"),
        )
        assert len(merged) > 0
        equal = (merged.value_summary.eq(merged.value_detail)) | (
            merged.value_summary.isna() & merged.value_detail.isna()
        )
        assert (
            equal.all()
        ), f"Genuine same-vintage source discrepancy: {summary}/{detail}"
        within_vintage.append(
            dict(summary=summary, detail=detail, cells_compared=len(merged))
        )
    for p in PRODUCT.glob("*.parquet"):
        pd.testing.assert_frame_equal(
            pd.read_parquet(p),
            pd.read_parquet(
                Path("data/validated/ons_population") / f"snapshot={SNAPSHOT}" / p.name
            ),
        )
    before = inventory()

    def never(_):
        raise AssertionError("Offline replay attempted acquisition")

    ingest(Path.cwd() / "data", SNAPSHOT, downloader=never, sleep=lambda _: None)
    assert before == inventory(), "Offline replay changed source or output files"
    source_geography = pd.read_parquet(PRODUCT / "geography_audit.parquet")
    discrepancies = source_geography[
        source_geography.relationship == "same_name_different_code"
    ]
    result = dict(
        status="PASS WITH CONDITIONS",
        acquisition_scope="Owner-authorised offline validation of nine retained editions; five advertised older versions remain unacquired pending approved project contact",
        observations=len(frame),
        edition_results=edition_results,
        source_cells_reconciled=len(all_keys),
        within_vintage_comparisons=within_vintage,
        source_value_kinds=frame.value_kind.value_counts().to_dict(),
        coverage_rows_reconciled=len(coverage),
        same_name_code_discrepancies=discrepancies[
            [
                "edition_id",
                "source_sheet",
                "source_code",
                "source_name",
                "same_name_target_code",
            ]
        ].to_dict("records"),
        prior_files_unchanged=len(baseline["files"]),
        offline_rerun_files_unchanged=len(before),
        raw_bundles_verified=len(list(RAW.glob("*/manifest.json"))),
        pending_downloads=evidence["pending_downloads"],
        conditions=[
            "Source geography/notes unresolved; no mappings",
            "Separate revision vintages; incomplete historical publication availability",
            "Further automated ONS downloads blocked pending contact approval",
        ],
        point_in_time_claim=False,
        production_network_requests_after_offline_instruction=0,
    )
    (OUT / "validation-evidence.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"same_name_code_discrepancies", "pending_downloads"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
