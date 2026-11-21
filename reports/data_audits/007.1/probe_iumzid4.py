"""One-off Task 007.1 source probe, not production ingestion.

Replay: python probe_iumzid4.py requests.json evidence.json
Raw HTTP responses stay in a printed temporary directory, not in Git.
Only public request metadata, observation attributes and links are retained.
"""

import concurrent.futures
import hashlib
import json
import re
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def probe(request, raw_dir):
    record = dict(request)
    record["started_at"] = datetime.now(timezone.utc).isoformat()
    headers = {"User-Agent": request.get("user_agent", "Mozilla/5.0")}
    record["request_headers"] = headers
    try:
        response = urllib.request.urlopen(
            urllib.request.Request(request["url"], headers=headers), timeout=30
        )
    except urllib.error.HTTPError as error:
        response = error
        record["error"] = str(error)
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        return record
    with response:
        body = response.read()
        record.update(
            status=response.code,
            resolved_url=response.url,
            content_type=response.headers.get("Content-Type"),
            response_date=response.headers.get("Date"),
            bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
        )
    (raw_dir / (request["id"] + ".bin")).write_bytes(body)
    text = body.decode("utf-8-sig", errors="replace")
    try:
        root = ET.fromstring(body)
        record["xml_root"] = root.tag
        record["xml_attributes"] = [
            {"tag": node.tag, "attributes": node.attrib}
            for node in root.iter()
            if node.attrib and "TIME" not in node.attrib and not node.tag.endswith("Revision")
        ]
        record["observations"] = [
            {
                **node.attrib,
                "revisions": [child.attrib for child in node if child.tag.endswith("Revision")],
                "note_present": any(child.tag.endswith("OBS_COM") for child in node),
            }
            for node in root.iter() if "TIME" in node.attrib
        ]
    except ET.ParseError:
        if "<html" in text.lower() or "<form" in text.lower():
            page = Page()
            page.feed(text)
            record["data_links"] = [
                link for link in page.links
                if re.search(r"prev|revis|xml|excel|csv|showcolumns|history", link, re.I)
            ]
            title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
            record["html_title"] = title.group(1).strip() if title else None
            published = re.search(r"Published:\s*(\d{2}\s+\w{3}\s+\d{4})", text)
            if published:
                record["published_label"] = published.group(1)
            if "Rates from July 2018 are affected by an increase in the population sample" in text:
                record["july_2018_population_note_present"] = True
            if "/ErrorPage.asp" in record["resolved_url"]:
                record["application_error"] = "Problem with request (HTTP 200 error page)"
            elif "ERROR - too many series" in text:
                record["application_error"] = "ERROR - too many series (HTTP 200)"
            record["data_rows"] = [
                re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row)).strip()
                for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, re.I | re.S)
                if re.search(r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", row)
                and not re.search(r"Notes:|Following a regular", row)
            ]
        elif len(body) < 20000:
            record["text"] = text
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    return record


if __name__ == "__main__":
    requests = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw_dir = Path(tempfile.mkdtemp(prefix="rental-007-1-"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(lambda item: probe(item, raw_dir), requests))
    Path(sys.argv[2]).write_text(
        json.dumps({"task": "007.1", "requests": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Local raw responses:", raw_dir)
    for record in records:
        print(record["id"], record.get("status"), record.get("bytes"), record.get("error", ""))
