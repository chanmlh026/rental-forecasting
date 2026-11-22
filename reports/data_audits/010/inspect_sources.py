"""Discover and inspect advertised, relevant ONS editions without selecting vintages."""

import io
import json
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urljoin, urlencode
import openpyxl
from ingestion.ons_population import CATALOGUE, SOURCE_PATH, DATASET, offline_fetch
from ingestion.source_io import raw_source

ROOT = Path("data")
SNAPSHOT = "2026-11-22-task010"
OUT = Path("reports/data_audits/010")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href:
                self.links.append(urljoin("https://www.ons.gov.uk", href))


def main():
    sources = {}
    documents = {}
    excluded = []
    pending = []
    for name, suffix in [
        ("catalogue", ""),
        ("versions_summary2022_2023", "/mid20222023localauthorityboundaires"),
        ("versions_summary2022_2021", "/mid20222021localauthorityboundaires"),
        ("versions_detail2022", "/mid2011tomid2022detailedtimeseries"),
    ]:
        body, meta = raw_source(
            ROOT, DATASET, SNAPSHOT, name, CATALOGUE + suffix, downloader=offline_fetch
        )
        documents[name] = dict(
            url=CATALOGUE + suffix, source_sha256=meta["source_sha256"]
        )
        parser = Links()
        parser.feed(body.decode("utf-8"))
        for url in parser.links:
            uri = parse_qs(urlsplit(url).query).get("uri", [""])[0]
            if not uri.startswith(SOURCE_PATH + "/") or not uri.endswith(".xlsx"):
                continue
            url = "https://www.ons.gov.uk/file?" + urlencode({"uri": uri})
            parts = uri[len(SOURCE_PATH) + 1 :].split("/")
            edition = parts[0]
            if edition.startswith("mid2011tomid"):
                year = next(y for y in (2022, 2023, 2024, 2025) if str(y) in edition)
                key = f"detail{year}"
                kind = "detail"
            elif edition.startswith("mid202") and "localauthority" in edition:
                year = int(edition[3:7])
                geo = "2021" if "2021localauthority" in edition else "2023"
                key = f"summary{year}" + ("_" + geo if year == 2022 else "")
                kind = "summary"
            else:
                excluded.append(
                    dict(
                        url=url,
                        reason="National/regional-only or pre-2011 series outside this forecasting-history source contract",
                    )
                )
                continue
            if "/previous/" in uri:
                key += "_previous_" + parts[parts.index("previous") + 1]
            # Pages sometimes advertise a byte-identical URL more than once.
            if key in sources and sources[key]["url"] != url:
                raise ValueError("Ambiguous official edition ID: " + key)
            sources.setdefault(
                key,
                dict(
                    edition_id=key,
                    kind=kind,
                    url=url,
                    edition_slug=edition,
                    latest_reference_year=year,
                    evidence_pages=[],
                ),
            )["evidence_pages"].append(name)
    for name, url in [
        (
            "bulletin2025",
            "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/bulletins/populationestimatesforenglandandwales/mid2025",
        ),
        ("licence", "https://www.ons.gov.uk/help/terms-conditions"),
        ("fair_use", "https://www.ons.gov.uk/help/fair-use-policy"),
    ]:
        body, meta = raw_source(
            ROOT, DATASET, SNAPSHOT, name, url, downloader=offline_fetch
        )
        documents[name] = dict(url=url, source_sha256=meta["source_sha256"])
    inventory = []
    for key, e in sources.items():
        print("Acquire/verify", key, flush=True)
        if not (ROOT / "raw" / DATASET / f"snapshot={SNAPSHOT}" / key).exists():
            pending.append(
                {
                    **e,
                    "status": "Not acquired; owner-approved offline continuation; project contact approval required before download",
                }
            )
            continue
        body, meta = raw_source(
            ROOT, DATASET, SNAPSHOT, key, e["url"], downloader=offline_fetch
        )
        book = openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=True)
        tables = []
        notes = []
        for sheet in book:
            if sheet.title in {"MYE3", "MYE4", "MYE5"} or sheet.title.startswith(
                "MYEB3"
            ):
                top = list(sheet.iter_rows(min_row=1, max_row=12, values_only=True))
                hr = next(
                    (
                        i
                        for i, r in enumerate(top, 1)
                        if str(r[0]).lower() in {"code", "ladcode23", "ladcode21"}
                    ),
                    None,
                )
                tables.append(
                    dict(
                        sheet=sheet.title,
                        title=str(top[0][0]),
                        header_row=hr,
                        headers=(
                            [str(v) if v is not None else "" for v in top[hr - 1]]
                            if hr
                            else []
                        ),
                        rows=sheet.max_row,
                        columns=sheet.max_column,
                    )
                )
            elif sheet.title.lower() in {"cover sheet", "notes", "geography guide"}:
                notes.append(
                    dict(
                        sheet=sheet.title,
                        text=[
                            str(v)
                            for row in sheet.iter_rows(values_only=True)
                            for v in row
                            if v is not None
                        ],
                    )
                )
        e.update(
            source_sha256=meta["source_sha256"],
            size_bytes=len(body),
            sheets=book.sheetnames,
            tables=tables,
            notes=notes,
        )
        inventory.append(e)
        book.close()
        print(
            json.dumps(
                {k: v for k, v in e.items() if k not in {"notes", "tables"}},
                ensure_ascii=True,
            ),
            flush=True,
        )

        (OUT / "source-investigation.json").write_text(
            json.dumps(
                dict(
                    editions=inventory,
                    documents=documents,
                    excluded=excluded,
                    pending_downloads=pending,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    (OUT / "source-investigation.json").write_text(
        json.dumps(
            dict(
                editions=inventory,
                documents=documents,
                excluded=excluded,
                pending_downloads=pending,
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "Offline verified", len(inventory), "editions; pending downloads", len(pending)
    )


if __name__ == "__main__":
    main()
