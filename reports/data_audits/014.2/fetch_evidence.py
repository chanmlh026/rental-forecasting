"""Focused manual research helper; no production ingestion or geography mapping."""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parents[3]
ROOT = BASE / 'data/raw/ashe-014-2-investigation'
INDEX = BASE / 'reports/data_audits/014.2/access-evidence.json'


def fetch(name, url):
    target = ROOT / name
    records = json.loads(INDEX.read_text()) if INDEX.exists() else []
    if target.exists():
        record = next(r for r in records if r['name'] == name)
        assert record['url'] == url
        assert hashlib.sha256(target.read_bytes()).hexdigest() == record['sha256']
        return target.read_bytes()
    if urlsplit(url).netloc != 'www.nomisweb.co.uk':
        raise ValueError('Fresh requests limited to Nomis; ONS acquisition held by ISS-022')
    ROOT.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).isoformat()
    try:
        response = urlopen(Request(url, headers={
            'User-Agent': 'RentalForecasting-ASHE-Research/0.1 (official aggregate availability audit)'
        }), timeout=60)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        record = dict(name=name, url=url, resolved_url=response.url, status=response.code,
                      started_at=start, retrieved_at=datetime.now(timezone.utc).isoformat(),
                      sha256=hashlib.sha256(body).hexdigest(), bytes=len(body),
                      headers={k: v for k, v in response.headers.items() if k.lower() in {
                          'content-type', 'last-modified', 'retry-after', 'etag'}})
    target.write_bytes(body)
    records.append(record)
    INDEX.write_text(json.dumps(records, indent=2) + '\n')
    print(name, record['status'], len(body), flush=True)
    if record['status'] != 200:
        raise RuntimeError('Official access failed; stop without retry or bypass')
    time.sleep(1)
    return body


if __name__ == '__main__':
    fetch(*sys.argv[1:])
