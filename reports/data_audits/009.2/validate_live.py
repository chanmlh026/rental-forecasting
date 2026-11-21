"""Offline reconciliation against official source cells and immutable rerun.

First run ingestion (online or explicit verified --source-cache), then this file.
No investigation-only ignored files are required. Outputs are lightweight JSON.
"""

import argparse
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import openpyxl
import pandas as pd
import xlrd

from ingestion import ons_ashe
from ingestion.boe import verify_bundle


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    return {str(p): digest(p) for p in root.rglob("*") if p.is_file()}


def direct_cells(name, body, rows):
    """Independent source-cell reads, without calling production table parsing."""
    if name.endswith(".xlsx"):
        book = openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=False)
        selected = set(rows)
        values = {
            i: row for i, row in enumerate(book["All"].values, 1) if i in selected
        }
        book.close()
        return values
    book = xlrd.open_workbook(file_contents=body)
    sheet = book.sheet_by_name("All")
    return {i: sheet.row_values(i - 1) for i in rows}


def independent_xml_cells(body):
    """Third path for latest XLSX spot checks: stdlib XML, no Excel reader."""
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        sheet = next(
            s for s in workbook.find("s:sheets", ns) if s.attrib["name"] == "All"
        )
        relations = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(
            r.attrib["Target"]
            for r in relations
            if r.attrib["Id"] == sheet.attrib[f"{{{rel}}}id"]
        )
        path = target.lstrip("/") if target.startswith("/") else "xl/" + target
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = [
                "".join(v.itertext())
                for v in ET.fromstring(z.read("xl/sharedStrings.xml"))
            ]
        cells = {}
        for c in ET.fromstring(z.read(path)).findall(".//s:c", ns):
            if c.attrib["r"] not in {"D5", "D11", "D131"}:
                continue
            v = c.find("s:v", ns)
            value = v.text if v is not None else "".join(c.find("s:is", ns).itertext())
            cells[c.attrib["r"]] = (
                strings[int(value)] if c.attrib.get("t") == "s" else value
            )
        return cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--snapshot-id", default="2026-11-21-task009-2")
    args = parser.parse_args()
    root, snapshot = args.root, args.snapshot_id
    path = root / "processed" / "ons_ashe" / f"snapshot={snapshot}"
    manifest = verify_bundle(path)
    frame = pd.read_parquet(path / "observations.parquet")
    entries = ons_ashe.load_inventory(Path("configs/ons_ashe_editions.json"))
    prior = json.loads(
        Path("reports/data_audits/009.1/coverage-quality-evidence.json").read_text(
            encoding="utf-8"
        )
    )["editions"]
    assert len(entries) == len(manifest["validation"]) == len(prior) == 37
    assert set(frame.observation_year) == set(range(2002, 2027))
    comparisons, cell_count, spots = [], 0, {}
    for entry, report, previous in zip(entries, manifest["validation"], prior):
        key = entry["edition_id"]
        raw = root / "raw" / "ons_ashe" / f"snapshot={snapshot}" / key
        meta = verify_bundle(raw)
        assert meta["source_sha256"] == previous["source_zip_sha256"]
        for name in ("exact_cohort_matches", "numeric_cohort_medians"):
            assert report[name] == previous[name]
        assert report["coded_rows"] == previous["source_coded_geography_rows"]
        assert report["cohort_pay_markers"] == previous["cohort_markers"]
        assert report["legacy_code_collisions"] == previous["duplicate_source_codes"]
        selected = frame[frame.source_edition_id == key]
        assert len(selected) == report["source_rows"]
        assert selected.source_url.eq(entry["url"]).all()
        assert selected.source_sha256.eq(meta["source_sha256"]).all()
        assert selected.retrieved_at.eq(meta["retrieval"]["retrieved_at"]).all()
        with zipfile.ZipFile(raw / "response.bin") as archive:
            for kind, column, value_column, text_column in (
                ("pay", "source_row", "annual_gross_median_gbp", "pay_source_text"),
                ("cv", "cv_source_row", "median_cv_percent", "cv_source_text"),
            ):
                name = report[kind]["workbook"]
                body = archive.read(name)
                assert (
                    hashlib.sha256(body).hexdigest() == report[kind]["workbook_sha256"]
                )
                cells = direct_cells(name, body, selected[column].tolist())
                for record in selected.to_dict("records"):
                    source = cells[record[column]]
                    assert source[0] == record["source_name"]
                    code_column = (
                        "source_code_raw" if kind == "pay" else "cv_source_code_raw"
                    )
                    assert ("" if source[1] is None else str(source[1])) == record[
                        code_column
                    ]
                    value = source[3]
                    assert ("" if value is None else str(value)) == record[text_column]
                    if isinstance(value, (float, int)):
                        assert value == record[value_column]
                    else:
                        assert math.isnan(record[value_column])
                    cell_count += 1
                if key == "2026provisional" and kind == "pay":
                    spots = independent_xml_cells(body)
        comparisons.append(
            dict(
                edition_id=key,
                observation_year=entry["observation_year"],
                source_rows=len(selected),
                coded_rows=report["coded_rows"],
                exact_cohort_matches=report["exact_cohort_matches"],
                numeric_cohort_medians=report["numeric_cohort_medians"],
                cohort_pay_markers=report["cohort_pay_markers"],
                missing_cohort_codes=report["missing_cohort_codes"],
                population_note_conflict=report["pay"]["population_note_conflict"]
                or report["cv"]["population_note_conflict"],
                source_sha256=meta["source_sha256"],
                all_source_cells_match=True,
            )
        )
    assert (
        spots["D5"] == "Median"
        and float(spots["D11"]) == 34199.3
        and spots["D131"] == "x"
    )
    assert set(frame.loc[frame.population_note_conflict, "source_edition_id"]) == {
        "2022revised",
        "2023provisional",
    }
    unknown = frame.loc[frame.source_release_date.isna(), "source_edition_id"].unique()
    assert len(unknown) == 35
    known = frame.loc[frame.source_release_date.notna()]
    assert set(known.source_edition_id) == {"2025revised", "2026provisional"}
    assert known.source_release_date.eq("2026-10-22").all()
    snapshots = [
        root / layer / "ons_ashe" / f"snapshot={snapshot}"
        for layer in ("raw", "validated", "processed")
    ]
    # Earlier production outputs are checked too; no ignored investigation cache
    # or old datasets are rewritten by the validator.
    earlier = [
        root / layer / dataset
        for layer in ("raw", "validated", "processed")
        for dataset in ("ons_pipr", "bank_of_england", "ons_inflation", "uk_hpi")
    ]
    before = {
        k: v for directory in snapshots + earlier for k, v in files(directory).items()
    }

    def offline(url):
        raise AssertionError("Rerun attempted network access")

    ons_ashe.ingest(root, snapshot, downloader=offline)
    after = {
        k: v for directory in snapshots + earlier for k, v in files(directory).items()
    }
    assert before == after
    result = dict(
        status="pass",
        snapshot_id=snapshot,
        edition_count=37,
        observation_years=[2002, 2026],
        source_observations=len(frame),
        independently_compared_pay_cv_cells=cell_count,
        all_cells_match=True,
        stdlib_xml_spots_2026=spots,
        investigation_hashes_and_coverage_reconciled=True,
        unknown_historical_availability_editions=len(unknown),
        population_note_conflict_editions=["2022revised", "2023provisional"],
        unchanged_files_on_offline_rerun=len(before),
        unchanged_earlier_production_files=sum(len(files(p)) for p in earlier),
        editions=comparisons,
    )
    out = Path("reports/data_audits/009.2/validation-evidence.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "editions"}, indent=2))


if __name__ == "__main__":
    main()
