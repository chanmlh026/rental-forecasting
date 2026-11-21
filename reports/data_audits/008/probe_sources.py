"""Task 008 source inspection; original bodies stay in ignored raw storage."""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from ingestion.boe import safe_http_headers, sha, publish

ROOT = Path("data/raw/008-inspection")
URLS = {
    "cpi.csv": "https://www.ons.gov.uk/generator?format=csv&uri=%2Feconomy%2Finflationandpriceindices%2Ftimeseries%2Fd7bt%2Fmm23",
    "cpi.json": "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23/data",
    "hpi.csv": "https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/UK-HPI-full-file-2026-09.csv",
    "revisions.csv": "https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Revisions-England-2026-09.csv",
}

for name, url in URLS.items():
    destination = ROOT / name
    if destination.exists():
        continue
    start = datetime.now(timezone.utc).isoformat()
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as response:
        body = response.read()
        metadata = dict(url=url, resolved_url=response.url, status=response.status,
            retrieval_started_at=start, retrieved_at=datetime.now(timezone.utc).isoformat(),
            response_headers=safe_http_headers(response.headers), sha256=sha(body))
    publish(destination, {"response.bin": body}, {"identity": {"url": url}, "retrieval": metadata})
    print(name, len(body), body[:650].decode("utf-8-sig", errors="replace").encode("ascii", errors="backslashreplace").decode())

import csv
import io
import pandas as pd

data = json.loads((ROOT / "cpi.json/response.bin").read_bytes())
print("ONS keys", list(data))
print("ONS description", json.dumps(data.get("description"), ensure_ascii=True))
print("ONS months", len(data.get("months", [])), data.get("months", [])[:1], data.get("months", [])[-1:])
hpi = pd.read_csv(ROOT / "hpi.csv/response.bin", dtype=str, keep_default_na=False)
print("HPI", hpi.shape, hpi.Date.min(), hpi.Date.max(), hpi.AreaCode.nunique(), hpi.head(2).to_json(orient="records"))
rows = list(csv.reader(io.StringIO((ROOT / "revisions.csv/response.bin").read_text(encoding="utf-8-sig"), newline="")))
print("Revision first cells", [(i, row[:4]) for i, row in enumerate(rows) if row and any(row)][:24])
print("Revision sections/tail", [(i, row[:3]) for i, row in enumerate(rows) if row and row[0] and not row[0][0].isdigit()], rows[-2:][0][:5])
dates = pd.to_datetime(hpi.Date, format="%d/%m/%Y")
print("HPI date bounds", dates.min(), dates.max(), "base samples", hpi.loc[hpi.Date.eq("01/01/2015"), ["RegionName","Index"]].head().to_dict("records"))
print("ONS versions", json.dumps(data['versions'][:2], ensure_ascii=True), "sourceDatasets", data['sourceDatasets'])
print("ONS latest versions", data['versions'][-2:])
reference = pd.read_csv('configs/ons_lad_apr2025_v2.csv', dtype=str)
eligible=reference.loc[reference.target_eligible.eq('true')]
matched=set(eligible.gss_code) & set(hpi.AreaCode)
print("HPI cohort matches", len(matched), "unmatched", eligible.loc[~eligible.gss_code.isin(matched), ['gss_code','local_authority_name']].to_dict('records'))
print("HPI names mismatches",hpi.loc[hpi.AreaCode.isin(matched), ['AreaCode','RegionName']].drop_duplicates().merge(eligible,left_on='AreaCode',right_on='gss_code').query('RegionName != local_authority_name')[['AreaCode','RegionName','local_authority_name']].to_dict('records'))
for candidate in Path("data/raw/task008_audit").rglob("response.bin"):
    if candidate.parent.name in {"AveragePrice", "Index"}:
        print("Comparison CSV schema", candidate.parent.name, candidate.open(encoding="utf-8-sig").readline().strip())
