"""Offline source-contract and immutable publication tests."""

from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET

import pandas as pd
import pytest

from ingestion import boe


def xml():
    root = ET.Element("Envelope")
    series = ET.SubElement(root, "Cube", SCODE="IUMZID4")
    ET.SubElement(series, "Cube", FREQ_CODE="M")
    ET.SubElement(series, "Cube", CAT_NAME="OUTPUT IN", CAT_VAL="%")
    ET.SubElement(series, "Cube", FIRST_OBS="2012-01-31", LAST_OBS="2019-02-28")
    for month in pd.period_range("2012-01", "2019-02", freq="M"):
        obs = ET.SubElement(series, "Cube", TIME=str(month.end_time.date()),
                            OBS_VALUE="5.28", LAST_UPDATED="2016-10-31 15:42:54")
        if str(month) == "2019-01":
            obs.set("OBS_VALUE", "2.37")
            obs.set("LAST_UPDATED", "2019-04-05 09:30:00")
            for stamp, kind, value in [("2019-02-07 09:30:00", "PROV_VALUE", "2.36"),
                                       ("2019-03-01 09:30:00", "OBS_VALUE", "2.36"),
                                       ("2019-04-05 09:30:00", "OBS_VALUE", "2.37")]:
                ET.SubElement(obs, "Revision", UPDATE_TIMESTAMP=stamp, **{kind: value})
        if str(month) == "2019-02":
            obs.set("OBS_VALUE", "2.22")
            obs.set("LAST_UPDATED", "2019-06-07 09:30:00")
            for stamp, value in [("2019-03-07", "2.17"), ("2019-04-05", "2.23"),
                                  ("2019-05-08", "2.20"), ("2019-06-07", "2.22")]:
                ET.SubElement(obs, "Revision", UPDATE_TIMESTAMP=stamp + " 09:30:00", OBS_VALUE=value)
    ET.SubElement(series, "OBS_COM", OBS_END="2018-07-31").text = "Population expansion"
    return ET.tostring(root)


def bank():
    return b'<html><table id="stats-table"><tr><th>Date Changed</th><th>Rate</th></tr><tr><td>05 Nov 26</td><td>4.00</td></tr><tr><td>20 Jan 75</td><td>11.25</td></tr></table></html>'


def download(body):
    return lambda url: (body, {"retrieved_at": "2026-11-21T12:00:00+00:00", "url": url})


def test_revision_regressions():
    frames, report = boe.parse_iumzid4(xml())
    selected = frames["selected"].set_index("observation_month")
    assert selected.loc["2019-01", "rate_percent"] == 2.36
    assert selected.loc["2019-01", "observation_status"] == "provisional"
    assert selected.loc["2019-02", "rate_percent"] == 2.17
    assert selected.loc["2012-01", "pre_introduction_backfill"]
    assert selected.loc["2012-01", "source_updated_at"] == "2016-10-31 15:42:54"
    assert selected.loc["2012-01", "history_evidence"] == "current_update_only"
    assert not report["original_publication_complete"]
    january = frames["history"].query("observation_month == '2019-01'")
    assert january.rate_percent.tolist() == [2.36, 2.36, 2.37]
    assert january.event_order.tolist() == [1, 2, 3]
    assert any(n["text"] == "Population expansion" for n in report["source_metadata"])


@pytest.mark.parametrize("old,new", [
    (b'SCODE="IUMZID4"', b'SCODE="OTHER"'),
    (b'OBS_VALUE="5.28"', b'OBS_VALUE="NaN"'),
    (b'TIME="2012-01-31"', b'TIME="2012-02-29"'),
    (b'TIME="2012-01-31"', b'TIME="2012-01-30"'),
    (b'LAST_OBS="2019-02-28"', b'LAST_OBS="2019-03-31"'),
    (b'2016-10-31 15:42:54', b'invalid'),
    (b'OBS_VALUE="2.22"', b'OBS_VALUE="2.99"'),
    (b'UPDATE_TIMESTAMP="2019-03-07', b'UPDATE_TIMESTAMP="2019-07-07'),
    (b'UPDATE_TIMESTAMP="2019-03-07', b'UPDATE_TIMESTAMP="2019-04-05'),
])
def test_invalid_xml(old, new):
    with pytest.raises(boe.IngestionError):
        boe.parse_iumzid4(xml().replace(old, new, 1))


@pytest.mark.parametrize("body", [b"<html>error</html>", b"<Envelope>", b'<!DOCTYPE x><x/>'])
def test_malformed_xml(body):
    with pytest.raises(boe.IngestionError):
        boe.parse_iumzid4(body)


def test_gap():
    root = ET.fromstring(xml())
    series = root[0]
    series.remove(series[4])
    with pytest.raises(boe.IngestionError, match="coverage"):
        boe.parse_iumzid4(ET.tostring(root))


def test_bank_dates_and_rates():
    frames, report = boe.parse_bank_rate(bank())
    assert frames["events"].effective_date.tolist() == [date(1975, 1, 20), date(2026, 11, 5)]
    assert frames["events"].rate_percent.tolist() == [11.25, 4.0]
    assert report["observation_count"] == 2


@pytest.mark.parametrize("body", [bank().replace(b"4.00", b"inf"),
    bank().replace(b"05 Nov 26", b"20 Jan 75"),
    bank().replace(b"20 Jan 75", b"21 Jan 75"),
    bank().replace(b"Date Changed", b"Date"), bank().replace(b"</table>", b""),
    bank().replace(b"05 Nov 26", b"32 Nov 26")])
def test_bank_failures(body):
    with pytest.raises(boe.IngestionError):
        boe.parse_bank_rate(body)


@pytest.mark.parametrize("dataset,body", [("iumzid4", xml()), ("bank_rate", bank())])
def test_ingestion_rerun_recovery_and_corruption(tmp_path, dataset, body, monkeypatch):
    def fail(*args):
        raise OSError("interrupted publication")
    original = boe.publish
    def interrupted(directory, files, info):
        if "processed" in directory.parts:
            fail()
        return original(directory, files, info)
    monkeypatch.setattr(boe, "publish", interrupted)
    with pytest.raises(OSError):
        boe.ingest(tmp_path, dataset, "run1", date(2026, 11, 21), download(body))
    monkeypatch.setattr(boe, "publish", original)
    result = boe.ingest(tmp_path, dataset, "run1", date(2026, 11, 21), fail)
    manifest = Path(result["processed_path"]) / "manifest.json"
    before = manifest.read_bytes()
    assert boe.ingest(tmp_path, dataset, "run1", date(2026, 11, 21), fail) == result
    assert manifest.read_bytes() == before
    (Path(result["raw_path"]) / "response.bin").write_bytes(b"corruption")
    with pytest.raises(boe.IngestionError, match="checksum"):
        boe.ingest(tmp_path, dataset, "run1", date(2026, 11, 21), fail)


def test_request_conflict_and_selected_change(tmp_path):
    boe.ingest(tmp_path, "iumzid4", "one", date(2026, 11, 21), download(xml()))
    with pytest.raises(boe.IngestionError, match="different request"):
        boe.ingest(tmp_path, "iumzid4", "one", date(2026, 11, 22), download(xml()))
    with pytest.raises(boe.IngestionError, match="earliest record changed"):
        boe.ingest(tmp_path, "iumzid4", "two", date(2026, 11, 21),
                   download(xml().replace(b'PROV_VALUE="2.36"', b'PROV_VALUE="2.35"')))


def test_failed_source_not_promoted(tmp_path):
    with pytest.raises(boe.IngestionError):
        boe.ingest(tmp_path, "bank_rate", "bad", date(2026, 11, 21), download(b"error"))
    assert list((tmp_path / "raw").rglob("response.bin"))
    assert not (tmp_path / "processed").exists()


@pytest.mark.parametrize("identifier", ["../escape", "..", "", "a/b"])
def test_identifier(tmp_path, identifier):
    with pytest.raises(boe.IngestionError):
        boe.ingest(tmp_path, "bank_rate", identifier, date(2026, 11, 21))


def test_retry_and_access_failure(monkeypatch):
    calls = []
    def failure(*args, **kwargs):
        calls.append(1)
        raise URLError("offline")
    monkeypatch.setattr(boe, "urlopen", failure)
    monkeypatch.setattr(boe.time, "sleep", lambda seconds: None)
    with pytest.raises(boe.IngestionError, match="3 attempts"):
        boe.fetch(boe.BANK_URL)
    assert len(calls) == 3
    def forbidden(*args, **kwargs):
        raise HTTPError(boe.BANK_URL, 403, "forbidden", {}, None)
    monkeypatch.setattr(boe, "urlopen", forbidden)
    with pytest.raises(boe.IngestionError, match="403"):
        boe.fetch(boe.BANK_URL)


@pytest.mark.parametrize("body,headers,url", [
    (b"short", {"Content-Length": "100"}, boe.BANK_URL),
    (b"", {}, boe.BANK_URL),
    (b"source", {}, "https://other.example/data"),
])
def test_incomplete_or_redirected_download(monkeypatch, body, headers, url):
    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, size):
            return body
    response = Response()
    response.url, response.headers = url, headers
    monkeypatch.setattr(boe, "urlopen", lambda *args, **kwargs: response)
    with pytest.raises(boe.IngestionError):
        boe.fetch(boe.BANK_URL)


def test_output_corruption_rejected(tmp_path):
    result = boe.ingest(tmp_path, "bank_rate", "one", date(2026, 11, 21), download(bank()))
    (Path(result["processed_path"]) / "events.parquet").write_bytes(b"corrupt")
    with pytest.raises(boe.IngestionError, match="checksum"):
        boe.ingest(tmp_path, "bank_rate", "one", date(2026, 11, 21), download(bank()))


def test_immutable_conflict_and_incomplete_bundle(tmp_path):
    directory = tmp_path / "snapshot"
    boe.publish(directory, {"data": b"original"}, {"identity": "one"})
    with pytest.raises(boe.IngestionError, match="conflict"):
        boe.publish(directory, {"data": b"replacement"}, {"identity": "one"})
    assert (directory / "data").read_bytes() == b"original"
    (directory / "manifest.json").unlink()
    with pytest.raises(boe.IngestionError, match="Incomplete"):
        boe.verify_bundle(directory)


def test_changed_bank_event_preserves_previous_output(tmp_path):
    result = boe.ingest(tmp_path, "bank_rate", "one", date(2026, 11, 21), download(bank()))
    original = (Path(result["processed_path"]) / "events.parquet").read_bytes()
    with pytest.raises(boe.IngestionError, match="Bank Rate event changed"):
        boe.ingest(tmp_path, "bank_rate", "two", date(2026, 11, 21), download(bank().replace(b"4.00", b"4.01")))
    assert (Path(result["processed_path"]) / "events.parquet").read_bytes() == original
