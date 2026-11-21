"""Offline official M01 history/uncertainty audit; temporary xlrd==2.0.2."""

import csv
import io
import json
import re
from pathlib import Path

import xlrd

RAW = Path("data/raw/umb-009-3-investigation")
OUT = Path("reports/data_audits/009.3")


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
    evidence, tables = [], []
    current_rows = [
        r
        for f in sorted(RAW.glob("history*/response.bin"))
        for r in csv.DictReader(io.StringIO(f.read_text(encoding="utf-8-sig")))
    ]
    for name in ("m01_latest", "m01_previous"):
        book = xlrd.open_workbook(
            file_contents=(RAW / name / "response.bin").read_bytes()
        )
        rates = book.sheet_by_name("LA,UA Rates")
        headings = rates.row_values(2)
        row = next(
            i for i in range(rates.nrows) if rates.cell_value(i, 0) == "Hartlepool"
        )
        rate_columns = [i for i, label in enumerate(headings) if i >= 3 and label]
        notes = [
            str(rates.cell_value(i, 0))
            for i in range(rates.nrows)
            if str(rates.cell_value(i, 0)).startswith(("1.", "2.", "3."))
        ]
        index = book.sheet_by_name("Index")
        source_notes = [
            str(index.cell_value(i, 0))
            for i in range(index.nrows)
            if "first published" in str(index.cell_value(i, 0))
            or "final edition" in str(index.cell_value(i, 0))
        ]
        if "Note" in book.sheet_names():
            source_notes += [
                book.sheet_by_name("Note").cell_value(i, 0)
                for i in range(book.sheet_by_name("Note").nrows)
            ]
        data = {
            (str(rates.cell_value(i, 1)), str(headings[c]).strip()): rates.cell_value(
                i, c
            )
            for i in range(5, rates.nrows)
            if re.fullmatch(r"[A-Z]\d{8}", str(rates.cell_value(i, 1)))
            for c in rate_columns
        }
        tables.append(data)
        historical = []
        for col in rate_columns[:8]:
            source_rows = [
                i
                for i in range(5, rates.nrows)
                if re.fullmatch(r"E0[6789]\d{6}", str(rates.cell_value(i, 1)))
            ]
            selected = [i for i in source_rows if str(rates.cell_value(i, 1)) in cohort]
            historical.append(
                dict(
                    reference_period=headings[col],
                    reference_definition="March to February (2006 guide); not a calendar-year label",
                    source_english_la_rows=len(source_rows),
                    exact_cohort_rows=len(selected),
                    numeric_cohort_rates=sum(
                        isinstance(rates.cell_value(i, col), (float, int))
                        for i in selected
                    ),
                    missing_cohort_value_codes=[
                        str(rates.cell_value(i, 1))
                        for i in selected
                        if not isinstance(rates.cell_value(i, col), (float, int))
                    ],
                    unmatched_cohort_codes=sorted(
                        set(cohort) - {str(rates.cell_value(i, 1)) for i in selected}
                    ),
                )
            )
        selected_periods = [
            dict(
                source_column=col + 1,
                reference_period=headings[col],
                value=rates.cell_value(row, col),
                confidence=rates.cell_value(row, col + 1),
                confidence_header=rates.cell_value(3, col + 1),
            )
            for col in rate_columns
            if str(headings[col]).strip()
            in {
                "1996/97",
                "Jan 2004 to Dec 2004",
                "Jan 2019 to Dec 2019",
                "Apr 2021 to Mar 2022",
            }
        ]
        current = {
            r["MEASURES"]: float(r["OBS_VALUE"])
            for r in current_rows
            if r["DATE"] == "2022-03" and r["GEOGRAPHY_CODE"] == "E06000001"
        }
        if name == "m01_latest":
            proof = next(
                p
                for p in selected_periods
                if str(p["reference_period"]).strip() == "Apr 2021 to Mar 2022"
            )
            assert round(proof["value"], 1) == current["20100"]
            assert round(proof["confidence"], 1) == current["20701"]
        evidence.append(
            dict(
                source=name,
                reader_version=xlrd.__version__,
                sheet="LA,UA Rates",
                source_notes=source_notes,
                table_footnotes=notes,
                hartlepool_row=row + 1,
                hartlepool_examples=selected_periods,
                early_history=historical,
                latest_archive_rate_and_confidence_match_nomis_rounding=(
                    name == "m01_latest"
                ),
            )
        )
    common = set(tables[0]) & set(tables[1])
    both_numeric = [
        k
        for k in common
        if isinstance(tables[0][k], (float, int))
        and isinstance(tables[1][k], (float, int))
    ]
    result = dict(
        archives=evidence,
        common_code_period_cells=len(common),
        numeric_in_both=len(both_numeric),
        changed_numeric_rate_cells=sum(
            tables[0][k] != tables[1][k] for k in both_numeric
        ),
        comparison_scope="All coded LA/UA source rows, no geography mapping, no source edition preferred",
    )
    (OUT / "archive-evidence.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "archives"}, indent=2))
    print(
        "Historical coverage:",
        [
            (r["reference_period"], r["exact_cohort_rows"], r["numeric_cohort_rates"])
            for r in evidence[0]["early_history"]
        ],
    )
    print("Footnotes:", [(a["source"], a["table_footnotes"]) for a in evidence])


if __name__ == "__main__":
    main()
