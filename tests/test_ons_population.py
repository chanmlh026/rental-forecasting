"""Native ONS population/source precision, schema and immutable offline recovery."""

import io
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

import openpyxl
import pandas as pd
import pytest
from openpyxl.styles import Font, PatternFill

from ingestion import ons_population as pop
from ingestion import source_io
from ingestion.boe import publish

STAMP = "2026-11-22T09:35:31+00:00"


def fixture_workbook(kind="summary", code="E08000016", marker=None):
    book = openpyxl.Workbook()
    book.remove(book.active)
    cover = book.create_sheet("Cover sheet")
    cover.append(["ONS population estimates"])
    cover.append(["Date published: 1 July 2013"])
    notes = book.create_sheet("Notes")
    notes.append(
        [
            "Population is usually resident at 30 June; flows are twelve months to mid-year."
        ]
    )
    tables = []
    if kind == "summary":
        definitions = [
            (
                "MYE3",
                [
                    "Code",
                    "Name",
                    "Geography",
                    "Internal Migration Inflow",
                    "Internal Migration Outflow",
                    "Internal Migration Net",
                    "International Migration Inflow",
                    "International Migration Outflow",
                    "International Migration Net",
                ],
                [10, 20, -10, 30, 40, -10],
            ),
            ("MYE4", ["Code", "Name", "Geography", "Mid-2012", "Mid-2011"], [100, 99]),
            (
                "MYE5",
                [
                    "Code",
                    "Name",
                    "Geography",
                    "Area (sq km)",
                    "2012 people per sq. km",
                    "2011 people per sq. km",
                ],
                [1.2345, 81, 80],
            ),
        ]
    else:
        definitions = [
            (
                "MYEB3",
                [
                    "ladcode23",
                    "laname23",
                    "country",
                    "population_2011",
                    "population_2012",
                    "internal_in_2012",
                    "internal_out_2012",
                    "internal_net_2012",
                    "international_in_2012",
                    "international_out_2012",
                    "international_net_2012",
                ],
                [99, 100, 10, 20, -10, 30, 40, -10],
            )
        ]
    for name, headers, values in definitions:
        sheet = book.create_sheet(name)
        title = name + ": native source table for mid-2012"
        hr = 8 if kind == "summary" else 2
        sheet.cell(1, 1, title)
        for c, h in enumerate(headers, 1):
            sheet.cell(hr, c, h)
        for rn, (gid, gn) in enumerate(
            [("E06000001", "Hartlepool"), (code, "Barnsley")], hr + 1
        ):
            for cn, v in enumerate(
                [gid, gn, "Unitary Authority" if kind == "summary" else "E"] + values, 1
            ):
                sheet.cell(rn, cn, v)
        sheet.cell(hr + 1, 4).font = Font(color="FF0000", bold=True)
        sheet.cell(hr + 1, 4).fill = PatternFill("solid", fgColor="FFFF00")
        sheet.cell(hr + 1, 4).number_format = "0.0000"
        if marker is not None:
            sheet.cell(hr + 1, 4, marker)
        sheet.cell(hr + 4, 1, "Source footnote retained verbatim")
        tables.append(
            dict(sheet=name, title=title, header_row=hr, column_labels=headers)
        )
    stream = io.BytesIO()
    book.save(stream)
    book.close()
    body = stream.getvalue()
    edition = dict(
        edition_id="fixture",
        kind=kind,
        url="https://www.ons.gov.uk/file?"
        + urlencode({"uri": pop.SOURCE_PATH + "/mid2012fixture/fixture.xlsx"}),
        edition_slug="mid2012fixture",
        latest_reference_year=2012,
        source_sha256=pop.sha(body),
        tables=tables,
    )
    return body, edition


def provenance(edition):
    return dict(
        identity=dict(url=edition["url"], snapshot_id="one"),
        source_sha256=edition["source_sha256"],
        retrieval=dict(retrieved_at=STAMP),
    )


def cohort():
    return {"E06000001": "Hartlepool", "E08000038": "Barnsley"}


@pytest.mark.parametrize("kind", ["summary", "detail"])
def test_published_fields_periods_original_geography_and_notes(kind):
    body, e = fixture_workbook(kind)
    rows, notes, schema = pop.parse_workbook(body, e, provenance(e), cohort())
    frame = pd.DataFrame(rows)
    assert set(frame.source_code) == {"E06000001", "E08000016"}
    assert frame.loc[frame.measure == "internal_net", "value"].eq(-10).all()
    assert frame.loc[frame.measure == "international_net", "value"].eq(-10).all()
    flow = frame[frame.measure == "internal_inflow"].iloc[0]
    assert (flow.period_start, flow.period_end, flow.unit) == (
        "2011-07-01",
        "2012-06-30",
        "persons",
    )
    assert any("footnote retained" in n["text"] for n in notes)
    styled = frame[(frame.source_code == "E06000001") & (frame.source_column == 4)]
    assert (
        styled.source_style_id.gt(0).all() and styled.source_style_json.ne("[]").all()
    )
    coverage, geo = pop.derive_audits(frame, cohort())
    assert coverage.exact_cohort_matches.eq(1).all()
    assert (
        geo[geo.source_code == "E08000016"]
        .relationship.eq("same_name_different_code")
        .all()
    )
    assert not geo.mapping_applied.any()
    if kind == "summary":
        area = frame[frame.measure == "land_area"]
        assert len(area) == 2 and area.reference_year.isna().all()
        assert (
            area.source_value_text.eq("1.2345").all()
            and area.unit.eq("square_kilometres").all()
        )
        assert len(frame[frame.measure == "published_density"]) == 4


@pytest.mark.parametrize("marker", ["..", "x", "#N/A"])
def test_source_markers_and_errors_preserved(marker):
    body, e = fixture_workbook(marker=marker)
    rows, _, _ = pop.parse_workbook(body, e, provenance(e), cohort())
    first = next(
        r
        for r in rows
        if r["source_sheet"] == "MYE4"
        and r["source_code"] == "E06000001"
        and r["reference_year"] == 2012
    )
    assert (
        first["value"] is None
        and first["source_value_text"] == marker
        and first["value_kind"] == "source_marker"
    )


def test_formula_without_cache_is_preserved_without_inventing_value():
    body, e = fixture_workbook(marker="=1+1")
    rows, _, _ = pop.parse_workbook(body, e, provenance(e), cohort())
    first = next(r for r in rows if r["source_formula"])
    assert (
        first["source_formula"] == "1+1"
        and first["value"] is None
        and first["value_kind"] == "formula_without_cached_value"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "header",
        "title",
        "unit",
        "year",
        "missing_sheet",
        "duplicate_code",
        "invalid_code",
    ],
)
def test_schema_duplicate_units_and_period_errors_are_terminal(mutation):
    body, e = fixture_workbook()
    book = openpyxl.load_workbook(io.BytesIO(body))
    hr = 8
    if mutation == "header":
        book["MYE3"].cell(hr, 4, "Count of households")
    if mutation == "title":
        book["MYE3"].cell(1, 1, "Wrong source table")
    if mutation == "unit":
        book["MYE5"].cell(hr, 4, "Area (square miles)")
        e["tables"][2]["column_labels"][3] = "Area (square miles)"
    if mutation == "year":
        book["MYE4"].cell(hr, 5, "Mid-2010")
        e["tables"][1]["column_labels"][4] = "Mid-2010"
    if mutation == "missing_sheet":
        book.remove(book["MYE4"])
    if mutation == "duplicate_code":
        book["MYE3"].cell(hr + 2, 1, "E06000001")
    if mutation == "invalid_code":
        book["MYE3"].cell(hr + 2, 1, "E0600001")
    stream = io.BytesIO()
    book.save(stream)
    book.close()
    with pytest.raises(pop.IngestionError):
        pop.parse_workbook(stream.getvalue(), e, provenance(e), cohort())


def hashes(root):
    return {
        str(p.relative_to(root)): pop.sha(p.read_bytes())
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def fixture_ingestion(tmp_path, monkeypatch):
    body, e = fixture_workbook()
    docs = b"<html>Office for National Statistics - Open Government Licence v3.0</html>"
    inventory = tmp_path / "inventory.json"
    reference = tmp_path / "reference.csv"
    reference.write_text("reference")
    contract = dict(
        source_catalogue=pop.CATALOGUE,
        editions=[e],
        documents={
            "licence": {
                "url": "https://www.ons.gov.uk/help/terms-conditions",
                "source_sha256": pop.sha(docs),
            }
        },
    )
    inventory.write_text(json.dumps(contract), encoding="utf-8")
    monkeypatch.setattr(
        pop,
        "load_geography_reference",
        lambda _: SimpleNamespace(eligible_names=cohort()),
    )

    def get(url):
        return (body if "/file?" in url else docs), dict(
            status=200,
            url=url,
            resolved_url=url,
            retrieved_at=STAMP,
            response_headers={
                "ETag": "safe",
                "Set-Cookie": "SYNTHETIC_ONLY",
                "Authorization": "SYNTHETIC_ONLY",
            },
        )

    return (
        dict(inventory=inventory, reference=reference, sleep=lambda _: None),
        get,
        body,
    )


def test_offline_publication_idempotency_and_original_output_preservation(
    tmp_path, fixture_ingestion
):
    kwargs, get, _ = fixture_ingestion
    root = tmp_path / "data"
    result = pop.ingest(root, "one", downloader=get, **kwargs)
    saved = hashes(root)
    again = pop.ingest(root, "one", **kwargs)
    assert result == again and saved == hashes(root)
    frame = pd.read_parquet(Path(result["processed_path"]) / "observations.parquet")
    assert len(frame) == 22 and not result["exact_point_in_time"]
    for p in root.rglob("manifest.json"):
        assert "SYNTHETIC_ONLY" not in p.read_text()
    pop.ingest(root, "two", downloader=get, **kwargs)
    assert all(hashes(root)[p] == v for p, v in saved.items())


def test_offline_missing_source_stops_without_network_or_outputs(
    tmp_path, fixture_ingestion
):
    kwargs, _, _ = fixture_ingestion
    with pytest.raises(pop.IngestionError, match="Offline"):
        pop.ingest(tmp_path / "data", "one", **kwargs)
    assert not (tmp_path / "data/processed").exists()


def test_interrupted_acquisition_reuses_completed_raw(tmp_path, fixture_ingestion):
    kwargs, get, _ = fixture_ingestion
    root = tmp_path / "data"

    def fail(url):
        if "/file?" in url:
            raise OSError("interrupted")
        return get(url)

    with pytest.raises(OSError):
        pop.ingest(root, "one", downloader=fail, **kwargs)
    before = hashes(root)
    calls = []

    def resume(url):
        calls.append(url)
        return get(url)

    pop.ingest(root, "one", downloader=resume, **kwargs)
    assert len(calls) == 1 and all(hashes(root)[p] == v for p, v in before.items())


def test_interrupted_output_publication_recovers_offline(
    tmp_path, fixture_ingestion, monkeypatch
):
    kwargs, get, _ = fixture_ingestion
    root = tmp_path / "data"
    original = source_io.publish

    def fail(directory, files, info):
        if "processed" in directory.parts:
            raise OSError("output interrupted")
        return original(directory, files, info)

    monkeypatch.setattr(source_io, "publish", fail)
    with pytest.raises(OSError):
        pop.ingest(root, "one", downloader=get, **kwargs)
    before = hashes(root)
    monkeypatch.setattr(source_io, "publish", original)
    pop.ingest(root, "one", **kwargs)
    assert all(hashes(root)[p] == v for p, v in before.items())


def test_changed_workbook_or_reference_cannot_overwrite_outputs(
    tmp_path, fixture_ingestion
):
    kwargs, get, _ = fixture_ingestion
    root = tmp_path / "data"
    pop.ingest(root, "one", downloader=get, **kwargs)
    saved = hashes(root)
    kwargs["reference"].write_text("changed")
    with pytest.raises(pop.IngestionError, match="conflict"):
        pop.ingest(root, "one", **kwargs)
    assert hashes(root) == saved


def test_investigated_workbook_hash_and_corruption_gates(tmp_path, fixture_ingestion):
    kwargs, get, _ = fixture_ingestion
    root = tmp_path / "data"

    def changed(url):
        body, meta = get(url)
        return (body + b"changed" if "/file?" in url else body), meta

    with pytest.raises(pop.IngestionError, match="checksum changed"):
        pop.ingest(root, "one", downloader=changed, **kwargs)
    assert not (root / "validated").exists()


def test_inventory_rejects_duplicates_and_unofficial_sources(
    tmp_path, fixture_ingestion
):
    kwargs, _, _ = fixture_ingestion
    p = kwargs["inventory"]
    data = json.loads(p.read_text())
    data["editions"].append(data["editions"][0])
    p.write_text(json.dumps(data))
    with pytest.raises(pop.IngestionError):
        pop.load_inventory(p)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.ons.gov.uk/file?uri=x.xlsx",
        "https://evil.test/file?uri=x.xlsx",
        "https://www.ons.gov.uk/file?uri=/other/source.xlsx",
        "https://www.ons.gov.uk/file?uri=" + pop.SOURCE_PATH + "/../x.xlsx",
        "https://user:password@www.ons.gov.uk/help/terms-conditions",
    ],
)
def test_only_official_approved_source_paths(url):
    with pytest.raises(pop.IngestionError):
        pop.source_url(url)


class Response:
    status = 200

    def __init__(self, url, headers=None, body=b"source"):
        self.url = url
        self.headers = headers or {}
        self.body = body

    def read(self, n):
        return self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_missing_contact_is_terminal_before_network():
    def never(*a, **k):
        pytest.fail("Network attempted before approved contact")

    with pytest.raises(pop.IngestionError, match="contact"):
        pop.fetch(pop.CATALOGUE, opener=never)


def test_fetch_bounded_retry_safe_headers_and_tls_default():
    attempts = []
    waits = []

    def opener(request, timeout):
        attempts.append(request)
        if len(attempts) == 1:
            raise HTTPError(
                pop.CATALOGUE,
                429,
                "limited",
                {"Retry-After": "2", "Set-Cookie": "SYNTHETIC_ONLY"},
                None,
            )
        return Response(
            pop.CATALOGUE,
            {"ETag": "safe", "Set-Cookie": "SYNTHETIC_ONLY", "Content-Length": "6"},
        )

    body, meta = pop.fetch(
        pop.CATALOGUE,
        contact_url="https://project.example.org/about",
        opener=opener,
        sleep=waits.append,
    )
    assert (
        body == b"source"
        and waits == [2]
        and meta["response_headers"] == {"ETag": "safe", "Content-Length": "6"}
    )
    assert "SYNTHETIC_ONLY" not in json.dumps(meta)


@pytest.mark.parametrize(
    "kind", ["403", "long_wait", "truncated", "redirect", "empty", "transport"]
)
def test_terminal_and_interrupted_http_responses(kind):
    attempts = []

    def opener(*args, **kwargs):
        attempts.append(1)
        if kind == "403":
            raise HTTPError(pop.CATALOGUE, 403, "denied", {}, None)
        if kind == "long_wait":
            raise HTTPError(pop.CATALOGUE, 429, "limited", {"Retry-After": "120"}, None)
        if kind == "transport":
            raise URLError("interrupted")
        return Response(
            "https://evil.test/data" if kind == "redirect" else pop.CATALOGUE,
            {"Content-Length": "10"} if kind == "truncated" else {},
            b"" if kind == "empty" else b"source",
        )

    with pytest.raises(pop.IngestionError):
        pop.fetch(
            pop.CATALOGUE,
            contact_url="https://project.example.org/about",
            opener=opener,
            sleep=lambda _: None,
        )
    assert len(attempts) == (3 if kind == "transport" else 1)


@pytest.mark.parametrize("raw", [None, "0.10000000000000001"])
def test_exact_xml_precision_and_missing_cells(raw):
    import zipfile

    body, e = fixture_workbook()
    book = openpyxl.load_workbook(io.BytesIO(body))
    sheet = book["MYE4"]
    sheet.cell(9, 4).value = None if raw is None else 0.1
    stream = io.BytesIO()
    book.save(stream)
    book.close()
    body = stream.getvalue()
    if raw:
        source = zipfile.ZipFile(io.BytesIO(body))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as target:
            for name in source.namelist():
                payload = source.read(name)
                if name.startswith("xl/worksheets/"):
                    payload = payload.replace(
                        b"<v>0.1</v>", b"<v>0.10000000000000001</v>"
                    )
                target.writestr(name, payload)
        source.close()
        body = out.getvalue()
    rows, _, _ = pop.parse_workbook(body, e, provenance(e), cohort())
    row = next(
        r
        for r in rows
        if r["source_sheet"] == "MYE4"
        and r["source_code"] == "E06000001"
        and r["reference_year"] == 2012
    )
    assert row["source_value_text"] == (raw or "")
    assert row["value"] == (float(raw) if raw else None)
    assert row["value_kind"] == ("numeric" if raw else "missing")


def test_negative_population_is_flagged_and_retained():
    body, e = fixture_workbook(marker=-1)
    rows, _, _ = pop.parse_workbook(body, e, provenance(e), cohort())
    row = next(
        r
        for r in rows
        if r["source_sheet"] == "MYE4"
        and r["source_code"] == "E06000001"
        and r["reference_year"] == 2012
    )
    assert row["value"] == -1 and "negative_non_net_source_value" in row["flags_json"]


def test_corrupted_completed_raw_or_output_fails_closed(tmp_path, fixture_ingestion):
    kwargs, get, _ = fixture_ingestion
    root = tmp_path / "data"
    result = pop.ingest(root, "one", downloader=get, **kwargs)
    output = Path(result["processed_path"]) / "observations.parquet"
    output.write_bytes(b"corrupt")
    with pytest.raises(pop.IngestionError):
        pop.ingest(root, "one", **kwargs)
    assert output.read_bytes() == b"corrupt"


def test_verified_historical_migration_header_capitalisation_is_preserved():
    body, e = fixture_workbook()
    book = openpyxl.load_workbook(io.BytesIO(body))
    sheet = book["MYE3"]
    sheet.cell(8, 9, "International migration Net")
    e["tables"][0]["column_labels"][8] = "International migration Net"
    stream = io.BytesIO()
    book.save(stream)
    book.close()
    rows, _, _ = pop.parse_workbook(stream.getvalue(), e, provenance(e), cohort())
    values = [
        r
        for r in rows
        if r["source_sheet"] == "MYE3" and r["measure"] == "international_net"
    ]
    assert len(values) == 2 and all(
        r["source_header"] == "International migration Net" and r["value"] == -10
        for r in values
    )
