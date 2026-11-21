"""Task 009.3 research HTTP evidence only; not production ingestion."""

import argparse
import json
import time
from html.parser import HTMLParser
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit, urljoin
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ingestion.boe import publish, safe_http_headers, verify_bundle

RAW = Path("data/raw/umb-009-3-investigation")
OUT = Path("reports/data_audits/009.3")
BASE = "https://www.nomisweb.co.uk/api/v01/dataset/NM_127_1"
UA = "RentalForecasting-UMB-SourceAudit/0.1 (public statistical source investigation)"


def retrieve(name, url):
    if not name.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Invalid research snapshot name")
    if (
        urlsplit(url).hostname not in {"www.nomisweb.co.uk", "www.ons.gov.uk"}
        or urlsplit(url).scheme != "https"
    ):
        raise ValueError("Expected official HTTPS research URL")
    path = RAW / name
    if path.exists():
        meta = verify_bundle(path)
        assert meta["identity"]["url"] == url
        return (path / "response.bin").read_bytes(), meta
    start = datetime.now(timezone.utc).isoformat()
    try:
        response = urlopen(Request(url, headers={"User-Agent": UA}), timeout=60)
    except HTTPError as error:
        response = error
    with response:
        body = response.read(32_000_001)
        if len(body) > 32_000_000:
            raise ValueError("Unexpectedly large research response")
        meta = dict(
            identity={"url": url},
            status=response.code,
            resolved_url=response.url,
            request_headers={"User-Agent": UA},
            response_headers=safe_http_headers(response.headers),
            retrieval_started_at=start,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
    publish(path, {"response.bin": body}, meta)
    return body, verify_bundle(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--get", nargs=2, metavar=("NAME", "URL"))
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--archives", action="store_true")
    args = parser.parse_args()
    if args.archives:

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "a" and ".xls" in attrs.get("href", ""):
                    self.links.append(urljoin("https://www.ons.gov.uk", attrs["href"]))

        page = Links()
        page.feed((RAW / "old_ons_archive/response.bin").read_text(encoding="utf-8"))
        (OUT / "ons-archive-links.json").write_text(
            json.dumps(page.links, indent=2) + "\n", encoding="utf-8"
        )
        urls = {"m01_latest": page.links[0], "m01_previous": page.links[1]}
    elif args.history:
        dates = json.loads((RAW / "dates/response.bin").read_text(encoding="utf-8"))[
            "structure"
        ]["codelists"]["codelist"][0]["code"]
        urls = {}
        for i in range(0, len(dates), 20):
            params = dict(
                geography="2092957699TYPE424",
                date=",".join(str(d["value"]) for d in dates[i : i + 20]),
                item="2",
                measures="20100,20701",
                ExcludeMissingValues="false",
                ExcludeZeroValues="false",
            )
            urls[f"history{i//20+1:02d}"] = BASE + ".data.csv?" + urlencode(params)
    else:
        urls = (
            dict(
                dataset="https://www.nomisweb.co.uk/datasets/umb",
                definition=BASE + "/def.sdmx.json",
                item=BASE + "/item.def.sdmx.json",
                measures=BASE + "/measures.def.sdmx.json",
                dates=BASE + "/time.def.sdmx.json",
                geography=BASE + "/geography.def.sdmx.json",
                time_metadata=BASE + "/time.metadata.json",
            )
            if args.metadata
            else dict([args.get])
        )
    access_path = OUT / "access-evidence.json"
    records = (
        json.loads(access_path.read_text(encoding="utf-8"))
        if access_path.exists()
        else {}
    )
    for name, url in urls.items():
        body, meta = retrieve(name, url)
        records[name] = meta
        access_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        print(name, meta["status"], len(body), flush=True)
        if meta["status"] == 429:
            print("Publisher rate limit: stop; no further requests", flush=True)
            break
        time.sleep(1.5)


if __name__ == "__main__":
    main()
