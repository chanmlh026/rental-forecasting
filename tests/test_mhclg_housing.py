"""MHCLG native ODS quality, geography, periods and immutable recovery tests."""

import io
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET

import pandas as pd
import pytest
from ingestion import mhclg_housing as h
from ingestion import source_io

STAMP = "2026-11-22T10:29:47+00:00"


def q(ns, name):
    return "{" + h.NS[ns] + "}" + name


def put(row, value, style=None, repeat=None):
    attrs = {}
    if style:
        attrs[q("t", "style-name")] = style
    if repeat:
        attrs[q("t", "number-columns-repeated")] = str(repeat)
    if isinstance(value, (int, float)):
        attrs.update({q("o", "value-type"): "float", q("o", "value"): str(value)})
    elif value is not None:
        attrs[q("o", "value-type")] = "string"
    cell = ET.SubElement(row, q("t", "table-cell"), attrs)
    if value is not None:
        ET.SubElement(cell, q("x", "p")).text = str(value)
    return cell


def ods_fixture(number, mutation=None):
    root = ET.Element(q("o", "document-content"))
    automatic = ET.SubElement(root, q("o", "automatic-styles"))
    styles = ET.Element(q("o", "document-styles"))
    named = ET.SubElement(styles, q("o", "styles"))
    for name, parent, bg in [
        ("Default", None, "#FFFFFF"),
        ("RedBase", "Default", "#FF0000"),
        ("InheritedRed", "RedBase", None),
    ]:
        node = ET.SubElement(
            named,
            q("s", "style"),
            {
                q("s", "name"): name,
                q("s", "family"): "table-cell",
                **({q("s", "parent-style-name"): parent} if parent else {}),
            },
        )
        if bg:
            ET.SubElement(
                node, q("s", "table-cell-properties"), {q("f", "background-color"): bg}
            )
    body = ET.SubElement(root, q("o", "body"))
    spreadsheet = ET.SubElement(body, q("o", "spreadsheet"))

    def table(name, rows):
        t = ET.SubElement(spreadsheet, q("t", "table"), {q("t", "name"): name})
        for values in rows:
            row = ET.SubElement(t, q("t", "table-row"))
            for value in values:
                put(row, value)
        return t

    table(
        "Cover",
        [
            [f"Table {number}: official MHCLG housing"],
            ["Published date"],
            ["20 November 2025"],
        ],
    )
    table(
        "Notes",
        [
            ["[note 1]", "Figures for this authority for this year have been imputed."],
            ["[p]", "The 2023-24 figures are provisional."],
            ["[r]", "Revised figures"],
            ["[x]", "Data unavailable"],
            [
                "[note 2]",
                "Census reconciliation adjustment; stock changes need not equal flows.",
            ],
        ],
    )
    if number == "122":
        definitions = [
            (
                "LT_122",
                [
                    "DCLG code",
                    "Former ONS code",
                    "Current ONS code",
                    "Authority data",
                    "2001-02",
                    "2002-03 [r]",
                ],
                [-2, "[x]"],
            )
        ]
    elif number == "123":
        definitions = [
            (
                "2012-13",
                [
                    "DCLG code",
                    "Former ONS code",
                    "Current ONS code",
                    "Authority Data",
                    "New build",
                    "Net conversions",
                    "Demolitions",
                    "Adjustment to Census 2021",
                    "Net Additions",
                ],
                [10, -3, 2, 1, 6],
            ),
            (
                "2024-25",
                [
                    "DCLG code",
                    "Former ONS code",
                    "Current ONS code",
                    "Authority data",
                    "New build",
                    "Of which under PDR: total (new build)",
                    "Net additions",
                ],
                [20, 2, 18],
            ),
        ]
    else:
        definitions = [
            (
                "LT_125_rounded",
                ["Old ONS code", "New ONS code", "Area", "2001", "2025 [p]", "Notes"],
                [1000, 2000, "[note 2]"],
            ),
            (
                "LT_125_unrounded",
                ["Old ONS code", "New ONS code", "Area", "2001", "2025 [p]", "Notes"],
                [1037, 2089, "[note 2]"],
            ),
        ]
    contracts = []
    for sn, headers, values in definitions:
        title = f"Table {number} source: " + sn + (" [p]" if sn == "2024-25" else "")
        preamble = (
            "Cells filled in red are imputed figures."
            if number == "123"
            else (
                "District totals are expressed to the nearest ten"
                if number == "125"
                else "Published source values"
            )
        )
        t = table(sn, [[title], [preamble], headers])
        hr = 3
        identities = [
            ("E06000001", "Hartlepool"),
            ("E08000016", "Barnsley [note 1]" if number == "123" else "Barnsley"),
            ("", "Historic district"),
            ("E92000001", "England"),
            ("", "Published group total"),
        ]
        for i, (code, name) in enumerate(identities):
            identity = (
                ["12AB", code, name]
                if number == "125"
                else ["F001", "12AB", code, name]
            )
            if i == 4:
                identity = ["", code, name] if number == "125" else ["", "", code, name]
            row = ET.SubElement(t, q("t", "table-row"))
            cells = [put(row, v) for v in identity + values]
            if i == 0:
                cells[len(identity)].set(q("t", "style-name"), "InheritedRed")
        tail = ET.SubElement(
            t,
            q("t", "table-row"),
            {
                q("t", "number-rows-repeated"): "1000000",
                q("t", "default-cell-style-name"): "Default",
            },
        )
        put(tail, None, repeat=16384)
        contracts.append(
            dict(
                sheet=sn,
                title=title,
                header_row=hr,
                column_labels={str(i + 1): v for i, v in enumerate(headers)},
            )
        )
    if mutation:
        mutation(root, styles, contracts)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
        archive.writestr("content.xml", ET.tostring(root))
        archive.writestr("styles.xml", ET.tostring(styles))
    data = stream.getvalue()
    filename = "LiveTable125" if number == "125" else "Live_Table_" + number
    source = dict(
        edition_id="table" + number,
        table_id=number,
        url=f"https://assets.publishing.service.gov.uk/media/fixture{number}/{filename}.ods",
        source_sha256=h.sha(data),
        tables=contracts,
    )
    return data, source


def cohort():
    return {"E06000001": "Hartlepool", "E08000038": "Barnsley"}


def provenance(source):
    return dict(
        identity=dict(url=source["url"], snapshot_id="one"),
        source_sha256=source["source_sha256"],
        retrieval=dict(retrieved_at=STAMP),
    )


@pytest.mark.parametrize("number", ["122", "123", "125"])
def test_original_geography_periods_values_and_styles(number):
    data, s = ods_fixture(number)
    rows, notes, styles, schema = h.parse_source(data, s, provenance(s), cohort())
    f = pd.DataFrame(rows)
    assert set(f.source_code) == {"E06000001", "E08000016", "E92000001", ""}
    assert (
        "12AB" in set(f.former_ons_code)
        and f[f.source_name == "Published group total"].source_code.eq("").all()
    )
    assert styles and any("Census" in n["text"] for n in notes)
    assert (
        f[f.source_name == "Hartlepool"]
        .effective_style_properties_json.str.contains("#FF0000")
        .any()
    )
    if number == "122":
        assert (
            f.value.min() == -2
            and f[f.period == "2001-2002"].period_start.eq("2001-04-01").all()
        )
        assert f[f.period == "2002-2003"].value_kind.eq("source_marker").all()
        assert f.publisher_imputation_flag.isna().all()
    elif number == "123":
        new = f[f.measure == "new_build_completions"]
        assert set(new.reference_year) == {2013, 2025}
        assert new[new.source_name == "Hartlepool"].publisher_imputation_flag.all()
        assert new[
            new.source_name.str.startswith("Barnsley")
        ].publisher_imputation_row_note.all()
        assert f[f.source_name == "England"].publisher_imputation_flag.isna().all()
        assert (
            f[f.source_sheet == "2024-25"]
            .flags_json.str.contains("publisher_provisional_note_year_differs")
            .all()
        )
        assert "census_2021_adjustment" in set(f.measure)
    else:
        assert f[f.measure == "dwelling_stock_unrounded"].value.max() == 2089
        assert f[f.reference_year == 2025].reference_date.eq("2025-03-31").all()
        assert f[
            f.measure == "dwelling_stock_unrounded"
        ].future_denominator_candidate.all()
        assert (
            f[f.measure == "dwelling_stock_rounded"]
            .future_denominator_candidate.eq(False)
            .all()
        )
        assert (
            f[f.measure == "dwelling_stock_unrounded"]
            .flags_json.str.contains("rounding|rounded_wording")
            .all()
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "header",
        "title",
        "duplicate",
        "bad_code",
        "bad_type",
        "infinite",
        "no_new_build",
    ],
)
def test_invalid_source_schema_or_identity_stops(mutation):
    def change(root, styles, contracts):
        t = next(
            t
            for t in root.findall(".//t:table", h.NS)
            if h.attr(t, "t", "name") == "2012-13"
        )
        rows = t.findall("t:table-row", h.NS)
        if mutation == "header":
            rows[2][4].find("x:p", h.NS).text = "Different field"
        if mutation == "title":
            rows[0][0].find("x:p", h.NS).text = "Wrong title"
        if mutation == "duplicate":
            rows[4][2].find("x:p", h.NS).text = "E06000001"
        if mutation == "bad_code":
            rows[3][2].find("x:p", h.NS).text = "E0600001"
        if mutation == "bad_type":
            rows[3][4].set(q("o", "value-type"), "percentage")
        if mutation == "infinite":
            rows[3][4].set(q("o", "value"), "NaN")
        if mutation == "no_new_build":
            rows[2][4].find("x:p", h.NS).text = "Demolitions"
            contracts[0]["column_labels"]["5"] = "Demolitions"

    data, s = ods_fixture("123", change)
    with pytest.raises(h.IngestionError):
        h.parse_source(data, s, provenance(s), cohort())


@pytest.mark.parametrize("label", ["2024-24", "2024-26", "2024 Q1", "2024-2025"])
def test_invalid_financial_year(label):
    with pytest.raises(h.IngestionError):
        h.financial_year(label)


def test_ods_repeated_spacing_and_large_empty_ranges():
    p = ET.Element(q("x", "p"))
    p.text = "New"
    space = ET.SubElement(p, q("x", "s"), {q("x", "c"): "2"})
    space.tail = "build"
    assert h.ods_text(p) == "New  build"
    data, s = ods_fixture("122")
    content, _ = h.ods_document(data)
    t = next(
        t
        for t in content.findall(".//t:table", h.NS)
        if h.attr(t, "t", "name") == "LT_122"
    )
    assert (
        len(list(h.sparse_rows(t))) == 8 and len(list(h.sparse_rows(t, width=6))) == 8
    )


def hashes(root):
    return {
        str(p.relative_to(root)): h.sha(p.read_bytes())
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def fixture_ingestion(tmp_path, monkeypatch):
    bodies = {}
    sources = []
    for number in ("122", "123", "125"):
        data, s = ods_fixture(number)
        bodies[s["url"]] = data
        sources.append(s)
    doc = b"<html>Open Government Licence v3.0 - Crown copyright</html>"
    bodies[h.PAGES["terms"]] = doc
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            dict(
                sources=sources,
                aliases=[],
                documents={
                    "terms": dict(url=h.PAGES["terms"], source_sha256=h.sha(doc))
                },
            )
        ),
        encoding="utf-8",
    )
    reference = tmp_path / "reference.csv"
    reference.write_text("reference")
    monkeypatch.setattr(
        h,
        "load_geography_reference",
        lambda _: SimpleNamespace(eligible_names=cohort()),
    )
    monkeypatch.setattr(h.time, "sleep", lambda _: None)

    def get(url):
        return bodies[url], dict(
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

    return dict(inventory=inventory, reference=reference), get


def test_immutable_rerun_without_network_and_prior_snapshot_preserved(
    tmp_path, fixture_ingestion
):
    kwargs, get = fixture_ingestion
    root = tmp_path / "data"
    info = h.ingest(root, "one", downloader=get, **kwargs)
    before = hashes(root)

    def never(_):
        pytest.fail("Unexpected acquisition")

    assert (
        h.ingest(root, "one", downloader=never, **kwargs) == info
        and hashes(root) == before
    )
    assert not info["exact_point_in_time"] and info[
        "stock_denominator_timing"
    ].startswith("Unselected")
    for p in root.rglob("manifest.json"):
        assert "SYNTHETIC_ONLY" not in p.read_text()
    h.ingest(root, "two", downloader=get, **kwargs)
    assert all(hashes(root)[p] == v for p, v in before.items())


def test_interruption_resumes_only_missing_acquisition(tmp_path, fixture_ingestion):
    kwargs, get = fixture_ingestion
    root = tmp_path / "data"

    def fail(url):
        if "Live_Table_123" in url:
            raise OSError("interrupted")
        return get(url)

    with pytest.raises(OSError):
        h.ingest(root, "one", downloader=fail, **kwargs)
    before = hashes(root)
    calls = []

    def resume(url):
        calls.append(url)
        return get(url)

    h.ingest(root, "one", downloader=resume, **kwargs)
    assert len(calls) == 2 and all(hashes(root)[p] == v for p, v in before.items())


def test_partial_output_publication_recovers_without_redownload(
    tmp_path, fixture_ingestion, monkeypatch
):
    kwargs, get = fixture_ingestion
    root = tmp_path / "data"
    original = source_io.publish

    def fail(directory, files, info):
        if "processed" in directory.parts:
            raise OSError("publication interrupted")
        return original(directory, files, info)

    monkeypatch.setattr(source_io, "publish", fail)
    with pytest.raises(OSError):
        h.ingest(root, "one", downloader=get, **kwargs)
    before = hashes(root)
    monkeypatch.setattr(source_io, "publish", original)
    h.ingest(root, "one", downloader=lambda _: pytest.fail("Network"), **kwargs)
    assert all(hashes(root)[p] == v for p, v in before.items())


def test_corrupt_or_changed_completed_snapshot_fails_closed(
    tmp_path, fixture_ingestion
):
    kwargs, get = fixture_ingestion
    root = tmp_path / "data"
    info = h.ingest(root, "one", downloader=get, **kwargs)
    p = Path(info["processed_path"]) / "observations.parquet"
    p.write_bytes(b"corrupt")
    with pytest.raises(h.IngestionError):
        h.ingest(root, "one", downloader=get, **kwargs)
    assert p.read_bytes() == b"corrupt"


def test_reference_or_inventory_change_cannot_overwrite(tmp_path, fixture_ingestion):
    kwargs, get = fixture_ingestion
    root = tmp_path / "data"
    h.ingest(root, "one", downloader=get, **kwargs)
    before = hashes(root)
    kwargs["reference"].write_text("changed")
    with pytest.raises(h.IngestionError, match="conflict"):
        h.ingest(root, "one", downloader=get, **kwargs)
    assert hashes(root) == before


def test_changed_workbook_cannot_silently_replace_inspected_source(
    tmp_path, fixture_ingestion
):
    kwargs, get = fixture_ingestion

    def changed(url):
        body, meta = get(url)
        return (body + b"changed" if url.endswith(".ods") else body), meta

    with pytest.raises(h.IngestionError, match="workbook changed"):
        h.ingest(tmp_path / "data", "one", downloader=changed, **kwargs)
    assert not (tmp_path / "data/validated").exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://www.gov.uk/robots.txt",
        "https://evil.test/Live_Table_122.ods",
        "https://www.ons.gov.uk/file",
        "https://user:password@www.gov.uk/robots.txt",
        h.PAGES["terms"] + "?token=secret",
        "https://assets.publishing.service.gov.uk/media/id/Other.ods",
    ],
)
def test_only_approved_official_source_urls(url):
    with pytest.raises(h.IngestionError):
        h.source_url(url)


class Response:
    status = 200

    def __init__(self, url, body=b"source", headers=None):
        self.url = url
        self.body = body
        self.headers = headers or {}

    def read(self, n):
        return self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_fetch_retry_after_and_safe_headers():
    calls = []
    waits = []

    def opener(request, timeout):
        calls.append(request)
        if len(calls) == 1:
            raise HTTPError(
                h.PAGES["terms"],
                429,
                "limited",
                {"Retry-After": "2", "Set-Cookie": "SYNTHETIC_ONLY"},
                None,
            )
        return Response(
            h.PAGES["terms"],
            headers={
                "ETag": "safe",
                "Content-Length": "6",
                "Set-Cookie": "SYNTHETIC_ONLY",
            },
        )

    body, meta = h.fetch(h.PAGES["terms"], opener=opener, sleep=waits.append)
    assert (
        body == b"source"
        and waits == [2]
        and meta["response_headers"] == {"ETag": "safe", "Content-Length": "6"}
    )
    assert "SYNTHETIC_ONLY" not in json.dumps(meta)


@pytest.mark.parametrize(
    "kind", ["403", "long_wait", "truncated", "redirect", "empty", "transport"]
)
def test_terminal_and_transport_failures(kind):
    calls = []

    def opener(*a, **k):
        calls.append(1)
        if kind == "403":
            raise HTTPError(h.PAGES["terms"], 403, "denied", {}, None)
        if kind == "long_wait":
            raise HTTPError(
                h.PAGES["terms"], 429, "limited", {"Retry-After": "120"}, None
            )
        if kind == "transport":
            raise URLError("interrupted")
        return Response(
            "https://evil.test/data" if kind == "redirect" else h.PAGES["terms"],
            b"" if kind == "empty" else b"source",
            {"Content-Length": "7"} if kind == "truncated" else {},
        )

    with pytest.raises(h.IngestionError):
        h.fetch(h.PAGES["terms"], opener=opener, sleep=lambda _: None)
    assert len(calls) == (3 if kind == "transport" else 1)


def test_explicit_ods_title_and_header_spacing_preserved():
    def change(root, styles, contracts):
        t = next(
            t
            for t in root.findall(".//t:table", h.NS)
            if h.attr(t, "t", "name") == "2012-13"
        )
        rows = t.findall("t:table-row", h.NS)
        title = rows[0][0].find("x:p", h.NS)
        title.text = "Table"
        space = ET.SubElement(title, q("x", "s"), {q("x", "c"): "2"})
        space.tail = "123 source"
        contracts[0]["title"] = "Table  123 source"
        header = rows[2][3].find("x:p", h.NS)
        header.text = None
        space = ET.SubElement(header, q("x", "s"))
        space.tail = "Authority Data"
        contracts[0]["column_labels"]["4"] = " Authority Data"

    data, source = ods_fixture("123", change)
    rows, notes, _, schema = h.parse_source(data, source, provenance(source), cohort())
    assert schema[0]["title"] == "Table  123 source"
    assert any(n["text"] == " Authority Data" for n in notes)


def test_standalone_pdr_label_retained_without_invented_component_assignment():
    assert (
        h.measure_name("Of which under PDR")
        == "of_which_under_pdr_unspecified_source_label"
    )
    assert (
        h.measure_name("Of which under PDR: total (new build)")
        == "of_which_under_pdr_total_new_build"
    )
