"""ASHE source identity, edition preservation, failure gates and recovery."""

import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import openpyxl
import pandas as pd
import pytest

from ingestion import ons_ashe as ashe
from ingestion import source_io


def entry(edition="2026provisional"):
    return dict(
        edition_id=edition,
        observation_year=2026,
        label=edition,
        status="provisional" if "provisional" in edition else "revised",
        url="https://www.ons.gov.uk/file?uri="
        + ashe.SOURCE_PATH
        + edition
        + "/table8.zip",
        publication_date="2026-10-22",
        publication_evidence_url="https://www.ons.gov.uk/release",
    )


def workbook(
    *, cv=False, split=False, year=2026, rows=None, header="Median", formula=False
):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "All"
    title = (
        f"Table 8.7{'b' if cv else 'a'} "
        + ("Coefficients of variation for " if cv else "")
        + "Annual pay - Gross (£)"
    )
    population = "For all employee jobs: United Kingdom" + ("" if split else f" {year}")
    sheet["A1"] = title if split else title + " - " + population
    if split:
        sheet["C1"] = population
    sheet.append([])
    sheet["A5"], sheet["B5"], sheet["C5"], sheet["D5"] = (
        "Description",
        "Code",
        "(thousand)",
        header,
    )
    rows = (
        rows
        if rows is not None
        else [
            ["United Kingdom", "", 1000, 5 if cv else 31000],
            ["Source Area", "'E06000001", 20, 7 if cv else 30000],
            ["Suppressed", "E06000002", 2, "x"],
            ["Inner London", "68", 20, "." if cv else 40000],
            ["  City of London", "68", 1, ".."],
            ["Unavailable", "E06000003", 1, None],
        ]
    )
    for i, row in enumerate(rows, 6):
        for j, value in enumerate(row, 1):
            sheet.cell(i, j, value)
    if formula:
        sheet["D7"] = "=1+1"
    sheet.cell(
        6 + len(rows),
        1,
        "a  Employees on adult rates who have been in the same job for more than a year.",
    )
    sheet.cell(7 + len(rows), 1, "KEY: retain original colours and uncertainty")
    sheet["D7"].fill = openpyxl.styles.PatternFill("solid", fgColor="FF00FF00")
    notes = book.create_sheet("Notes")
    notes.append(
        ["Annual estimates: tax year ending 5 April; all sexes, full-/part-time."]
    )
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def archive(pay=None, cv=None):
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as out:
        out.writestr("Home Table 8.7a Annual pay - Gross 2026.xlsx", pay or workbook())
        out.writestr(
            "Home Table 8.7b Annual pay - Gross 2026 CV.xlsx", cv or workbook(cv=True)
        )
    return result.getvalue()


def test_definition_alignment_quality_and_legacy_row_preservation():
    frame, notes, report = ashe.parse_archive(
        archive(),
        entry(),
        {
            "E06000001": "Approved Area",
            "E06000002": "Suppressed",
            "E06000004": "Absent",
        },
    )
    assert len(frame) == 6  # Includes uncoded national aggregate, both legacy rows.
    selected = frame.loc[frame.source_code == "E06000001"].iloc[0]
    assert selected.annual_gross_median_gbp == 30000
    assert selected.median_cv_percent == 7
    assert selected.source_code_raw == "'E06000001" and selected.source_name_differs
    assert "FF00FF00" in selected.pay_style_json
    assert report["missing_cohort_codes"] == ["E06000004"]
    assert report["legacy_code_collisions"] == {"68": 2}
    assert frame.pay_marker.dropna().tolist() == ["x", "..", ""]
    assert frame.median_cv_percent.isna().sum() == 4
    assert set(frame.source_row) == set(range(6, 12))
    assert notes.cells_json.str.contains("tax year").any()


def test_split_header_and_pay_cv_row_order():
    pay = workbook(split=True)
    # CV alignment uses source identity rather than accidental row position.
    reordered = [
        ["Source Area", "'E06000001", 20, 7],
        ["United Kingdom", "", 1000, 5],
        ["Suppressed", "E06000002", 2, "x"],
        ["Inner London", "68", 20, "."],
        ["  City of London", "68", 1, ".."],
        ["Unavailable", "E06000003", 1, None],
    ]
    frame, _, report = ashe.parse_archive(
        archive(pay, workbook(cv=True, rows=reordered)), entry(), {}
    )
    assert report["pay"]["year_evidence"] == "inventory_and_filename_split_header"
    assert frame.iloc[0].cv_source_row == 7 and frame.iloc[1].median_cv_percent == 7


@pytest.mark.parametrize("year", [2022, 2023])
@pytest.mark.parametrize("cv", [False, True])
def test_verified_split_schema_omits_unit_and_cv_descriptor(year, cv):
    book = openpyxl.load_workbook(io.BytesIO(workbook(split=True, cv=cv)))
    book["All"]["A1"] = f"Table 8.7{'b' if cv else 'a'} Annual pay - Gross"
    book["All"]["C1"] = "For all employee jobs(a): United Kingdom"
    output = io.BytesIO()
    book.save(output)
    _, _, proof = ashe.parse_workbook(
        f"Table 8.7 Annual pay Gross {year}.xlsx", output.getvalue(), year, cv=cv
    )
    assert (
        proof["unit_evidence"] == "Task009.1_verified_split_schema_and_table_identity"
    )
    with pytest.raises(ashe.IngestionError):
        ashe.parse_workbook("Table 2024.xlsx", output.getvalue(), 2024, cv=cv)


def test_conflicting_population_footnote_is_preserved_and_flagged():
    book = openpyxl.load_workbook(io.BytesIO(workbook(split=True)))
    book["All"]["A1"] = "Table 8.7a Annual pay - Gross"
    book["All"]["C1"] = "For all employee jobs(a): United Kingdom"
    book["All"][
        "A12"
    ] = "a  Employees on adult rates whose pay for the survey pay-period was not affected by absence."
    book["Notes"][
        "A1"
    ] = "Annual estimates relate to employees in the same job for more than a year."
    output = io.BytesIO()
    book.save(output)
    data, notes, proof = ashe.parse_workbook("Table 2022.xlsx", output.getvalue(), 2022)
    assert len(data) == 6 and proof["population_note_conflict"]
    assert any("not affected by absence" in n["cells_json"] for n in notes)
    assert any("same job for more than a year" in n["cells_json"] for n in notes)


@pytest.mark.parametrize(
    "change",
    [
        "header",
        "year",
        "formula",
        "mismatch",
        "duplicate",
        "badmarker",
        "moderncollision",
        "wrongtable",
    ],
)
def test_source_failures(change):
    pay, cv = workbook(), workbook(cv=True)
    if change == "header":
        pay = workbook(header="Mean")
    if change == "year":
        pay = workbook(year=2025)
    if change == "formula":
        pay = workbook(formula=True)
    if change == "mismatch":
        cv = workbook(cv=True, rows=[["Elsewhere", "123", 1, 7]])
    if change == "duplicate":
        pay = workbook(rows=[["Same", "68", 1, 4], ["Same", "68", 1, 5]])
    if change == "badmarker":
        pay = workbook(rows=[["Area", "68", 1, "unknown"]])
    if change == "moderncollision":
        rows = [["A", "E06000001", 1, 5], ["B", "E06000001", 1, 6]]
        pay, cv = workbook(rows=rows), workbook(cv=True, rows=rows)
    if change == "wrongtable":
        pay = workbook(cv=True)
    with pytest.raises(ashe.IngestionError):
        ashe.parse_archive(archive(pay, cv), entry(), {})


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "=1+1"])
def test_invalid_numeric_or_formula(value):
    with pytest.raises(ashe.IngestionError):
        ashe.cell_value(value)


def test_corrupt_zip_and_missing_member():
    with pytest.raises(ashe.IngestionError):
        ashe.parse_archive(b"truncated", entry(), {})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("unrelated.xlsx", workbook())
    with pytest.raises(ashe.IngestionError):
        ashe.parse_archive(stream.getvalue(), entry(), {})


def fixture_inventory(tmp_path, monkeypatch):
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps(dict(editions=[entry(), entry("2026revised")])))
    reference = tmp_path / "reference.csv"
    reference.write_text("fixture")
    monkeypatch.setattr(
        ashe,
        "load_geography_reference",
        lambda path: SimpleNamespace(
            eligible_names={"E06000001": "Approved Area", "E06000002": "Suppressed"}
        ),
    )
    return inventory, reference


def test_pipeline_editions_recovery_rerun_and_sanitised_metadata(tmp_path, monkeypatch):
    inventory, reference = fixture_inventory(tmp_path, monkeypatch)
    body = archive()

    def download(url):
        return body, dict(
            status=200,
            retrieved_at="2026-11-21T16:00:00+00:00",
            response_headers={
                "Set-Cookie": "SYNTHETIC_SESSION_ONLY",
                "Content-Type": "application/zip",
            },
        )

    original = source_io.publish

    def interrupt(directory, files, info):
        if "processed" in directory.parts:
            raise OSError("interruption")
        return original(directory, files, info)

    monkeypatch.setattr(source_io, "publish", interrupt)
    with pytest.raises(OSError, match="interruption"):
        ashe.ingest(
            tmp_path,
            "one",
            inventory=inventory,
            reference=reference,
            downloader=download,
            sleep=lambda _: None,
        )
    assert not (tmp_path / "processed/ons_ashe/snapshot=one").exists()
    monkeypatch.setattr(source_io, "publish", original)

    def offline(url):
        raise AssertionError("Unexpected network")

    kwargs = dict(inventory=inventory, reference=reference, downloader=offline)
    result = ashe.ingest(tmp_path, "one", **kwargs)
    frame = pd.read_parquet(Path(result["processed_path"]) / "observations.parquet")
    assert len(frame) == 12 and set(frame.source_edition_status) == {
        "provisional",
        "revised",
    }
    assert not result["exact_point_in_time"]
    assert frame.reference_period_end.eq("2026-04-05").all()
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    ashe.ingest(tmp_path, "one", **kwargs)
    assert all(p.read_bytes() == body for p, body in before.items())
    assert all(
        "SYNTHETIC_SESSION_ONLY" not in p.read_text()
        for p in tmp_path.rglob("manifest.json")
    )
    inventory.write_text(inventory.read_text() + "\n")
    with pytest.raises(ashe.IngestionError, match="conflict"):
        ashe.ingest(tmp_path, "one", **kwargs)


def test_no_partial_publication_for_bad_download(tmp_path, monkeypatch):
    inventory, reference = fixture_inventory(tmp_path, monkeypatch)

    def broken(url):
        return b"not a ZIP", dict(retrieved_at="2026-11-21T16:00:00+00:00")

    with pytest.raises(ashe.IngestionError):
        ashe.ingest(
            tmp_path,
            "bad",
            inventory=inventory,
            reference=reference,
            downloader=broken,
            sleep=lambda _: None,
        )
    assert (
        not (tmp_path / "validated").exists() and not (tmp_path / "processed").exists()
    )


def test_later_edition_failure_does_not_publish_partial_history(tmp_path, monkeypatch):
    inventory, reference = fixture_inventory(tmp_path, monkeypatch)

    def broken(url):
        return (archive() if "/2026provisional/" in url else b"truncated"), dict(
            retrieved_at="2026-11-21T16:00:00+00:00"
        )

    with pytest.raises(ashe.IngestionError):
        ashe.ingest(
            tmp_path,
            "bad",
            inventory=inventory,
            reference=reference,
            downloader=broken,
            sleep=lambda _: None,
        )
    assert (
        not (tmp_path / "validated").exists() and not (tmp_path / "processed").exists()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("edition_id", "2026wrong"),
        ("status", "revised"),
        ("publication_date", "2025-10-22"),
    ],
)
def test_inventory_attribution_failures(tmp_path, field, value):
    record = entry()
    record[field] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(dict(editions=[record])))
    with pytest.raises(ashe.IngestionError):
        ashe.load_inventory(path)


class Response:
    status = 200
    url = entry()["url"]
    headers = {"Content-Length": "3", "Set-Cookie": "SYNTHETIC_SESSION_ONLY"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, limit):
        return b"zip"


@pytest.mark.parametrize(
    "retry", ["10", format_datetime(datetime.now(timezone.utc) + timedelta(seconds=10))]
)
def test_rate_limit_seconds_and_http_date(retry):
    waits = []
    attempts = []

    def opener(request, timeout):
        attempts.append(request)
        if len(attempts) == 1:
            raise HTTPError(
                request.full_url,
                429,
                "rate limit",
                {"Retry-After": retry, "Set-Cookie": "SYNTHETIC_SESSION_ONLY"},
                None,
            )
        return Response()

    body, metadata = ashe.fetch(entry()["url"], sleep=waits.append, opener=opener)
    assert body == b"zip" and 0 <= waits[0] <= 10
    assert metadata["prior_attempts"][0]["status"] == 429
    assert "SYNTHETIC_SESSION_ONLY" not in json.dumps(metadata)
    assert "ASHE-Ingestion" in attempts[0].get_header("User-agent")


@pytest.mark.parametrize("status,retry", [(403, None), (429, "120"), (429, "invalid")])
def test_access_restrictions_stop_without_early_retry(status, retry):
    calls = []

    def opener(request, timeout):
        calls.append(request)
        raise HTTPError(
            request.full_url,
            status,
            "stop",
            {"Retry-After": retry} if retry else {},
            None,
        )

    with pytest.raises(ashe.IngestionError):
        ashe.fetch(
            entry()["url"], opener=opener, sleep=lambda _: pytest.fail("must stop")
        )
    assert len(calls) == 1


def test_exhausted_retries_and_incomplete_response():
    waits = []

    def opener(request, timeout):
        raise HTTPError(request.full_url, 503, "unavailable", {}, None)

    with pytest.raises(ashe.IngestionError, match="three attempts"):
        ashe.fetch(entry()["url"], opener=opener, sleep=waits.append)
    assert waits == [1, 2]
    response = Response()
    response.headers = {"Content-Length": "9"}
    with pytest.raises(ashe.IngestionError, match="incomplete"):
        ashe.fetch(entry()["url"], opener=lambda *args, **kwargs: response)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.ons.gov.uk/file?uri=" + ashe.SOURCE_PATH + "2026/x.zip",
        "https://example.com/file?uri=" + ashe.SOURCE_PATH + "2026/x.zip",
        "https://www.ons.gov.uk/file?uri=/unrelated/x.zip",
    ],
)
def test_official_source_only(url):
    with pytest.raises(ashe.IngestionError):
        ashe.source_url(url)


def test_verified_cache_import_and_tamper_detection(tmp_path):
    url = entry()["url"]
    cache = tmp_path / "cache"
    from ingestion.boe import publish, sha

    publish(
        cache / "one",
        {"response.bin": b"zip"},
        dict(
            identity={"url": url},
            status=200,
            retrieved_at="2026-11-21T16:00:00+00:00",
            source_sha256=sha(b"zip"),
        ),
    )
    body, meta = ashe.cached_source(cache, url)
    assert body == b"zip" and meta["acquisition"] == "verified_local_official_response"
    (cache / "one/response.bin").write_bytes(b"changed")
    with pytest.raises(ashe.IngestionError):
        ashe.cached_source(cache, url)
