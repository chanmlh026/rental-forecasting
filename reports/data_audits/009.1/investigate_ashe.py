"""Focused ASHE source investigation, not a production ingestion pipeline.

Original public responses are cached immutably under ignored data/raw.
No browser impersonation, cookies, authentication or access-control workaround.
"""

import argparse
import io
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from ingestion.boe import publish, safe_http_headers, verify_bundle

DATASET = "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8"
ROOT = Path("data/raw/ashe-009-1-investigation")
USER_AGENT = "RentalForecasting-ASHE-SourceAudit/0.1 (public statistical source investigation)"
EDITION_LABELS = {}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.heading = None
        self.edition = ""
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            url = urljoin(DATASET, attrs["href"])
            self.links.append(url)
            EDITION_LABELS[url] = self.edition
        if tag == "h3":
            self.heading = []

    def handle_data(self, data):
        self.text.append(data)
        if self.heading is not None:
            self.heading.append(data)

    def handle_endtag(self, tag):
        if tag == "h3" and self.heading is not None:
            self.edition = " ".join("".join(self.heading).split())
            self.heading = None


def retrieve(name, url):
    target = ROOT / name
    if target.exists():
        metadata = verify_bundle(target)
        assert metadata["identity"]["url"] == url
        return (target / "response.bin").read_bytes(), metadata
    started = datetime.now(timezone.utc).isoformat()
    try:
        response = urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=45)
    except HTTPError as error:
        response = error
    except URLError as error:
        return None, {"identity": {"url": url}, "retrieval_started_at": started,
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "error": str(error)}
    with response:
        body = response.read()
        metadata = dict(identity={"url": url}, status=response.code, resolved_url=response.url,
            request_headers={"User-Agent": USER_AGENT}, response_headers=safe_http_headers(response.headers),
            retrieval_started_at=started, retrieved_at=datetime.now(timezone.utc).isoformat())
    publish(target, {"response.bin": body}, metadata)
    return body, verify_bundle(target)


def discover():
    body, metadata = retrieve("dataset-page", DATASET)
    if body is None or metadata.get("status") != 200:
        raise RuntimeError("Dataset page unavailable")
    page = Links()
    page.feed(body.decode("utf-8"))
    return sorted(set(url for url in page.links if ".zip" in url))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--retry-rate-limited", action="store_true")
    parser.add_argument("--publication", action="store_true")
    args = parser.parse_args()
    if args.publication:
        urls={
            "edition-2026-provisional": DATASET+"/2026provisional",
            "edition-2025-provisional": DATASET+"/2025provisional",
            "edition-2025-revised": DATASET+"/2025revised",
            "edition-2015-versions": DATASET+"/2015",
            "qmi": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/methodologies/annualsurveyofhoursandearningslowpayandannualsurveyofhoursandearningspensionresultsqmi",
            "bulletin-2026": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2026",
            "questionnaire-guide": "https://www.ons.gov.uk/surveys/informationforbusinesses/businesssurveys/additionalguidancefortheannualsurveyofhoursandearningspaperquestionnaire",
            "licence": "https://www.ons.gov.uk/help/terms-conditions",
        }
        results=[]
        for name,url in urls.items():
            body,metadata=retrieve(name,url)
            record={"id":name,"url":url,"metadata":metadata}
            if body and metadata.get("status")==200:
                page=Links()
                page.feed(body.decode("utf-8"))
                text=" ".join(" ".join(page.text).split())
                record["release_date_labels"]=re.findall(r"Release date:\s*(\d{1,2}\s+\w+\s+\d{4})",text)
                record["open_government_licence_mentioned"]="Open Government Licence" in text
                record["previous_download_links"]=[link for link in page.links if "version-" in link or ".zip" in link]
                record["correction_mentioned"]=bool(re.search(r"correction|error",text,re.I))
            results.append(record)
            print(name,metadata.get("status"),record.get("release_date_labels"),flush=True)
            if metadata.get("status")==429:
                break
            time.sleep(1.5)
        Path("reports/data_audits/009.1/publication-evidence.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
        return
    if args.retry_rate_limited:
        path = Path("reports/data_audits/009.1/access-evidence.json")
        records = json.loads(path.read_text(encoding="utf-8"))
        for record in records:
            previous = record["metadata"]
            if previous.get("status") != 429:
                continue
            # Retry the same public link/headers after the publisher's interval;
            # never overwrite the original error snapshot or work around a block.
            delay = int(previous.get("response_headers", {}).get("Retry-After", "10"))
            received = datetime.fromisoformat(previous["retrieved_at"])
            remaining = delay - (datetime.now(timezone.utc)-received).total_seconds()
            if remaining > 0:
                time.sleep(min(remaining + 1, 60))
                if remaining > 59:
                    print("Publisher wait remains; stop and resume later", flush=True)
                    break
            time.sleep(1.5)
            name = re.sub(r"[^a-zA-Z0-9_.-]", "_", record["url"].rsplit("/",1)[-1])
            body, metadata = retrieve(name + ".retry1", record["url"])
            record.setdefault("previous_attempts", []).append(previous)
            record["metadata"] = metadata
            record["raw_directory"] = name + ".retry1"
            if body and zipfile.is_zipfile(io.BytesIO(body)):
                with zipfile.ZipFile(io.BytesIO(body)) as archive:
                    record["files"] = archive.namelist()
            path.write_text(json.dumps(records, indent=2)+"\n",encoding="utf-8")
            print("Paced retry",name,metadata.get("status"),flush=True)
            if metadata.get("status") != 200:
                print("Stopping at renewed source restriction/failure",flush=True)
                break
        return
    links = discover()
    print("Advertised ZIP links:", len(links))
    Path("reports/data_audits/009.1/download-links.json").write_text(json.dumps(links, indent=2)+"\n", encoding="utf-8")
    selected = [u for u in links if any(s in u for s in ["2026provisional", "2025revised", "2002"])] if args.initial else links
    evidence_path = Path("reports/data_audits/009.1/access-evidence.json")
    prior_records = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.exists() else []
    prior_by_url = {record["url"]: record for record in prior_records}
    def inspect_url(url):
        previous = prior_by_url.get(url)
        if previous and previous["metadata"].get("status") == 200:
            name = previous.get("raw_directory") or re.sub(r"[^a-zA-Z0-9_.-]", "_", url.rsplit("/", 1)[-1])
            verify_bundle(ROOT / name)
            return previous
        name = re.sub(r"[^a-zA-Z0-9_.-]", "_", url.rsplit("/", 1)[-1])
        body, metadata = retrieve(name, url)
        record = {"url": url, "edition": EDITION_LABELS.get(url), "metadata": metadata}
        if body and zipfile.is_zipfile(io.BytesIO(body)):
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                record["files"] = archive.namelist()
                annual = [n for n in archive.namelist() if re.search(r"Annual pay.*Gross", n, re.I)]
                print(name, metadata.get("status"), "annual files", annual)
                if args.inspect:
                    for member in annual:
                        raw = archive.read(member)
                        if member.lower().endswith(".xlsx"):
                            import openpyxl
                            book = openpyxl.load_workbook(io.BytesIO(raw), data_only=False)
                            print("SHEETS", member, book.sheetnames)
                            sheet = book["All"] if "All" in book.sheetnames else book.worksheets[0]
                            for row in sheet.iter_rows():
                                if row[0].row <= 18 or row[0].row > sheet.max_row - 14:
                                    print(row[0].row, [(c.coordinate, c.value, c.style_id) for c in row if c.value is not None])
                        elif member.lower().endswith(".xls"):
                            import xlrd
                            book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
                            print("SHEETS", member, book.sheet_names())
                            sheet = book.sheet_by_index(0)
                            for i in list(range(min(18, sheet.nrows))) + list(range(max(18, sheet.nrows-14), sheet.nrows)):
                                print(i+1, [(j+1, value) for j,value in enumerate(sheet.row_values(i)) if value != ""])
        else:
            print(name, metadata.get("status"), metadata.get("error", "not a ZIP"))
        return record
    results = []
    for url in selected:
        record = inspect_url(url)
        results.append(record)
        if record["metadata"].get("status") == 429:
            print("Rate limit encountered; stop further fresh requests", flush=True)
            # Preserve existing access records for URLs not attempted this run.
            path=Path("reports/data_audits/009.1/access-evidence.json")
            prior=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
            results.extend(r for r in prior if r["url"] not in {x["url"] for x in results})
            break
        time.sleep(1.5)
    results.extend(r for r in prior_records if r["url"] not in {x["url"] for x in results})
    evidence_path.write_text(json.dumps(results, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
