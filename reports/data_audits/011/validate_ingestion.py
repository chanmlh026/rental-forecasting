"""Independent ODS XML reconciliation, native quality signals and offline replay."""

import io
import json
import re
import hashlib
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
import pandas as pd

from ingestion.boe import verify_bundle, safe_http_headers
from ingestion.ons_pipr import load_geography_reference
from ingestion.mhclg_housing import ingest

OUT = Path("reports/data_audits/011")
SNAPSHOT = "2026-11-22-task011"
RAW = Path("data/raw/mhclg_housing") / f"snapshot={SNAPSHOT}"
PRODUCT = Path("data/processed/mhclg_housing") / f"snapshot={SNAPSHOT}"
N = {
    k: "urn:oasis:names:tc:opendocument:xmlns:" + v + ":1.0"
    for k, v in {
        "o": "office",
        "t": "table",
        "x": "text",
        "s": "style",
        "f": "xsl-fo-compatible",
    }.items()
}


def attribute(node, ns, name, default=""):
    return node.get("{" + N[ns] + "}" + name, default) if node is not None else default


def source_text(node):
    pieces = [node.text or ""]
    for child in node:
        local = child.tag.split("}")[-1]
        if child.tag == "{" + N["x"] + "}s":
            value = " " * int(attribute(child, "x", "c", "1"))
        elif child.tag == "{" + N["x"] + "}tab":
            value = "\t"
        elif child.tag == "{" + N["x"] + "}line-break":
            value = "\n"
        else:
            value = source_text(child)
        pieces.extend([value, child.tail or ""])
    return "".join(pieces)


def unpack(path):
    with zipfile.ZipFile(path) as archive:
        assert (
            archive.read("mimetype")
            == b"application/vnd.oasis.opendocument.spreadsheet"
        )
        roots = {
            name: ET.fromstring(archive.read(name))
            for name in ("content.xml", "styles.xml")
        }
    tables = {
        attribute(t, "t", "name"): t
        for t in roots["content.xml"].findall(".//t:table", N)
    }
    return roots, tables


def grid(table, width):
    """Independently index source cells, retaining logical repeated-cell positions."""
    result = {}
    rn = 1
    row_defaults = {}
    column_defaults = {}
    cn = 1
    for column in table.findall(".//t:table-column", N):
        size = int(attribute(column, "t", "number-columns-repeated", "1"))
        for i in range(cn, min(cn + size, width + 1)):
            column_defaults[i] = attribute(column, "t", "default-cell-style-name")
        cn += size
    for row in table.findall(".//t:table-row", N):
        repeat = int(attribute(row, "t", "number-rows-repeated", "1"))
        cells = {}
        cn = 1
        has_content = False
        for cell in row:
            if cell.tag.split("}")[-1] not in {"table-cell", "covered-table-cell"}:
                continue
            size = int(attribute(cell, "t", "number-columns-repeated", "1"))
            text = "\n".join(source_text(p) for p in cell.findall("x:p", N))
            exists = bool(
                text or attribute(cell, "o", "value") or attribute(cell, "t", "formula")
            )
            has_content = has_content or exists
            if exists or cn <= width:
                for c in range(
                    cn,
                    min(cn + size, max(width + 1, cn + size) if exists else width + 1),
                ):
                    cells[c] = (cell, text)
            cn += size
        if has_content:
            for index in range(rn, rn + repeat):
                result[index] = cells
                row_defaults[index] = attribute(row, "t", "default-cell-style-name")
        rn += repeat
    return result, row_defaults, column_defaults


def effective_styles(roots):
    definitions = {}
    defaults = {}
    for root in roots.values():
        for node in root.findall(".//s:style", N):
            if attribute(node, "s", "family") == "table-cell":
                definitions[attribute(node, "s", "name")] = node
        for node in root.findall(".//s:default-style", N):
            if attribute(node, "s", "family") == "table-cell":
                defaults = {c.tag.split("}")[-1]: dict(c.attrib) for c in node}
    cache = {}

    def resolve(name):
        if name in cache:
            return cache[name]
        chain = []
        current = name
        seen = set()
        while current:
            assert current in definitions and current not in seen
            seen.add(current)
            node = definitions[current]
            chain.append(node)
            current = attribute(node, "s", "parent-style-name")
        result = {k: dict(v) for k, v in defaults.items()}
        for node in reversed(chain):
            for child in node:
                result.setdefault(child.tag.split("}")[-1], {}).update(child.attrib)
        cache[name] = result
        return result

    return resolve


def definition(table, sheet, header):
    if table == "125":
        year = int(header[:4])
        return (
            (
                "dwelling_stock_unrounded"
                if sheet.endswith("unrounded")
                else "dwelling_stock_rounded"
            ),
            str(year),
            "",
            "",
            f"{year}-03-31",
        )
    period = sheet if table == "123" else header
    year = int(period[:4])
    assert int(period[5:7]) == (year + 1) % 100
    measure = "net_additional_dwellings"
    if table == "123":
        label = " ".join(header.lower().split())
        labels = {
            "new build": "new_build_completions",
            "net additions": "net_additional_dwellings",
            "net conversions": "net_conversions",
            "net change of use": "net_change_of_use",
            "demolitions": "demolitions",
            "net other gains and losses": "net_other_gains_and_losses",
            "adjustment to census 2021": "census_2021_adjustment",
        }
        if label in labels:
            measure = labels[label]
        elif label == "of which under pdr":
            measure = "of_which_under_pdr_unspecified_source_label"
        else:
            assert label.startswith("of which under pdr:")
            measure = re.sub("[^a-z0-9]+", "_", label).strip("_")
    return measure, f"{year}-{year+1}", f"{year}-04-01", f"{year+1}-03-31", ""


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {str(p): checksum(p) for p in Path("data").rglob("*") if p.is_file()}


def assess_net_additions(first, second):
    """Report native cross-publication differences without adjusting either source.

    Same units/concept do not establish equal stored precision. This is an audit
    inventory, not an outlier tolerance, rounding policy or model-input choice.
    Exact per-source XML reconciliation remains a separate mandatory gate.
    """
    joined = first.merge(
        second, on=["source_code", "period"], suffixes=("_122", "_123")
    )
    numeric = joined.value_122.notna() & joined.value_123.notna()
    different = joined[numeric & joined.value_122.ne(joined.value_123)]
    differences = (different.value_122 - different.value_123).abs()
    result = dict(
        numeric_pairs=int(numeric.sum()),
        exact_value_differences=len(different),
        missing_or_marker_pairs=int((~numeric).sum()),
        max_observed_absolute_difference=(
            float(differences.max()) if len(differences) else 0.0
        ),
        differences_by_period=different.groupby("period").size().to_dict(),
        policy="Differences reported verbatim; no tolerance/rounding/transform/source choice; no stock-change equality or ratio",
        examples=different.head(5).to_dict("records"),
    )
    if "source_display_text_122" in different.columns:
        result["displayed_value_differences"] = int(
            different.source_display_text_122.ne(
                different.source_display_text_123
            ).sum()
        )
    return result


def main():
    baseline = json.loads(
        (OUT / "preservation-before.json").read_text(encoding="utf-8")
    )
    for p, value in baseline["files"].items():
        assert checksum(Path(p)) == value, f"Prior file changed: {p}"
    contract = json.loads(
        Path("configs/mhclg_housing_sources.json").read_text(encoding="utf-8")
    )
    frame = pd.read_parquet(PRODUCT / "observations.parquet")
    coverage = pd.read_parquet(PRODUCT / "coverage.parquet")
    note_frame = pd.read_parquet(PRODUCT / "notes.parquet")
    actual = {
        (r.edition_id, r.source_sheet, r.source_row, r.source_column): r
        for r in frame.itertuples()
    }
    assert len(actual) == len(frame)
    cohort = load_geography_reference(
        Path("configs/ons_lad_apr2025_v2.csv")
    ).eligible_names
    for layer in ("validated", "processed"):
        verify_bundle(Path("data") / layer / "mhclg_housing" / f"snapshot={SNAPSHOT}")
    for path in RAW.glob("*/manifest.json"):
        verify_bundle(path.parent)
        raw = json.loads(path.read_text(encoding="utf-8"))
        for name in ("request_headers", "response_headers"):
            if name in raw["retrieval"]:
                assert raw["retrieval"][name] == safe_http_headers(
                    raw["retrieval"][name]
                )
    expected = set()
    source_results = []
    note_cells = {}
    all_red = all_row_imputed = 0
    for source in contract["sources"]:
        name = source["edition_id"]
        number = source["table_id"]
        path = RAW / name / "response.bin"
        manifest = verify_bundle(path.parent)
        assert (
            checksum(path) == source["source_sha256"] == manifest["source_sha256"]
            and manifest["identity"]["url"] == source["url"]
        )
        roots, tables = unpack(path)
        resolve = effective_styles(roots)
        notes = {}
        red_legend = False
        for sn, table in tables.items():
            rows, _, _ = grid(table, 40)
            for rn, cells in rows.items():
                for cn, (cell, text) in cells.items():
                    note_cells[(name, sn, rn, cn)] = (cell, text)
                    if "Cells filled in red are imputed figures." in text:
                        red_legend = True
                if sn == "Notes" and cells.get(1, (None, ""))[1].startswith("["):
                    notes[cells[1][1]] = cells.get(2, (None, ""))[1]
        count = 0
        for schema in source["tables"]:
            sn = schema["sheet"]
            width = max(map(int, schema["column_labels"]))
            rows, rd, cd = grid(tables[sn], width)
            hr = schema["header_row"]
            code_col, name_col = (2, 3) if number == "125" else (3, 4)
            assert rows[1][1][1] == schema["title"]
            selected = {
                int(c): label
                for c, label in schema["column_labels"].items()
                if int(c) > name_col and label != "Notes"
            }
            assert {
                str(c): text for c, (_, text) in rows[hr].items() if text
            } == schema["column_labels"]
            for rn, cells in rows.items():
                if rn <= hr:
                    continue
                name_text = cells.get(name_col, (None, ""))[1]
                code = cells.get(code_col, (None, ""))[1]
                if not name_text or not any(
                    c in cells and (cells[c][1] or attribute(cells[c][0], "o", "value"))
                    for c in selected
                ):
                    continue
                row_note = (
                    cells.get(width, (None, ""))[1]
                    if schema["column_labels"][str(width)] == "Notes"
                    else ""
                )
                row_imputed = (
                    number == "123"
                    and "[note 1]" in (name_text + " " + row_note)
                    and "imputed" in notes.get("[note 1]", "")
                )
                for cn, label in selected.items():
                    key = (source["edition_id"], sn, rn, cn)
                    assert key not in expected
                    expected.add(key)
                    assert key in actual, key
                    result = actual[key]
                    cell, text = cells.get(cn, (None, ""))
                    raw = attribute(cell, "o", "value")
                    dtype = attribute(cell, "o", "value-type")
                    assert (result.source_code, result.source_name) == (
                        code,
                        name_text,
                    ), key
                    assert (
                        result.source_display_text == text
                        and result.source_xml_value == raw
                        and result.source_value_type == dtype
                    ), key
                    numeric = dtype == "float"
                    assert result.source_value_text == (raw if numeric else text), key
                    assert (
                        result.value == float(raw) if numeric else pd.isna(result.value)
                    ), key
                    assert not (
                        numeric and text.strip() in {"[x]", "..", "x"}
                    ), f"Conflicting published missing marker: {key}"
                    measure, period, start, end, refdate = definition(number, sn, label)
                    assert (
                        result.measure,
                        result.period,
                        result.period_start,
                        result.period_end,
                        result.reference_date,
                    ) == (measure, period, start, end, refdate), key
                    assert (
                        result.unit == "dwellings"
                        and result.source_header == label
                        and result.source_formula == attribute(cell, "t", "formula")
                    ), key
                    effective = (
                        attribute(cell, "t", "style-name")
                        or rd.get(rn, "")
                        or cd.get(cn, "")
                    )
                    props = resolve(effective)
                    background = props.get("table-cell-properties", {}).get(
                        "{" + N["f"] + "}background-color", ""
                    )
                    assert (
                        result.effective_style_name == effective
                        and json.loads(result.effective_style_properties_json) == props
                    ), key
                    assert (
                        result.source_background_color == background
                        and result.publisher_red_fill
                        == (background.lower() == "#ff0000")
                    ), key
                    assert result.publisher_imputation_row_note == row_imputed, key
                    flagged = bool(
                        row_imputed
                        or (
                            number == "123"
                            and red_legend
                            and background.lower() == "#ff0000"
                        )
                    )
                    assert (
                        result.publisher_imputation_flag == True
                        if flagged
                        else pd.isna(result.publisher_imputation_flag)
                    ), key
                    all_red += int(
                        number == "123"
                        and red_legend
                        and background.lower() == "#ff0000"
                    )
                    all_row_imputed += int(bool(row_imputed))
                    assert result.exact_cohort_code_match == (code in cohort), key
                    assert (
                        result.source_url == source["url"]
                        and result.source_sha256 == source["source_sha256"]
                        and result.retrieved_at == manifest["retrieval"]["retrieved_at"]
                    ), key
                    assert (
                        result.source_snapshot_id == SNAPSHOT
                        and result.future_denominator_candidate
                        == (measure == "dwelling_stock_unrounded")
                    ), key
                    count += 1
        sf = frame[frame.edition_id == name]
        source_results.append(
            dict(
                edition_id=name,
                table_id=number,
                source_cells_reconciled=count,
                source_sheets=len(source["tables"]),
                GSS_codes=sf.loc[sf.source_code.ne(""), "source_code"].nunique(),
                source_area_rows=sf[["source_sheet", "source_row"]]
                .drop_duplicates()
                .shape[0],
                periods=sorted(sf.period.unique().tolist()),
                numeric_cells=int(sf.value.notna().sum()),
                negative_cells=int(sf.value.lt(0).sum()),
                imputation_indicator_cells=int(
                    sf.publisher_imputation_flag.fillna(False).sum()
                ),
            )
        )
    assert expected == set(actual), "Extra or omitted source observations"
    for row in note_frame.itertuples():
        cell, text = note_cells[
            (row.edition_id, row.source_sheet, row.source_row, row.source_column)
        ]
        assert row.text == text and row.source_cell_xml == ET.tostring(
            cell, encoding="unicode"
        )
    for alias in contract["aliases"]:
        meta = verify_bundle(RAW / alias["edition_id"])
        assert meta["identity"]["url"] == alias["url"]
        assert (
            checksum(RAW / alias["edition_id"] / "response.bin")
            == checksum(RAW / alias["equivalent_primary"] / "response.bin")
            == alias["source_sha256"]
        )
    for row in coverage.itertuples():
        group = frame[
            (frame.edition_id == row.edition_id)
            & (frame.source_sheet == row.source_sheet)
            & (frame.measure == row.measure)
            & (frame.period == row.period)
        ]
        selected = group[group.source_code.isin(cohort)]
        assert (len(group), len(selected), selected.value.notna().sum()) == (
            row.source_area_rows,
            row.exact_cohort_matches,
            row.numeric_cohort_values,
        )
        assert json.loads(row.unmatched_target_codes_json) == sorted(
            set(cohort) - set(group.source_code)
        )
    prior = json.loads(
        Path("reports/data_audits/006.2/predictor-exploration-evidence.json").read_text(
            encoding="utf-8"
        )
    )["measurements"]
    for sn, measure, key in [
        ("LT_122", "net_additional_dwellings", "Live_Table_122.ods"),
        ("LT_125_unrounded", "dwelling_stock_unrounded", "LiveTable125.ods"),
    ]:
        group = coverage[(coverage.source_sheet == sn) & (coverage.measure == measure)]
        old = prior[key]["periods"]
        assert len(group) == len(old)
        for item in old:
            label = item["period"]
            period = (
                f"{int(label[:4])}-{int(label[:4])+1}" if sn == "LT_122" else label[:4]
            )
            assert (
                group[group.period == period].iloc[0].numeric_cohort_values
                == item["numeric"]
            ), (sn, period)
    for old in prior["Live_Table_123.ods"]:
        period = old.get("year", old.get("period"))
        group = coverage[
            (coverage.source_sheet == period)
            & (coverage.measure == "new_build_completions")
        ]
        assert (
            len(group) == 1
            and group.iloc[0].numeric_cohort_values == old["numeric_new_build"]
        ), period
    flow122 = frame[(frame.table_id == "122") & frame.source_code.ne("")][
        ["source_code", "period", "value"]
    ]
    flow123 = frame[
        (frame.table_id == "123")
        & (frame.measure == "net_additional_dwellings")
        & frame.source_code.ne("")
    ][["source_code", "period", "value", "source_display_text"]]
    same = flow122.merge(
        flow123, on=["source_code", "period"], suffixes=("_122", "_123")
    )
    numeric = same.value_122.notna() & same.value_123.notna()
    compatibility = assess_net_additions(flow122, flow123)
    for p in PRODUCT.glob("*.parquet"):
        pd.testing.assert_frame_equal(
            pd.read_parquet(p),
            pd.read_parquet(
                Path("data/validated/mhclg_housing") / f"snapshot={SNAPSHOT}" / p.name
            ),
        )
    before = inventory()

    def never(_):
        raise AssertionError("Offline replay attempted download")

    ingest(Path.cwd() / "data", SNAPSHOT, downloader=never)
    assert before == inventory(), "Offline replay changed saved bytes"
    result = dict(
        status="PASS WITH CONDITIONS",
        observations=len(frame),
        source_cells_reconciled=len(expected),
        source_results=source_results,
        source_note_cells_reconciled=len(note_frame),
        coverage_rows_reconciled=len(coverage),
        red_fill_imputation_cells=all_red,
        row_imputation_note_cells=all_row_imputed,
        imputation_indicator_cells=int(
            frame.publisher_imputation_flag.fillna(False).sum()
        ),
        source_value_kinds=frame.value_kind.value_counts().to_dict(),
        equivalent_net_additions_cells_compared=int(numeric.sum()),
        net_additions_compatibility=compatibility,
        net_additions_missing_or_marker_pairs=int((~numeric).sum()),
        attachment_aliases_byte_identical=len(contract["aliases"]),
        raw_bundles_verified=len(list(RAW.glob("*/manifest.json"))),
        prior_data_files_unchanged=len(baseline["files"]),
        offline_rerun_files_unchanged=len(before),
        cross_dataset_policy="Compare equivalent published net-additions cells; stock 31 March versus April-March flows and distinct publication vintages remain explicit. No stock-difference equality, ratio or denominator timing chosen.",
        conditions=[
            "Native geography and historical code gaps retained",
            "Publisher imputation/notes and inconsistent labels retained",
            "Historical first-publication availability incomplete; no model-input vintage",
            "Cross-table stored precision differs; raw differences retained without rounding/tolerance",
            "Ratio/stock-denominator timing requires future owner approval",
        ],
    )
    (OUT / "validation-evidence.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
