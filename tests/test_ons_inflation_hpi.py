"""Source contracts, vintage preservation, exact geography and recovery."""

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

import pandas as pd
import pytest

from ingestion import ons_inflation as cpi
from ingestion import source_io as sio
from ingestion import uk_hpi as hpi


def ons(code="D7BT", version="current"):
    concept, measure, unit, title = cpi.SERIES[code]
    release = "2026-11-18T00:00:00.000Z" if version == "current" else "2026-10-21T00:00:00.000Z"
    months = [{"date": "2026 SEP", "value": "144.0" if measure == "index" else "3.0",
        "sourceDataset": "MM23", "updateDate": release}]
    if version == "current":
        months.append({"date": "2026 OCT", "value": "144.9" if measure == "index" else "3.6",
            "sourceDataset": "MM23", "updateDate": release})
    return dict(uri=cpi.series_path(code), description=dict(cdid=code, datasetId="MM23",
        title=title + " 2015=100", unit=unit, keyNote="Index, 2015 = 100",
        releaseDate=release, date=months[-1]["date"], number=months[-1]["value"]),
        months=months, versions=[dict(uri=cpi.series_path(code)+"/previous/v1",
        updateDate="2026-10-21T00:00:00.000Z", correctionNotice="Retain this correction")])


def encoded(source):
    return json.dumps(source).encode()


def test_inflation_monthly_identity_vintage_and_precision():
    for code in cpi.SERIES:
        frame, report = cpi.parse_series(encoded(ons(code)), code, "current")
        assert frame.observation_month.tolist() == ["2026-09", "2026-10"]
        assert frame.source_release_date.iloc[0] == date(2026, 11, 18)
        assert frame.source_release_timestamp.iloc[0] == "2026-11-18T00:00:00.000Z"
        assert report["version_inventory"][0]["correctionNotice"] == "Retain this correction"
        assert frame.source_value_text.iloc[-1] == ons(code)["description"]["number"]
        assert not report["missing_months"]


@pytest.mark.parametrize("field,value", [("cdid","WRONG"),("datasetId","OTHER"),
    ("unit","GBP"),("title","CPI INDEX 00: ALL ITEMS"),("keyNote","Index, 2020 = 100"),
    ("date","2026 NOV"),("number","99"),("releaseDate","bad")])
def test_inflation_metadata_failures(field,value):
    source=ons()
    source["description"][field]=value
    with pytest.raises(sio.IngestionError):
        cpi.parse_series(encoded(source),"D7BT","current")


@pytest.mark.parametrize("value", ["NaN","inf","bad","-1"])
def test_inflation_numeric_failures(value):
    source=ons()
    source["months"][0]["value"]=value
    with pytest.raises(sio.IngestionError):
        cpi.parse_series(encoded(source),"D7BT","current")


def test_inflation_duplicate_and_gap_missing_reporting():
    source=ons()
    source["months"].append(source["months"][0])
    with pytest.raises(sio.IngestionError, match="Duplicate"):
        cpi.parse_series(encoded(source),"D7BT","current")
    source=ons()
    source["months"][0]["date"]="2026 AUG"
    source["months"][0]["value"]=""
    frame, report=cpi.parse_series(encoded(source),"D7BT","current")
    assert report["missing_months"]==["2026-09"]
    assert report["missing_values"]==1
    assert frame.value.isna().sum()==1
    source=ons("D7G7")
    source["months"][0]["value"]="-0.5"
    assert cpi.parse_series(encoded(source),"D7G7","current")[0].value.iloc[0]==-0.5


def hpi_csv():
    return ("Date,RegionName,AreaCode,AveragePrice,Index,UnselectedField\n"
        "01/01/2023,Source Alias,E06000001,123456.789,100,retained\n"
        "01/02/2023,Source Alias,E06000001,124000.123,101,retained\n"
        "01/01/2023,Historic Area,E07000001,200000,100,retained\n"
        "01/02/2023,Historic Area,E07000001,,101,retained\n"
        "01/01/2023,England,E92000001,300000,100,retained\n").encode()


def revision_csv():
    return b"Average price,,\r\r\nPublication date,01/01/2023,01/02/2023\r\r\n01/03/2023,123456.789,\r\r\nAnnual growth (%),,\r\r\nPublication date,01/01/2023,01/02/2023\r\r\n01/03/2023,-1.2,2.5\r\r\n"


def test_hpi_full_source_and_exact_code_coverage():
    cohort={"E06000001":"Approved Name", "E06000002":"Missing Authority"}
    tables, report=hpi.parse_hpi(hpi_csv(),"2023-02","2023-01",cohort)
    assert len(tables["source_table"])==5
    assert "UnselectedField" in tables["source_table"]
    assert len(tables["observations"])==5
    assert len(tables["cohort"])==2
    assert tables["cohort"].average_price_gbp.iloc[0]==123456.789
    assert report["unmatched_cohort_codes"]==["E06000002"]
    assert report["missing_cohort_area_months"]==2
    assert tables["cohort_coverage"].source_row_present.tolist()==[True,True,False,False]
    assert tables["cohort"].source_area_name.tolist()==["Source Alias","Source Alias"]
    assert report["source_name_differences"]
    assert report["source_missing_prices"]==1
    assert tables["monthly_coverage"].expected_authorities.tolist()==[2,2]


@pytest.mark.parametrize("old,new", [
    (b"AveragePrice",b"Unknown"), (b"123456.789",b"NaN"),
    (b"123456.789",b"bad"), (b"123456.789",b"-1"),
    (b"01/01/2023",b"02/01/2023"), (b"E06000001",b"BADCODE"),
    (b",100,retained",b",99,retained"), (b",100,retained",b",100"),
])
def test_hpi_source_failures(old,new):
    with pytest.raises(sio.IngestionError):
        hpi.parse_hpi(hpi_csv().replace(old,new,1),"2023-02","2023-01",{})


def test_hpi_duplicate_and_truncation():
    body=hpi_csv()+hpi_csv().splitlines(keepends=True)[1]
    with pytest.raises(sio.IngestionError,match="Duplicate"):
        hpi.parse_hpi(body,"2023-02","2023-01",{})
    with pytest.raises(sio.IngestionError,match="reference month"):
        hpi.parse_hpi(hpi_csv(),"2023-03","2023-01",{})


def test_revision_labels_and_precision_are_not_availability_dates():
    frame=hpi.parse_revisions(revision_csv())
    assert len(frame)==4
    assert frame.source_publication_label.tolist()==["01/03/2023"]*4
    assert frame.source_publication_month.tolist()==["2023-03"]*4
    assert frame.source_value_text.iloc[0]=="123456.789"
    assert frame.value.isna().sum()==1
    assert frame.publication_evidence.str.contains("not_verified").all()
    assert "published_at" not in frame


@pytest.mark.parametrize("body", [b"error", revision_csv()+revision_csv(),
    revision_csv().replace(b"123456.789",b"inf"),
    revision_csv().replace(b"123456.789,",b"123456.789")])
def test_bad_revision_source(body):
    with pytest.raises(sio.IngestionError):
        hpi.parse_revisions(body)


def release_html():
    return ("<html><p>Published: 18 November 2026</p>"
        '<a href="https://publicdata.landregistry.gov.uk/UK-HPI-full-file-2026-09.csv">Full</a>'
        '<a href="https://publicdata.landregistry.gov.uk/Revisions-England-2026-09.csv">Revisions</a></html>').encode()


def test_release_identity_and_base():
    assert hpi.release_contract(release_html(),"2026-09")["source_release_date"]=="2026-11-18"
    assert hpi.summary_base(b"<p>Monthly index (January 2023 = 100)</p>")=="2023-01"
    with pytest.raises(sio.IngestionError):
        hpi.release_contract(release_html(),"2026-08")
    with pytest.raises(sio.IngestionError):
        hpi.summary_base(b"<p>no base metadata</p>")


def inflation_downloader(url):
    code=url.split("/timeseries/")[1].split("/")[0].upper()
    version="v1" if "/previous/" in url else "current"
    return encoded(ons(code,version)), {"retrieved_at":"2026-11-21T14:00:00+00:00",
        "response_headers":{"Set-Cookie":"SYNTHETIC_TEST_ONLY", "Content-Type":"application/json"}}


def test_inflation_ingest_vintages_rerun_recovery(tmp_path,monkeypatch):
    original=sio.publish
    def interrupted(directory,files,info):
        if "processed" in directory.parts:
            raise OSError("interrupted")
        return original(directory,files,info)
    monkeypatch.setattr(sio,"publish",interrupted)
    with pytest.raises(OSError):
        cpi.ingest(tmp_path,"one",downloader=inflation_downloader)
    monkeypatch.setattr(sio,"publish",original)
    def offline(url):
        raise AssertionError("Unexpected download")
    result=cpi.ingest(tmp_path,"one",downloader=offline)
    path=Path(result["processed_path"])
    before={p:p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    cpi.ingest(tmp_path,"one",downloader=offline)
    assert all(p.read_bytes()==body for p,body in before.items())
    frame=pd.read_parquet(path/"observations.parquet")
    assert set(frame.source_version_id)=={"current","v1"}
    assert len(frame)==12
    assert "SYNTHETIC_TEST_ONLY" not in json.dumps(result)
    assert all("SYNTHETIC_TEST_ONLY" not in p.read_text() for p in tmp_path.rglob("manifest.json"))


def test_hpi_pipeline_recovery_and_rerun(tmp_path,monkeypatch):
    monkeypatch.setattr(hpi,"load_geography_reference",lambda path: SimpleNamespace(
        eligible_names={"E06000001":"Approved Name","E06000002":"Missing Authority"},version="fixture"))
    reference=tmp_path/"reference.txt"
    reference.write_text("fixture")
    def downloader(url):
        if "statistical-data-sets" in url:
            body=release_html().replace(b"2026-09",b"2023-02")
        elif "summary" in url:
            body=b"<p>January 2023 = 100</p>"
        elif "Revisions" in url:
            body=revision_csv()
        else:
            body=hpi_csv()
        return body,{"retrieved_at":"2026-11-21T14:00:00+00:00"}
    result=hpi.ingest(tmp_path,"one","2023-02",reference,downloader)
    files={p:p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    def offline(url):
        raise AssertionError("Unexpected download")
    hpi.ingest(tmp_path,"one","2023-02",reference,offline)
    assert all(p.read_bytes()==value for p,value in files.items())
    assert result["validation"]["cohort_codes_matched"]==1
    reference.write_text("changed")
    with pytest.raises(sio.IngestionError,match="conflict"):
        hpi.ingest(tmp_path,"one","2023-02",reference,offline)


def test_source_retry_access_and_immutable_conflict(tmp_path,monkeypatch):
    calls=[]
    def fail(*args,**kwargs):
        calls.append(1)
        raise URLError("offline")
    monkeypatch.setattr(sio,"urlopen",fail)
    monkeypatch.setattr(sio.time,"sleep",lambda seconds: None)
    with pytest.raises(sio.IngestionError):
        sio.fetch("https://www.ons.gov.uk/source")
    assert len(calls)==3
    url="https://www.ons.gov.uk/source"
    sio.raw_source(tmp_path,"fixture","one","source",url,lambda u:(b"body",{}))
    with pytest.raises(sio.IngestionError,match="conflict"):
        sio.raw_source(tmp_path,"fixture","one","source",url+"2",fail)
    (tmp_path/"raw/fixture/snapshot=one/source/response.bin").write_bytes(b"changed")
    with pytest.raises(sio.IngestionError,match="checksum"):
        sio.raw_source(tmp_path,"fixture","one","source",url,fail)
    with pytest.raises(sio.IngestionError):
        sio.official_url("https://thirdparty.example/source")


@pytest.mark.parametrize("body", [b"{", b"{}", b"<html>error</html>"])
def test_malformed_ons_json(body):
    with pytest.raises(sio.IngestionError):
        cpi.parse_series(body,"D7BT","current")


def test_failed_inflation_source_does_not_promote(tmp_path):
    def malformed(url):
        return b"error", {"retrieved_at":"2026-11-21T14:00:00+00:00"}
    with pytest.raises(sio.IngestionError):
        cpi.ingest(tmp_path,"bad",downloader=malformed)
    assert list((tmp_path/"raw").rglob("response.bin"))
    assert not (tmp_path/"validated").exists()
    assert not (tmp_path/"processed").exists()


@pytest.mark.parametrize("length,url", [("100","https://www.ons.gov.uk/source"),
    ("6","https://unofficial.example/source")])
def test_incomplete_download_or_unofficial_redirect(monkeypatch,length,url):
    class Response:
        status=200
        headers={"Content-Length":length}
        def __enter__(self):
            return self
        def __exit__(self,*args):
            pass
        def read(self,size):
            return b"source"
    response=Response()
    response.url=url
    monkeypatch.setattr(sio,"urlopen",lambda *args,**kwargs:response)
    with pytest.raises(sio.IngestionError):
        sio.fetch("https://www.ons.gov.uk/source")


def test_hpi_interrupted_publication_recovers(tmp_path,monkeypatch):
    monkeypatch.setattr(hpi,"load_geography_reference",lambda path: SimpleNamespace(
        eligible_names={"E06000001":"Approved Name"},version="fixture"))
    reference=tmp_path/"reference.txt"
    reference.write_text("fixture")
    def downloader(url):
        if "statistical-data-sets" in url:
            body=release_html().replace(b"2026-09",b"2023-02")
        elif "summary" in url:
            body=b"<p>January 2023 = 100</p>"
        elif "Revisions" in url:
            body=revision_csv()
        else:
            body=hpi_csv()
        return body,{"retrieved_at":"2026-11-21T14:00:00+00:00"}
    original=sio.publish
    def interrupted(directory,files,info):
        if "processed" in directory.parts:
            raise OSError("interrupted")
        return original(directory,files,info)
    monkeypatch.setattr(sio,"publish",interrupted)
    with pytest.raises(OSError):
        hpi.ingest(tmp_path,"one","2023-02",reference,downloader)
    monkeypatch.setattr(sio,"publish",original)
    def offline(url):
        raise AssertionError("Unexpected download")
    result=hpi.ingest(tmp_path,"one","2023-02",reference,offline)
    path=Path(result["processed_path"])/"cohort.parquet"
    original_bytes=path.read_bytes()
    path.write_bytes(b"corrupt")
    with pytest.raises(sio.IngestionError,match="checksum"):
        hpi.ingest(tmp_path,"one","2023-02",reference,offline)
    assert path.read_bytes()==b"corrupt"
    assert original_bytes


def test_storage_configuration(tmp_path):
    config=tmp_path/"configs/storage.toml"
    config.parent.mkdir()
    config.write_text('backend="local"\nlocal_root="./data"\n')
    assert sio.storage_root(config)==tmp_path/"data"
    config.write_text('backend="gcs"\nlocal_root="./data"\n')
    with pytest.raises(sio.IngestionError):
        sio.storage_root(config)
