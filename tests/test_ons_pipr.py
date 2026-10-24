from __future__ import annotations

import json
import zipfile
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
import pytest

from ingestion.ons_pipr import (
    BEDROOM_COLUMNS,
    DEFAULT_RELEASE_ID,
    EXCLUDED_GEOGRAPHIES,
    TABLE_IDENTIFIER,
    DataValidationError,
    GeographyReference,
    IngestionError,
    WorkbookStructureError,
    _parse_month,
    extract_pipr_rows,
    load_geography_reference,
    parse_long_observations,
    run_ingestion,
    validate_panel,
)
from ingestion import ons_pipr as pipr


ROOT = Path(__file__).resolve().parents[1]
GEOGRAPHY_PATH = ROOT / "configs" / "ons_lad_apr2025_v2.csv"
HEADINGS = [
    "Time period",
    "Area code",
    "Area name",
    *BEDROOM_COLUMNS.values(),
]


def _column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _inline_cell(address: str, value: str) -> str:
    return (
        f'<c r="{address}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    )


def _number_cell(address: str, value: float | int) -> str:
    return f'<c r="{address}" t="n"><v>{value}</v></c>'


def _excel_serial(month: date) -> int:
    return (datetime.combine(month, datetime.min.time()) - datetime(1899, 12, 30)).days


def make_workbook(
    path: Path,
    rows: list[dict[str, object]],
    *,
    headings: list[str] | None = None,
    table_identifier: str = TABLE_IDENTIFIER,
) -> Path:
    headings = headings or HEADINGS
    worksheet_rows = []
    header_cells = "".join(
        _inline_cell(f"{_column_name(index)}1", heading)
        for index, heading in enumerate(headings, 1)
    )
    worksheet_rows.append(f'<row r="1">{header_cells}</row>')
    for row_number, row in enumerate(rows, 2):
        cells = []
        for index, heading in enumerate(headings, 1):
            value = row.get(heading)
            address = f"{_column_name(index)}{row_number}"
            if value is None:
                continue
            if isinstance(value, (float, int)):
                cells.append(_number_cell(address, value))
            else:
                cells.append(_inline_cell(address, str(value)))
        worksheet_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')
    last_column = _column_name(len(headings))
    last_row = len(rows) + 1
    table_columns = "".join(
        f'<tableColumn id="{index}" name="{escape(name)}"/>'
        for index, name in enumerate(headings, 1)
    )
    files = {
        "[Content_Types].xml": (
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            "</Types>"
        ),
        "xl/workbook.xml": (
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Table 1" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/></Relationships>'
        ),
        "xl/worksheets/sheet1.xml": (
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheetData>{"".join(worksheet_rows)}</sheetData>'
            '<tableParts count="1"><tablePart r:id="rId1"/></tableParts></worksheet>'
        ),
        "xl/worksheets/_rels/sheet1.xml.rels": (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" '
            'Target="../tables/table1.xml"/></Relationships>'
        ),
        "xl/tables/table1.xml": (
            '<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'id="1" name="{table_identifier}" displayName="{table_identifier}" '
            f'ref="A1:{last_column}{last_row}">'
            f'<tableColumns count="{len(headings)}">{table_columns}</tableColumns></table>'
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return path


def source_row(
    month: date,
    code: str = "E06000001",
    name: str = "Hartlepool",
    one_bed: object = 400,
    two_bed: object = 500,
    three_bed: object = 600,
) -> dict[str, object]:
    return {
        "Time period": _excel_serial(month),
        "Area code": code,
        "Area name": name,
        "Rental price one bed": one_bed,
        "Rental price two bed": two_bed,
        "Rental price three bed": three_bed,
    }


def small_geography() -> GeographyReference:
    return GeographyReference(
        eligible_names={
            "E06000001": "Hartlepool",
            "E06000002": "Middlesbrough",
        },
        excluded_names=EXCLUDED_GEOGRAPHIES,
        version="LAD_APR_2025_UK_NC_v2",
    )


def complete_small_panel() -> pd.DataFrame:
    geography = small_geography()
    rows = []
    for month in (
        date(2020, 1, 1),
        date(2020, 2, 1),
        date(2020, 3, 1),
        date(2020, 4, 1),
    ):
        for code, name in geography.eligible_names.items():
            rows.append(source_row(month, code, name))
    frame, _ = parse_long_observations(rows, geography, "2020-04-01")
    return frame


def _full_release_inputs(
    tmp_path: Path, months: tuple[date, ...]
) -> tuple[Path, Path, Path]:
    geography = load_geography_reference(GEOGRAPHY_PATH)
    rows = []
    for month_index, month in enumerate(months):
        for index, (code, name) in enumerate(geography.eligible_names.items()):
            rent = 500 + index + month_index
            rows.append(
                source_row(month, code, name, rent, rent + 100, rent + 200)
            )
    workbook = make_workbook(tmp_path / "input.xlsx", rows)
    config_dir = tmp_path / "project" / "configs"
    config_dir.mkdir(parents=True)
    data_root = tmp_path / "project" / "data"
    config_path = config_dir / "storage.toml"
    config_path.write_text(
        f'backend = "local"\nlocal_root = "{data_root.as_posix()}"\n',
        encoding="utf-8",
    )
    return config_path, workbook, data_root


def _ingest_full_release(
    config_path: Path,
    workbook: Path,
    *,
    release_id: str = "2020-03-01",
    expected_start_month: str = "2020-01",
    expected_end_month: str = "2020-02",
) -> dict[str, object]:
    return run_ingestion(
        config_path=config_path,
        geography_path=GEOGRAPHY_PATH,
        release_id=release_id,
        source_url="local-test-fixture",
        local_workbook=workbook,
        expected_start_month=expected_start_month,
        expected_end_month=expected_end_month,
    )


def test_extracts_named_table_and_required_columns(tmp_path: Path) -> None:
    workbook = make_workbook(tmp_path / "sample.xlsx", [source_row(date(2020, 1, 1))])

    rows, metadata = extract_pipr_rows(workbook)

    assert rows[0]["Time period"] == "43831"
    assert rows[0]["Area code"] == "E06000001"
    assert rows[0]["Rental price three bed"] == "600"
    assert metadata["worksheet"] == "Table 1"
    assert metadata["table_identifier"] == TABLE_IDENTIFIER
    assert metadata["table_row_count"] == 1


def test_wide_to_long_maps_bedrooms_and_month() -> None:
    frame, _ = parse_long_observations(
        [source_row(date(2020, 1, 1))], small_geography(), "2020-02-01"
    )

    assert frame["bedroom_count"].tolist() == [1, 2, 3]
    assert frame["average_monthly_rent_gbp"].tolist() == [400.0, 500.0, 600.0]
    assert frame["observation_month"].dt.strftime("%Y-%m-%d").tolist() == [
        "2020-01-01",
    ] * 3
    assert frame["source_release_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2020-02-01",
    ] * 3
    assert frame["source_vintage_id"].tolist() == ["2020-02-01"] * 3


def test_filters_aggregate_rows_and_explicit_exclusions() -> None:
    rows = [
        source_row(date(2020, 1, 1)),
        source_row(date(2020, 1, 1), "E09000001", "City of London"),
        source_row(date(2020, 1, 1), "E06000053", "Isles of Scilly"),
        source_row(date(2020, 1, 1), "K02000001", "United Kingdom"),
    ]

    frame, metadata = parse_long_observations(rows, small_geography(), "2020-02-01")

    assert set(frame["local_authority_code"].astype(str)) == {"E06000001"}
    assert metadata["exclusion_observations"] == {
        "E09000001": 1,
        "E06000053": 1,
    }


def test_pinned_geography_reference_has_approved_cohort() -> None:
    geography = load_geography_reference(GEOGRAPHY_PATH)

    assert len(geography.eligible_names) == 294
    assert geography.excluded_names == EXCLUDED_GEOGRAPHIES
    assert geography.version == "LAD_APR_2025_UK_NC_v2"


def test_missing_required_heading_fails_closed(tmp_path: Path) -> None:
    headings = [heading for heading in HEADINGS if heading != "Rental price two bed"]
    workbook = make_workbook(
        tmp_path / "wrong-schema.xlsx",
        [source_row(date(2020, 1, 1))],
        headings=headings,
    )

    with pytest.raises(WorkbookStructureError, match="Rental price two bed"):
        extract_pipr_rows(workbook)


def test_unexpected_table_identifier_fails_closed(tmp_path: Path) -> None:
    workbook = make_workbook(
        tmp_path / "wrong-table.xlsx",
        [source_row(date(2020, 1, 1))],
        table_identifier="Other_Table",
    )

    with pytest.raises(WorkbookStructureError, match="Expected one table"):
        extract_pipr_rows(workbook)


def test_duplicate_la_month_rows_are_rejected_by_validation() -> None:
    rows = [
        source_row(date(2020, 1, 1)),
        source_row(date(2020, 1, 1)),
    ]
    frame, _ = parse_long_observations(rows, small_geography(), "2020-02-01")

    report = validate_panel(frame, small_geography(), "2020-02-01")

    assert report.duplicate_keys == 3
    assert any("duplicate" in message.lower() for message in report.errors)


@pytest.mark.parametrize(
    ("rent", "message"),
    [
        (None, "Missing 1-bed rent"),
        ("[x]", "Non-numeric 1-bed rent"),
        (0, "finite and positive"),
        (-1, "finite and positive"),
    ],
)
def test_null_non_numeric_and_non_positive_rents_fail_validation(
    rent: object, message: str
) -> None:
    frame, metadata = parse_long_observations(
        [source_row(date(2020, 1, 1), one_bed=rent)],
        small_geography(),
        "2020-02-01",
    )
    frame.attrs["value_errors"] = metadata["value_errors"]

    report = validate_panel(frame, small_geography(), "2020-02-01")

    assert report.status == "failed"
    assert any(message in error for error in report.errors)


def test_rejects_ambiguous_or_invalid_months() -> None:
    with pytest.raises(DataValidationError, match="Ambiguous or invalid"):
        _parse_month("2020/01", 7)
    with pytest.raises(DataValidationError, match="not the first of a month"):
        _parse_month("2020-01-02", 7)


def test_isolated_missing_month_is_reported() -> None:
    geography = small_geography()
    frame = complete_small_panel()
    missing = (
        (frame["local_authority_code"] == "E06000001")
        & (frame["bedroom_count"] == 2)
        & (frame["observation_month"] == pd.Timestamp("2020-02-01"))
    )

    report = validate_panel(frame.loc[~missing], geography, "2020-04-01")

    assert report.missing_cells == 1
    assert report.missing_gap_sequences == [
        {
            "local_authority_code": "E06000001",
            "local_authority_name": "Hartlepool",
            "bedroom_count": 2,
            "gap_start_month": "2020-02",
            "gap_end_month": "2020-02",
            "gap_length_months": 1,
            "classification": "isolated_internal_missing",
        }
    ]


def test_consecutive_and_entirely_absent_series_are_classified() -> None:
    geography = small_geography()
    frame = complete_small_panel()
    missing = (
        (frame["local_authority_code"] == "E06000001")
        & (frame["bedroom_count"] == 1)
        & frame["observation_month"].isin(
            [pd.Timestamp("2020-02-01"), pd.Timestamp("2020-03-01")]
        )
    ) | (
        (frame["local_authority_code"] == "E06000002")
        & (frame["bedroom_count"] == 3)
    )

    report = validate_panel(frame.loc[~missing], geography, "2020-04-01")
    classifications = {
        (gap["local_authority_code"], gap["bedroom_count"]): gap
        for gap in report.missing_gap_sequences
    }

    assert classifications["E06000001", 1]["classification"] == "internal_consecutive_gap"
    assert classifications["E06000001", 1]["gap_length_months"] == 2
    assert classifications["E06000002", 3]["classification"] == "entirely_absent_series"


def test_reference_release_coverage_is_enforced() -> None:
    frame = complete_small_panel()

    report = validate_panel(frame, small_geography(), DEFAULT_RELEASE_ID)

    assert any("Reference release" in error for error in report.errors)


def test_manifest_checksum_and_idempotent_parquet_round_trip(tmp_path: Path) -> None:
    geography = load_geography_reference(GEOGRAPHY_PATH)
    rows = []
    start = date(2020, 1, 1)
    for month_offset, month in enumerate((start, date(2020, 2, 1))):
        for index, (code, name) in enumerate(geography.eligible_names.items()):
            rent = 500 + index + month_offset
            rows.append(source_row(month, code, name, rent, rent + 100, rent + 200))
    workbook = make_workbook(tmp_path / "input.xlsx", rows)
    project = tmp_path / "project"
    config_dir = project / "configs"
    config_dir.mkdir(parents=True)
    data_root = project / "local-data"
    (config_dir / "storage.toml").write_text(
        f'backend = "local"\nlocal_root = "{data_root.as_posix()}"\n',
        encoding="utf-8",
    )
    config_path = config_dir / "storage.toml"

    result = run_ingestion(
        config_path=config_path,
        geography_path=GEOGRAPHY_PATH,
        release_id="2020-03-01",
        source_url="local-test-fixture",
        local_workbook=workbook,
        expected_start_month="2020-01",
        expected_end_month="2020-02",
    )

    parquet_path = Path(result["output_parquet"])
    output = pd.read_parquet(parquet_path)
    assert len(output) == 294 * 3 * 2
    assert not output.duplicated(
        ["local_authority_code", "bedroom_count", "observation_month"]
    ).any()
    assert output["bedroom_count"].dtype == "int8"
    assert result["local_authorities"] == 294
    assert result["missing_cells"] == 0
    assert Path(result["validated_parquet"]).is_file()
    with Path(result["manifest"]).open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert manifest["processed_parquet_sha256"] == result["processed_parquet_sha256"]
    assert manifest["raw_sha256"]
    assert manifest["published_at"] is None
    assert manifest["validation_outcome"] == "passed"

    rerun = run_ingestion(
        config_path=config_path,
        geography_path=GEOGRAPHY_PATH,
        release_id="2020-03-01",
        source_url="local-test-fixture",
        local_workbook=workbook,
        expected_start_month="2020-01",
        expected_end_month="2020-02",
    )
    assert rerun["status"] == "reused"


def test_conflicting_local_bytes_cannot_overwrite_release_snapshot(
    tmp_path: Path,
) -> None:
    geography = load_geography_reference(GEOGRAPHY_PATH)
    rows = []
    month = date(2020, 1, 1)
    for index, (code, name) in enumerate(geography.eligible_names.items()):
        rent = 500 + index
        rows.append(source_row(month, code, name, rent, rent + 100, rent + 200))
    first = make_workbook(tmp_path / "first.xlsx", rows)
    second_rows = [dict(row) for row in rows]
    second_rows[0]["Rental price one bed"] = 999
    second = make_workbook(tmp_path / "second.xlsx", second_rows)
    raw_root = tmp_path / "raw"

    from ingestion.ons_pipr import obtain_raw_snapshot

    obtain_raw_snapshot(raw_root, "2020-02-01", "local-test-fixture", local_workbook=first)
    with pytest.raises(IngestionError, match="bytes differ"):
        obtain_raw_snapshot(
            raw_root, "2020-02-01", "local-test-fixture", local_workbook=second
        )


def test_validation_failure_does_not_publish_final_parquet(tmp_path: Path) -> None:
    geography = load_geography_reference(GEOGRAPHY_PATH)
    rows = []
    month = date(2020, 1, 1)
    for index, (code, name) in enumerate(geography.eligible_names.items()):
        if index == 0:
            continue
        rent = 500 + index
        rows.append(source_row(month, code, name, rent, rent + 100, rent + 200))
    workbook = make_workbook(tmp_path / "incomplete.xlsx", rows)
    project = tmp_path / "project"
    config_dir = project / "configs"
    config_dir.mkdir(parents=True)
    data_root = project / "data"
    config_path = config_dir / "storage.toml"
    config_path.write_text(
        f'backend = "local"\nlocal_root = "{data_root.as_posix()}"\n',
        encoding="utf-8",
    )

    with pytest.raises(DataValidationError, match="Missing approved Local Authority"):
        run_ingestion(
            config_path=config_path,
            geography_path=GEOGRAPHY_PATH,
            release_id="2020-02-01",
            source_url="local-test-fixture",
            local_workbook=workbook,
            expected_start_month="2020-01",
            expected_end_month="2020-01",
        )

    assert not list((data_root / "processed").rglob("rent_observations.parquet"))
    assert not list((data_root / "validated").rglob("rent_observations.parquet"))
    report = data_root / "validation_reports" / "ons_pipr" / "release=2020-02-01"
    assert (report / "validation_summary.txt").is_file()
    assert (report / "validation_summary.json").is_file()


def test_unexpected_workbook_layout_writes_failure_report_without_parquet(
    tmp_path: Path,
) -> None:
    workbook = make_workbook(
        tmp_path / "changed-layout.xlsx",
        [source_row(date(2020, 1, 1))],
        headings=[heading for heading in HEADINGS if heading != "Rental price two bed"],
    )
    config_dir = tmp_path / "project" / "configs"
    config_dir.mkdir(parents=True)
    data_root = tmp_path / "project" / "data"
    config_path = config_dir / "storage.toml"
    config_path.write_text(
        f'backend = "local"\nlocal_root = "{data_root.as_posix()}"\n',
        encoding="utf-8",
    )

    with pytest.raises(DataValidationError, match="Validation report"):
        run_ingestion(
            config_path=config_path,
            geography_path=GEOGRAPHY_PATH,
            release_id="2020-02-01",
            source_url="local-test-fixture",
            local_workbook=workbook,
            expected_start_month="2020-01",
            expected_end_month="2020-01",
        )

    assert not list((data_root / "processed").rglob("rent_observations.parquet"))
    report = (
        data_root
        / "validation_reports"
        / "ons_pipr"
        / "release=2020-02-01"
        / "validation_summary.txt"
    )
    assert "Rental price two bed" in report.read_text(encoding="utf-8")


@pytest.mark.parametrize("layer", ["processed", "validated"])
def test_corrupt_existing_parquet_fails_without_replacing_it(
    tmp_path: Path, layer: str
) -> None:
    config_path, workbook, data_root = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )
    result = _ingest_full_release(config_path, workbook)
    output = Path(result["output_parquet" if layer == "processed" else "validated_parquet"])
    output.write_bytes(output.read_bytes() + b"corruption")
    damaged_bytes = output.read_bytes()

    with pytest.raises(IngestionError, match="checksum"):
        _ingest_full_release(config_path, workbook)

    assert output.read_bytes() == damaged_bytes


def test_modified_manifest_fails_closed(tmp_path: Path) -> None:
    config_path, workbook, _ = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )
    result = _ingest_full_release(config_path, workbook)
    manifest_path = Path(result["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_url"] = "different-source"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(IngestionError, match="manifest"):
        _ingest_full_release(config_path, workbook)


def test_completed_release_with_rechecksummed_duplicate_content_is_rejected(
    tmp_path: Path,
) -> None:
    config_path, workbook, _ = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )
    result = _ingest_full_release(config_path, workbook)
    processed_path = Path(result["output_parquet"])
    processed = pd.read_parquet(processed_path)
    processed.loc[0, "local_authority_code"] = processed.loc[3, "local_authority_code"]
    processed.to_parquet(processed_path, index=False, engine="pyarrow")
    checksum = pipr._sha256(processed_path)
    for manifest_path in (
        Path(result["manifest"]),
        processed_path.parents[3]
        / "validated"
        / "ons_pipr"
        / "release=2020-03-01"
        / "manifest.json",
    ):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["processed_parquet_sha256"] = checksum
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(IngestionError, match="duplicate observation keys"):
        _ingest_full_release(config_path, workbook)


def test_missing_required_release_file_fails_closed(tmp_path: Path) -> None:
    config_path, workbook, _ = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )
    result = _ingest_full_release(config_path, workbook)
    report_path = Path(result["manifest"]).parent / "validation_summary.txt"
    report_path.unlink()

    with pytest.raises(IngestionError, match="incomplete"):
        _ingest_full_release(config_path, workbook)


def test_interrupted_publication_recovers_without_overwriting_layer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, workbook, data_root = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )
    original_rename = pipr.os.rename
    rename_calls = 0

    def fail_after_first_layer(source: str | Path, destination: str | Path) -> None:
        nonlocal rename_calls
        rename_calls += 1
        if rename_calls == 2:
            raise OSError("simulated interruption between layer publications")
        original_rename(source, destination)

    monkeypatch.setattr(pipr.os, "rename", fail_after_first_layer)
    with pytest.raises(OSError, match="simulated interruption"):
        _ingest_full_release(config_path, workbook)
    validated_dir = data_root / "validated" / "ons_pipr" / "release=2020-03-01"
    existing_bytes = (validated_dir / "rent_observations.parquet").read_bytes()
    assert not (data_root / "processed" / "ons_pipr" / "release=2020-03-01").exists()

    monkeypatch.setattr(pipr.os, "rename", original_rename)
    recovered = _ingest_full_release(config_path, workbook)

    assert recovered["status"] == "created"
    assert (validated_dir / "rent_observations.parquet").read_bytes() == existing_bytes
    assert (
        data_root
        / "processed"
        / "ons_pipr"
        / "release=2020-03-01"
        / "_SUCCESS.json"
    ).is_file()


def test_future_release_accepts_additional_month_when_expected(tmp_path: Path) -> None:
    config_path, workbook, _ = _full_release_inputs(
        tmp_path,
        (date(2020, 1, 1), date(2020, 2, 1), date(2020, 3, 1)),
    )

    result = _ingest_full_release(
        config_path,
        workbook,
        expected_end_month="2020-03",
    )

    assert result["status"] == "created"
    assert result["observation_end"] == "2020-03"
    assert result["rows"] == 294 * 3 * 3


def test_future_release_missing_expected_latest_month_fails(tmp_path: Path) -> None:
    config_path, workbook, data_root = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )

    with pytest.raises(DataValidationError, match="Expected last month"):
        _ingest_full_release(
            config_path,
            workbook,
            expected_end_month="2020-03",
        )

    assert not list((data_root / "processed").rglob("rent_observations.parquet"))


def test_more_than_25_large_movements_retains_all_details() -> None:
    movement_frame = pd.DataFrame(
        [
            {
                "local_authority_code": f"E{index:08d}",
                "local_authority_name": f"Area {index}",
                "bedroom_count": bedroom,
                "observation_month": pd.Timestamp(month),
                "average_monthly_rent_gbp": rent,
            }
            for index in range(9)
            for bedroom in (1, 2, 3)
            for month, rent in (
                ("2020-01-01", 100.0),
                ("2021-01-01", 130.0),
            )
        ]
    )

    total, displayed, details = pipr._large_movements(movement_frame, 20.0)

    assert total == 27
    assert len(displayed) == 25
    assert len(details) == 27


@pytest.mark.parametrize(
    ("release_id", "source_url", "message"),
    [
        ("2026-02-30", "local-test-fixture", "valid calendar date"),
        (
            "2026-10-20",
            pipr.DEFAULT_DOWNLOAD_URL,
            "does not match the edition",
        ),
    ],
)
def test_release_identity_checks_fail_before_io(
    tmp_path: Path, release_id: str, source_url: str, message: str
) -> None:
    with pytest.raises(IngestionError, match=message):
        run_ingestion(
            config_path=tmp_path / "missing.toml",
            geography_path=GEOGRAPHY_PATH,
            release_id=release_id,
            source_url=source_url,
            local_workbook=tmp_path / "offline.xlsx",
        )


def test_non_reference_release_requires_explicit_expected_end(tmp_path: Path) -> None:
    with pytest.raises(IngestionError, match="expected-end-month"):
        run_ingestion(
            config_path=tmp_path / "missing.toml",
            geography_path=GEOGRAPHY_PATH,
            release_id="2020-03-01",
            source_url="local-test-fixture",
            local_workbook=tmp_path / "offline.xlsx",
        )


def test_offline_local_workbook_ingestion_and_idempotent_reuse(
    tmp_path: Path,
) -> None:
    config_path, workbook, _ = _full_release_inputs(
        tmp_path, (date(2020, 1, 1), date(2020, 2, 1))
    )
    first = _ingest_full_release(config_path, workbook)
    second = _ingest_full_release(config_path, workbook)

    assert first["status"] == "created"
    assert second["status"] == "reused"


def test_expected_coverage_detects_a_missing_trailing_month() -> None:
    geography = small_geography()
    frame = complete_small_panel()
    frame = frame.loc[frame["observation_month"] < pd.Timestamp("2020-04-01")]

    report = validate_panel(
        frame,
        geography,
        "2020-04-01",
        expected_start_month="2020-01",
        expected_end_month="2020-04",
        require_complete_cohort=False,
    )

    assert report.status == "failed"
    assert any("Expected last month" in error for error in report.errors)
