"""Planning source contracts, native historical ambiguity, immutable recovery/security."""

import csv
import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request
import pytest
from ingestion import mhclg_planning as p

STAMP = "2026-11-22T12:58:38+00:00"
COHORT = {"E08000038": "Barnsley", "E07000001": "Example"}


def fixture(table="PS2", rows=None):
    columns = ["Region", "LPANM", "LPACD", "Quarter"]
    columns += (
        ["Applications received", "Applications decided", "Applications withdrawn"]
        if table == "PS1"
        else [
            a + "; " + c + " (all)"
            for a in ["Total decisions", "Total granted", "Total refused"]
            for c in ["major dwellings", "minor dwellings"]
        ]
    )
    columns += ["F_Year"]
    values = ["10", "..", "2"] if table == "PS1" else ["10", "..", "7", "..", "3", ".."]
    rows = rows or [
        ["North", "Barnsley\u2019s original", "E08000016", "2025 Q4"]
        + values
        + ["2025-26"]
    ]
    preamble = [
        ["Official " + table],
        ["Native periods"],
        *([["PDR definition changed"]] if table == "PS1" else []),
    ]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(preamble + [columns] + rows)
    body = buf.getvalue().encode("cp1252")
    source = dict(
        edition_id=table.lower() + "_full",
        table=table,
        kind="full",
        columns=columns,
        preamble=preamble,
        url="https://assets.publishing.service.gov.uk/media/test/"
        + table
        + "_data_test.csv",
        source_sha256=p.sha(body),
    )
    meta = {"retrieval": {"retrieved_at": STAMP}}
    return body, source, meta


@pytest.mark.parametrize("table", ["PS1", "PS2"])
def test_original_cells_encoding_periods_markers_geography(table):
    b, s, m = fixture(table)
    raw, n = p.parse_source(b, s, m, COHORT)
    assert raw.LPANM[0] == "Barnsley\u2019s original"
    assert raw.LPACD[0] == "E08000016" and not raw.exact_cohort_code_match[0]
    assert raw.period_start[0] == "2025-10-01" and raw.period_end[0] == "2025-12-31"
    assert raw.F_Year[0] == "2025-26"
    col = s["columns"][5]
    assert raw[col][0] == ".." and n[col].isna()[0]
    assert raw.source_record[0] == len(s["preamble"]) + 2
    cov, geo, schema = p.audit_tables(raw, n, s, COHORT)
    assert not geo.mapping_applied.any()
    assert all(
        x["unit"].endswith("not_dwelling_units")
        for x in schema
        if x["value_type"] == "count"
    )


@pytest.mark.parametrize(
    "quarter,end",
    [("2024 Q1", "2024-03-31"), ("2015 Q2", "2015-06-30"), ("1979 Q3", "1979-09-30")],
)
def test_quarter_end(quarter, end):
    assert p.quarter_period(quarter)[1] == end


@pytest.mark.parametrize(
    "quarter", ["2025 Q0", "2025 Q5", "2025Q1", "Q1 2025", "2025 Q1 [r]"]
)
def test_invalid_quarter(quarter):
    with pytest.raises(p.IngestionError):
        p.quarter_period(quarter)


def test_native_duplicate_and_missing_codes_preserved_not_silently_deduplicated():
    b, s, m = fixture("PS1")
    r = list(csv.reader(io.StringIO(b.decode("cp1252"))))[-1]
    b, s, m = fixture("PS1", [r, r, list(r[:2]) + ["-", r[3]] + r[4:]])
    raw, n = p.parse_source(b, s, m, COHORT)
    assert len(raw) == 3 and raw.source_record.nunique() == 3
    assert raw.source_duplicate_payload.tolist() == [True, True, False]
    assert raw.source_authority_period_collision.tolist() == [True, True, False]
    assert raw.source_code_is_gss.tolist() == [True, True, False]


@pytest.mark.parametrize(
    "mutation",
    ["header", "preamble", "ragged", "unknown_marker", "quarter", "blank_identifier"],
)
def test_changed_or_malformed_source_stops(mutation):
    b, s, m = fixture()
    r = list(csv.reader(io.StringIO(b.decode("cp1252"))))
    if mutation == "header":
        r[-2][4] = "Dwelling units permitted"
    if mutation == "preamble":
        r[0] = ["Unreviewed release"]
    if mutation == "ragged":
        r[-1].pop()
    if mutation == "unknown_marker":
        r[-1][4] = "suppressed?"
    if mutation == "quarter":
        r[-1][3] = "2025 Q9"
    if mutation == "blank_identifier":
        r[-1][2] = ""
    buf = io.StringIO()
    csv.writer(buf).writerows(r)
    with pytest.raises(p.IngestionError):
        p.parse_source(buf.getvalue().encode("cp1252"), s, m, COHORT)


def contract(tmp_path):
    b, s, m = fixture()
    d = b"Open Government Licence"
    inv = tmp_path / "sources.json"
    inv.write_text(
        json.dumps(
            dict(
                sources=[s],
                documents={
                    "terms": {
                        "url": "https://www.gov.uk/help/terms-conditions",
                        "source_sha256": p.sha(d),
                    }
                },
            )
        )
    )
    ref = Path("configs/ons_lad_apr2025_v2.csv")
    calls = []

    def fetch(url):
        calls.append(url)
        return (b if url == s["url"] else d), dict(
            status=200,
            retrieved_at=STAMP,
            response_headers={"Set-Cookie": "synthetic-cookie", "ETag": "test"},
        )

    return inv, ref, fetch, calls


def test_immutable_rerun_and_header_safety(tmp_path, monkeypatch):
    monkeypatch.setattr(p.time, "sleep", lambda _: None)
    inv, ref, download, calls = contract(tmp_path)
    p.ingest(
        tmp_path / "data", "test", inventory=inv, reference=ref, downloader=download
    )
    before = {
        str(f): f.read_bytes() for f in (tmp_path / "data").rglob("*") if f.is_file()
    }

    def no_network(_):
        pytest.fail("offline replay attempted download")

    p.ingest(
        tmp_path / "data", "test", inventory=inv, reference=ref, downloader=no_network
    )
    assert before == {
        str(f): f.read_bytes() for f in (tmp_path / "data").rglob("*") if f.is_file()
    }
    assert len(calls) == 2
    for f in (tmp_path / "data").rglob("manifest.json"):
        assert "synthetic-cookie" not in f.read_text()
    inv.write_text(inv.read_text() + " ")
    with pytest.raises(p.IngestionError, match="identity conflict"):
        p.ingest(
            tmp_path / "data",
            "test",
            inventory=inv,
            reference=ref,
            downloader=no_network,
        )


def test_interrupted_acquisition_reuses_success_and_preserves_prior_outputs(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(p.time, "sleep", lambda _: None)
    inv, ref, download, calls = contract(tmp_path)
    n = 0

    def fail(url):
        nonlocal n
        n += 1
        if n == 2:
            raise p.IngestionError("interrupted")
        return download(url)

    with pytest.raises(p.IngestionError):
        p.ingest(
            tmp_path / "data", "test", inventory=inv, reference=ref, downloader=fail
        )
    assert not (tmp_path / "data" / "processed").exists()
    p.ingest(
        tmp_path / "data", "test", inventory=inv, reference=ref, downloader=download
    )
    assert len(calls) == 2
    raw = next((tmp_path / "data" / "raw").rglob("response.bin"))
    raw.write_bytes(b"corrupt")
    with pytest.raises(p.IngestionError, match="checksum"):
        p.ingest(
            tmp_path / "data", "test", inventory=inv, reference=ref, downloader=download
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://www.gov.uk/robots.txt",
        "https://evil.example/PS2.csv",
        "https://user:password@www.gov.uk/robots.txt",
        "https://www.gov.uk/robots.txt?secret=x",
        "https://assets.publishing.service.gov.uk/media/a/Other.csv",
    ],
)
def test_unapproved_urls_rejected(url):
    with pytest.raises(p.IngestionError):
        p.official_url(url)


def test_redirect_rejected_before_following():
    with pytest.raises(p.IngestionError):
        p.OfficialRedirect().redirect_request(
            Request(p.PAGE), None, 302, "", {}, "https://evil.example/data.csv"
        )


@pytest.mark.parametrize("status", [403, 404, 429, 503])
def test_http_terminal_or_bounded_retry(status):
    calls = []
    waits = []

    def opener(*args, **kwargs):
        calls.append(1)
        raise HTTPError(p.PAGE, status, "test", {}, io.BytesIO())

    with pytest.raises(p.IngestionError):
        p.fetch(p.PAGE, opener=opener, sleep=waits.append)
    assert len(calls) == (1 if status in [403, 404] else 3)


def test_long_retry_after_stops_without_early_retry():
    def opener(*args, **kwargs):
        raise HTTPError(p.PAGE, 429, "test", {"Retry-After": "120"}, io.BytesIO())

    with pytest.raises(p.IngestionError, match="exceeds 60"):
        p.fetch(p.PAGE, opener=opener, sleep=lambda _: pytest.fail("early retry"))


def test_inventory_requires_residential_application_measures(tmp_path):
    inv, _, _, _ = contract(tmp_path)
    x = json.loads(inv.read_text())
    x["sources"][0]["columns"][4] = "Dwelling units permitted"
    inv.write_text(json.dumps(x))
    with pytest.raises(p.IngestionError):
        p.load_inventory(inv)


def test_original_zero_negative_and_blank_values_are_not_filled():
    b, s, m = fixture("PS1")
    rows = list(csv.reader(io.StringIO(b.decode("cp1252"))))
    rows[-1][4:7] = ["0", "-2", ""]
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    raw, n = p.parse_source(buf.getvalue().encode("cp1252"), s, m, COHORT)
    assert raw["Applications received"][0] == "0" and n["Applications received"][0] == 0
    assert raw["Applications decided"][0] == "-2" and n["Applications decided"][0] == -2
    assert (
        raw["Applications withdrawn"][0] == "" and n["Applications withdrawn"].isna()[0]
    )


def test_new_revision_snapshot_preserves_previous_values(tmp_path, monkeypatch):
    monkeypatch.setattr(p.time, "sleep", lambda _: None)
    inv, ref, download, _ = contract(tmp_path)
    root = tmp_path / "data"
    p.ingest(root, "first", inventory=inv, reference=ref, downloader=download)
    previous = {str(f): f.read_bytes() for f in root.rglob("*") if f.is_file()}
    old, source, meta = fixture()
    revised = old.replace(b",7,", b",8,")
    cfg = json.loads(inv.read_text())
    cfg["sources"][0]["source_sha256"] = p.sha(revised)
    inv.write_text(json.dumps(cfg))

    def new_download(url):
        body, meta = download(url)
        return (revised if url == source["url"] else body), meta

    p.ingest(root, "revised", inventory=inv, reference=ref, downloader=new_download)
    assert all(Path(f).read_bytes() == b for f, b in previous.items())


def test_incomplete_response_stops_before_storage():
    class Response:
        url = p.PAGE
        status = 200
        headers = {"Content-Length": "99"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return b"partial"

    with pytest.raises(p.IngestionError, match="incomplete"):
        p.fetch(p.PAGE, opener=lambda *a, **k: Response())


@pytest.mark.parametrize(
    "mutation", ["duplicate_id", "bad_hash", "missing_required", "unsafe_name"]
)
def test_inventory_rejects_ambiguous_or_unreviewed_contract(tmp_path, mutation):
    inv, _, _, _ = contract(tmp_path)
    cfg = json.loads(inv.read_text())
    if mutation == "duplicate_id":
        cfg["sources"] *= 2
    if mutation == "bad_hash":
        cfg["sources"][0]["source_sha256"] = "unknown"
    if mutation == "missing_required":
        cfg["sources"][0]["columns"].remove("F_Year")
    if mutation == "unsafe_name":
        cfg["sources"][0]["edition_id"] = "../outside"
    inv.write_text(json.dumps(cfg))
    with pytest.raises(p.IngestionError):
        p.load_inventory(inv)


def test_independent_audit_reads_bom_reference_without_modifying_it(tmp_path):
    import runpy

    audit = runpy.run_path("reports/data_audits/012/validate_ingestion.py")
    ref = tmp_path / "reference.csv"
    body = "gss_code,target_eligible\nE08000038,true\nE09000001,false\n".encode(
        "utf-8-sig"
    )
    ref.write_bytes(body)
    assert audit["reference_codes"](ref) == {"E08000038"}
    assert ref.read_bytes() == body
