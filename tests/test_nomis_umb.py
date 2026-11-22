"""Contract, source preservation and immutable-recovery tests for Nomis UMB."""

import csv
import io
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pandas as pd
import pytest

from ingestion import nomis_umb as umb
from ingestion import source_io
from ingestion.boe import publish

STAMP = "2026-11-22T07:20:43+00:00"
CONTRACT = Path("configs/nomis_umb_contract.json")
HEADERS = [
    "DATE",
    "DATE_CODE",
    "DATE_NAME",
    "GEOGRAPHY",
    "GEOGRAPHY_CODE",
    "GEOGRAPHY_NAME",
    "GEOGRAPHY_TYPE",
    "GEOGRAPHY_TYPECODE",
    "ITEM",
    "ITEM_NAME",
    "MEASURES",
    "MEASURES_NAME",
    "OBS_VALUE",
    "OBS_STATUS",
    "OBS_STATUS_NAME",
    "OBS_CONF",
    "OBS_CONF_NAME",
    "URN",
    "RECORD_OFFSET",
    "RECORD_COUNT",
]


def encoded(value):
    return json.dumps(value).encode()


def ann(**values):
    return {
        "annotations": {
            "annotation": [
                {"annotationtitle": k, "annotationtext": v} for k, v in values.items()
            ]
        }
    }


def codes(name, values):
    return {
        "structure": {
            "header": {"id": "NM_127_1"},
            "codelists": {"codelist": [{"id": "CL_127_1_" + name, "code": values}]},
        }
    }


def fixtures(areas=2):
    dates = []
    months = list(umb.MONTHS)
    for code in umb.periods():
        y, m = map(int, code.split("-"))
        start = y * 12 + m - 1 - 11
        sy, sm = divmod(start, 12)
        dates.append(
            {
                "value": code,
                "description": {"value": f"{months[sm]} {sy}-{months[m-1]} {y}"},
                **ann(CurrentRevisionReleased="2026-10-20 07:00:00"),
            }
        )
    dates[-1].update(
        ann(
            CurrentRevisionReleased="2026-10-20 07:00:00",
            **{"start period": "apsStartDate", "end period": "apsEndDate"},
        )
    )
    geo = [
        {
            "value": str(100 + i),
            "description": {
                "value": (
                    "Hartlepool" if i == 0 else "Barnsley" if i == 1 else "Extra area"
                )
            },
            **ann(
                TypeCode=424,
                TypeName=umb.GEOGRAPHY_LABEL,
                GeogCode=(
                    "E06000001" if i == 0 else "E08000016" if i == 1 else "E06000002"
                ),
            ),
        }
        for i in range(areas)
    ]
    meta = {
        "definition": {
            "structure": {
                "keyfamilies": {
                    "keyfamily": [
                        {
                            "id": "NM_127_1",
                            "name": {"value": "model-based estimates of unemployment"},
                            "version": 1.0,
                            "components": {
                                "dimension": [
                                    {"conceptref": v}
                                    for v in ["GEOGRAPHY", "ITEM", "MEASURES", "FREQ"]
                                ]
                            },
                            **ann(Units="Persons"),
                        }
                    ]
                }
            }
        },
        "item": codes(
            "ITEM",
            [{"value": 2, "description": {"value": "Unemployment rate (model based)"}}],
        ),
        "measures": codes(
            "MEASURES",
            [
                {"value": 20100, "description": {"value": "value"}},
                {"value": 20701, "description": {"value": "confidence"}},
            ],
        ),
        "dates": codes("TIME", dates),
        "geography_current": codes("GEOGRAPHY", geo),
        "overview": {
            "overview": {
                "restricted": "false",
                "lastupdated": "2026-10-20 07:00:00",
                "lastrevised": "2021-09-14 07:00:00",
                "units": {"unit": {"name": "Persons"}},
            }
        },
        "time_metadata": {
            "metadata": {
                "entries": {
                    "entry": [
                        {
                            "id": 1,
                            "periodstart": "2004-01-01",
                            "periodend": "2004-12-01",
                            "revisions": {
                                "revision": {
                                    "released": "2006-03-29 09:30:00",
                                    "status": "current",
                                    "version": 0,
                                }
                            },
                        },
                        {
                            "id": 2,
                            "periodstart": "apsStartDate",
                            "periodend": "apsEndDate",
                            "revisions": {
                                "revision": {
                                    "released": "2026-10-20 07:00:00",
                                    "status": "Live",
                                    "version": 0,
                                }
                            },
                        },
                    ]
                }
            }
        },
        "item_metadata": {"metadata": {"notfound": "CL_127_1_ITEM"}},
        "measures_metadata": {
            "metadata": {
                "entries": {
                    "entry": [
                        {
                            "id": 20202,
                            "text": "Generic claimant measure; not selected item",
                        }
                    ]
                }
            }
        },
    }
    bodies = {k: encoded(v) for k, v in meta.items()}
    bodies.update(
        dataset=b"<html>Published model-based unemployment: economically active residents aged 16 and over</html>",
        copyright=b"<p>Office for National Statistics - Open Government Licence - Crown copyright</p>",
        terms=b"<p>Public statistical service terms</p>",
    )
    return bodies


def csv_body(codes_requested, bodies):
    dates = {
        x["value"]: x["description"]["value"]
        for x in json.loads(bodies["dates"])["structure"]["codelists"]["codelist"][0][
            "code"
        ]
    }
    geo = json.loads(bodies["geography_current"])["structure"]["codelists"]["codelist"][
        0
    ]["code"]
    rows = []
    for code in codes_requested:
        for x in geo:
            for measure in ["20100", "20701"]:
                a = umb.annotation(x)
                missing = measure == "20701" and str(x["value"]) == "100"
                rows.append(
                    dict(
                        DATE=code,
                        DATE_CODE=code,
                        DATE_NAME=dates[code],
                        GEOGRAPHY=str(x["value"]),
                        GEOGRAPHY_CODE=a["GeogCode"],
                        GEOGRAPHY_NAME=x["description"]["value"],
                        GEOGRAPHY_TYPE=umb.GEOGRAPHY_LABEL,
                        GEOGRAPHY_TYPECODE="424",
                        ITEM="2",
                        ITEM_NAME="Unemployment rate (model based)",
                        MEASURES=measure,
                        MEASURES_NAME="Value" if measure == "20100" else "Confidence",
                        OBS_VALUE=(
                            ""
                            if missing
                            else "7.700" if measure == "20100" else "1.300"
                        ),
                        OBS_STATUS="Q" if missing else "A",
                        OBS_STATUS_NAME=(
                            "These figures are missing." if missing else "Normal Value"
                        ),
                        OBS_CONF="F",
                        OBS_CONF_NAME="Free (free for publication)",
                        URN=f"Nm-127d1d0d{x['value']}d2d{measure}",
                        RECORD_OFFSET=str(len(rows)),
                        RECORD_COUNT="",
                    )
                )
    for row in rows:
        row["RECORD_COUNT"] = str(len(rows))
    return write_rows(rows)


def write_rows(rows, fields=HEADERS):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
    return out.getvalue().encode()


def downloader(bodies, calls):
    by_url = {url: name for name, url in umb.METADATA_URLS.items()}

    def get(url):
        calls.append(url)
        body = (
            csv_body(parse_qs(urlsplit(url).query)["date"][0].split(","), bodies)
            if ".data.csv?" in url
            else bodies[by_url[url]]
        )
        return body, dict(
            status=200,
            url=url,
            resolved_url=url,
            retrieved_at=STAMP,
            response_headers={
                "Content-Type": "application/json",
                "Set-Cookie": "SYNTHETIC_SESSION_ONLY",
                "Authorization": "SYNTHETIC_AUTH_ONLY",
                "X-Session-Id": "SYNTHETIC_SESSION_ONLY",
            },
            token="SYNTHETIC_TOKEN_ONLY",
            cookie="SYNTHETIC_SESSION_ONLY",
        )

    return get


@pytest.fixture
def source(tmp_path, monkeypatch):
    reference = tmp_path / "reference.csv"
    reference.write_text("reference fixture")
    monkeypatch.setattr(
        umb,
        "load_geography_reference",
        lambda p: SimpleNamespace(
            eligible_names={"E06000001": "Hartlepool", "E08000038": "Barnsley"}
        ),
    )
    bodies = fixtures()
    calls = []
    return (
        bodies,
        calls,
        dict(
            reference=reference,
            downloader=downloader(bodies, calls),
            sleep=lambda _: None,
        ),
    )


def hashes(root):
    return {
        str(p.relative_to(root)): umb.sha(p.read_bytes())
        for p in root.rglob("*")
        if p.is_file()
    }


def parsed(bodies=None):
    bodies = bodies or fixtures()
    period, roster, rev, info = umb.parse_metadata(bodies)
    requested = umb.periods()[:20]
    provenance = dict(
        identity={"url": umb.BASE + ".data.csv", "snapshot_id": "one"},
        source_sha256="a" * 64,
        retrieval={"retrieved_at": STAMP},
    )
    return bodies, period, roster, rev, info, requested, provenance


def test_full_snapshot_preserves_rows_missing_confidence_and_code_mismatch(
    tmp_path, source
):
    bodies, calls, kwargs = source
    result = umb.ingest(tmp_path, "one", **kwargs)
    path = Path(result["processed_path"])
    frame = pd.read_parquet(path / "observations.parquet")
    rates = pd.read_parquet(path / "rates.parquet")
    audit = pd.read_parquet(path / "geography_audit.parquet")
    assert len(frame) == 87 * 2 * 2 and len(rates) == 87 * 2
    assert set(frame.gss_code) == {"E06000001", "E08000016"}
    assert frame.loc[frame.measure == "20100", "source_value_text"].eq("7.700").all()
    h = rates[rates.gss_code == "E06000001"]
    assert (
        h.unemployment_rate_percent.eq(7.7).all()
        and h.confidence_margin_percentage_points.isna().all()
    )
    assert h.confidence_obs_status.eq("Q").all() and h.confidence_obs_conf.eq("F").all()
    assert (
        audit.loc[audit.source_code == "E08000016", "relationship"].iloc[0]
        == "same_name_different_code"
    )
    assert (
        audit.loc[audit.source_code == "E08000016", "same_name_target_code"].iloc[0]
        == "E08000038"
    )
    assert not audit.mapping_applied.any()
    assert (
        len(pd.read_parquet(path / "periods.parquet")) == 87
        and len(pd.read_parquet(path / "revisions.parquet")) == 2
    )
    assert not result["exact_point_in_time"] and result[
        "source_timestamp_timezone"
    ].startswith("unverified")
    assert (
        result["metadata"]["generic_units_not_rate_specific"]
        and result["metadata"]["item_metadata_notfound"]
    )
    for p in tmp_path.rglob("manifest.json"):
        value = p.read_text()
        assert (
            "SYNTHETIC_" not in value
            and '"Set-Cookie"' not in value
            and '"Authorization"' not in value
        )
    before = hashes(tmp_path)
    n = len(calls)
    result2 = umb.ingest(
        tmp_path,
        "one",
        **{**kwargs, "downloader": lambda _: pytest.fail("Unexpected network")},
    )
    assert result2 == result and len(calls) == n and hashes(tmp_path) == before


@pytest.mark.parametrize(
    "raw,status,expected,kind",
    [
        ("", "Q", None, "missing"),
        ("..", "Q", None, "source_marker"),
        ("x", "A", None, "source_marker"),
        ("0", "A", 0.0, "numeric"),
        ("1.2500", "A", 1.25, "numeric"),
    ],
)
def test_numeric_and_marker_semantics(raw, status, expected, kind):
    assert umb.parse_value(raw, status) == (expected, kind)


@pytest.mark.parametrize(
    "raw,status", [("0", "Q"), ("NaN", "A"), ("Infinity", "A"), ("1e9999", "A")]
)
def test_inconsistent_or_nonfinite_values_fail(raw, status):
    with pytest.raises(umb.IngestionError):
        umb.parse_value(raw, status)


@pytest.mark.parametrize(
    "mutation",
    [
        "schema",
        "measure",
        "measure_name",
        "item",
        "family",
        "gss",
        "date",
        "label",
        "duplicate",
        "offset",
        "truncated",
        "urn",
    ],
)
def test_corrupt_extract_fails_without_discarding_records(mutation):
    bodies, period, roster, rev, info, requested, meta = parsed()
    rows = list(csv.DictReader(io.StringIO(csv_body(requested, bodies).decode())))
    if mutation == "schema":
        fields = [x for x in HEADERS if x != "OBS_CONF"]
        for r in rows:
            r.pop("OBS_CONF")
        body = write_rows(rows, fields)
    else:
        if mutation == "measure":
            rows[0]["MEASURES"] = "20201"
        if mutation == "measure_name":
            rows[0]["MEASURES_NAME"] = "Count"
        if mutation == "item":
            rows[0]["ITEM"] = "1"
        if mutation == "family":
            rows[0]["GEOGRAPHY_TYPECODE"] = "464"
        if mutation == "gss":
            rows[0]["GEOGRAPHY_CODE"] = "E08000038"
        if mutation == "date":
            rows[0]["DATE"] = "2004-11"
        if mutation == "label":
            rows[0]["DATE_NAME"] = "Oct 2004-Dec 2004"
        if mutation == "duplicate":
            rows[1] = {**rows[0], "RECORD_OFFSET": "1"}
        if mutation == "offset":
            rows[1]["RECORD_OFFSET"] = "0"
        if mutation == "truncated":
            rows = rows[:-1]
        if mutation == "urn":
            rows[0]["URN"] = "Nm-17d5d0"
        body = write_rows(rows)
    with pytest.raises(umb.IngestionError):
        umb.parse_chunk(body, requested, period, roster, meta, "one")


@pytest.mark.parametrize(
    "code,label",
    [
        ("2004-11", "Dec 2003-Nov 2004"),
        ("2004-12", "Oct 2004-Dec 2004"),
        ("2004-12", "Jan 2004-Dec 2005"),
        ("2004-12", "bad"),
    ],
)
def test_period_contract(code, label):
    with pytest.raises(umb.IngestionError):
        umb.reference_period(code, label)


def test_metadata_placeholders_extra_advertised_period_and_counts_not_hardcoded():
    bodies = fixtures(3)
    d = json.loads(bodies["dates"])
    d["structure"]["codelists"]["codelist"][0]["code"].append(
        {"value": "2026-09", "description": {"value": "Oct 2025-Sep 2026"}}
    )
    bodies["dates"] = encoded(d)
    frame, roster, rev, info = umb.parse_metadata(bodies)
    assert (
        len(frame) == 87
        and len(roster) == 3
        and info["advertised_periods_outside_contract"] == ["2026-09"]
    )
    assert "placeholder_period_annotations" in frame.iloc[-1].flags_json
    assert "metadata_period_end_not_month_end" in rev.iloc[0].flags_json
    assert "apsEndDate" in rev.iloc[1].source_metadata_json


@pytest.mark.parametrize(
    "name", ["definition", "item", "measures", "dates", "geography_current", "overview"]
)
def test_metadata_identity_changes_rejected(name):
    bodies = fixtures()
    d = json.loads(bodies[name])
    if name == "definition":
        d["structure"]["keyfamilies"]["keyfamily"][0]["id"] = "NM_17_5"
    elif name == "item":
        d["structure"]["codelists"]["codelist"][0]["code"][0]["description"][
            "value"
        ] = "Count"
    elif name == "measures":
        d["structure"]["codelists"]["codelist"][0]["code"][1]["value"] = 999
    elif name == "dates":
        d["structure"]["codelists"]["codelist"][0]["code"].pop()
    elif name == "geography_current":
        d["structure"]["codelists"]["codelist"][0]["code"][0].update(
            ann(TypeCode=464, TypeName="old", GeogCode="E06000001")
        )
    else:
        d["overview"]["restricted"] = "true"
    bodies[name] = encoded(d)
    with pytest.raises(umb.IngestionError):
        umb.parse_metadata(bodies)


def test_interrupted_download_resumes_without_overwriting_raw_or_earlier_snapshots(
    tmp_path, source
):
    bodies, calls, kwargs = source
    get = kwargs["downloader"]

    def fail(url):
        if ".data.csv?" in url and "2009-12" in url:
            raise OSError("interrupted")
        return get(url)

    with pytest.raises(OSError):
        umb.ingest(tmp_path, "one", **{**kwargs, "downloader": fail})
    assert (
        not (tmp_path / "processed").exists() and not (tmp_path / "validated").exists()
    )
    saved = hashes(tmp_path)
    umb.ingest(tmp_path, "one", **kwargs)
    after = hashes(tmp_path)
    assert all(after[p] == sha for p, sha in saved.items())
    full = hashes(tmp_path)
    umb.ingest(tmp_path, "two", **kwargs)
    again = hashes(tmp_path)
    assert all(again[p] == sha for p, sha in full.items())


def test_output_publication_interruption_recovers_immutably(
    tmp_path, source, monkeypatch
):
    _, _, kwargs = source
    original = source_io.publish

    def fail(directory, files, info):
        if "processed" in directory.parts:
            raise OSError("publication interrupted")
        return original(directory, files, info)

    monkeypatch.setattr(source_io, "publish", fail)
    with pytest.raises(OSError):
        umb.ingest(tmp_path, "one", **kwargs)
    before = hashes(tmp_path)
    monkeypatch.setattr(source_io, "publish", original)
    umb.ingest(
        tmp_path, "one", **{**kwargs, "downloader": lambda _: pytest.fail("network")}
    )
    after = hashes(tmp_path)
    assert all(after[p] == sha for p, sha in before.items())


def test_corrupt_completed_output_and_raw_fail_closed(tmp_path, source):
    _, _, kwargs = source
    result = umb.ingest(tmp_path, "one", **kwargs)
    p = Path(result["processed_path"]) / "rates.parquet"
    p.write_bytes(b"corrupt")
    with pytest.raises(umb.IngestionError):
        umb.ingest(tmp_path, "one", **kwargs)
    assert p.read_bytes() == b"corrupt"
    p = tmp_path / "raw/nomis_umb/snapshot=one/history01/response.bin"
    p.write_bytes(b"corrupt")
    with pytest.raises(umb.IngestionError):
        umb.ingest(tmp_path, "one", **kwargs)


def test_contract_and_reference_conflicts_preserve_completed_outputs(tmp_path, source):
    _, _, kwargs = source
    umb.ingest(tmp_path, "one", **kwargs)
    before = hashes(tmp_path)
    kwargs["reference"].write_text("changed")
    with pytest.raises(umb.IngestionError, match="conflict"):
        umb.ingest(tmp_path, "one", **kwargs)
    assert all(
        umb.sha((tmp_path / p).read_bytes()) == sha
        for p, sha in before.items()
        if p != "reference.csv"
    )
    changed = tmp_path / "contract.json"
    d = json.loads(CONTRACT.read_text())
    d["last_period"] = "2026-09"
    changed.write_text(json.dumps(d))
    with pytest.raises(umb.IngestionError, match="approval"):
        umb.load_contract(changed)


def test_release_change_during_acquisition_blocks_publication(tmp_path, source):
    bodies, _, kwargs = source
    get = kwargs["downloader"]
    count = 0

    def change(url):
        nonlocal count
        body, meta = get(url)
        if url == umb.METADATA_URLS["overview"]:
            count += 1
            if count == 2:
                d = json.loads(body)
                d["overview"]["lastupdated"] = "new release"
                body = encoded(d)
        return body, meta

    with pytest.raises(umb.IngestionError, match="release changed"):
        umb.ingest(tmp_path, "one", **{**kwargs, "downloader": change})
    assert (
        not (tmp_path / "processed").exists() and not (tmp_path / "validated").exists()
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://www.nomisweb.co.uk/datasets/umb",
        "https://evil.test/datasets/umb",
        "https://user:password@www.nomisweb.co.uk/datasets/umb",
        umb.BASE + ".data.csv?uid=secret",
        umb.BASE + ".data.csv?Token=secret",
    ],
)
def test_credential_or_unofficial_urls_rejected(url):
    with pytest.raises(umb.IngestionError):
        umb.source_url(url)


class Response:
    def __init__(self, url, body=b"source", headers=None, status=200):
        self.url = url
        self.body = body
        self.headers = headers or {}
        self.status = status

    def read(self, n):
        return self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_http_header_exclusion_and_bounded_retry():
    url = umb.METADATA_URLS["definition"]
    attempts = []
    waits = []

    def opener(request, timeout):
        attempts.append(request)
        if len(attempts) == 1:
            raise HTTPError(
                url,
                429,
                "limited",
                {"Retry-After": "3", "Set-Cookie": "SYNTHETIC_SESSION_ONLY"},
                None,
            )
        return Response(
            url,
            headers={
                "Content-Length": "6",
                "ETag": "safe",
                "Set-Cookie": "SYNTHETIC_SESSION_ONLY",
                "Authorization": "SYNTHETIC_AUTH_ONLY",
            },
        )

    body, meta = umb.fetch(url, opener=opener, sleep=waits.append)
    assert body == b"source" and waits == [3]
    assert meta["response_headers"] == {"Content-Length": "6", "ETag": "safe"}
    assert (
        "SYNTHETIC_" not in json.dumps(meta)
        and meta["prior_attempts"][0]["status"] == 429
    )


@pytest.mark.parametrize(
    "kind", ["403", "long_retry", "truncated", "redirect", "empty", "transport"]
)
def test_http_failures_stop_safely(kind):
    url = umb.METADATA_URLS["definition"]
    calls = []

    def opener(*a, **k):
        calls.append(1)
        if kind == "403":
            raise HTTPError(url, 403, "denied", {}, None)
        if kind == "long_retry":
            raise HTTPError(url, 429, "limited", {"Retry-After": "120"}, None)
        if kind == "transport":
            raise URLError("transport")
        if kind == "truncated":
            return Response(url, headers={"Content-Length": "7"})
        if kind == "redirect":
            return Response("https://evil.test/data")
        return Response(url, b"")

    with pytest.raises(umb.IngestionError):
        umb.fetch(url, opener=opener, sleep=lambda _: None)
    assert len(calls) == (3 if kind == "transport" else 1)


def test_explicit_verified_cache_import_and_missing_cache(tmp_path, source):
    bodies, _, kwargs = source
    cache = tmp_path / "cache"
    get = kwargs["downloader"]
    urls = dict(umb.METADATA_URLS)
    for i in range(0, 87, 20):
        from urllib.parse import urlencode

        urls[f"history{i//20+1:02d}"] = (
            umb.BASE
            + ".data.csv?"
            + urlencode(
                dict(
                    geography="2092957699TYPE424",
                    date=",".join(umb.periods()[i : i + 20]),
                    item="2",
                    measures="20100,20701",
                    ExcludeMissingValues="false",
                    ExcludeZeroValues="false",
                )
            )
        )
    for name, url in urls.items():
        body, meta = get(url)
        publish(
            cache / name,
            {"response.bin": body},
            {"identity": {"url": url}, "status": 200, "retrieved_at": STAMP},
        )
    result = umb.ingest(tmp_path / "data", "one", **kwargs, source_cache=cache)
    assert (
        result["sources"]["history01"]["retrieval"]["acquisition"]
        == "verified_local_official_response"
    )
    assert (
        result["sources"]["overview_after"]["source_sha256"]
        == result["sources"]["overview"]["source_sha256"]
    )
    with pytest.raises(umb.IngestionError):
        umb.cached_source(cache, "https://www.nomisweb.co.uk/absent")
