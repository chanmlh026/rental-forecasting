"""Official MHCLG source discovery and retained ODS structure/style investigation."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from ingestion.mhclg_housing import (
    PAGES,
    DATASET,
    NS,
    ET,
    acquire,
    ods_document,
    sparse_rows,
    attr,
)

ROOT = Path("data")
SNAPSHOT = "2026-11-22-task011"
OUT = Path("reports/data_audits/011")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data):
        if self.href:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.links.append(
                (urljoin("https://www.gov.uk", self.href), " ".join(self.parts))
            )
            self.href = None


def main():
    docs = {}
    files = {}
    for name, url in PAGES.items():
        body, meta = acquire(ROOT, SNAPSHOT, name, url)
        docs[name] = dict(url=url, source_sha256=meta["source_sha256"])
        parser = Links()
        parser.feed(body.decode("utf-8"))
        for link, label in parser.links:
            for number in (122, 123, 125):
                if label.strip().startswith(f"Table {number}:"):
                    key = str(number) + (
                        "_stock_link"
                        if name == "stock_page" and number in (122, 123)
                        else ""
                    )
                    if key in files:
                        assert files[key]["url"] == link
                    files[key] = dict(
                        table_id=str(number),
                        url=link,
                        source_label=label.strip(),
                        source_page=name,
                        primary=(
                            name == "supply_page"
                            if number in (122, 123)
                            else name == "stock_page"
                        ),
                    )
    inventory = []
    for key, entry in files.items():
        name = "table" + key
        body, meta = acquire(ROOT, SNAPSHOT, name, entry["url"])
        content, styles = ods_document(body)
        tables = []
        for table in content.findall(".//t:table", NS):
            sn = attr(table, "t", "name")
            rows = list(sparse_rows(table))
            selected = []
            for rn, cells in rows:
                values = {str(col): text for col, (_, text) in cells.items()}
                if rn < 12 or any(
                    any(
                        k in text.lower()
                        for k in (
                            "imput",
                            "colour",
                            "color",
                            "highlight",
                            "provisional",
                            "revis",
                            "census",
                        )
                    )
                    for _, text in cells.values()
                ):
                    selected.append(dict(row=rn, values=values))
            tables.append(
                dict(sheet=sn, nonempty_rows=len(rows), inspected_rows=selected)
            )
            print(
                key,
                sn,
                "rows",
                len(rows),
                json.dumps(selected[:9], ensure_ascii=True),
                flush=True,
            )
        inventory.append(
            {
                **entry,
                "edition_id": name,
                "source_sha256": meta["source_sha256"],
                "size_bytes": len(body),
                "tables": tables,
            }
        )
    (OUT / "source-investigation.json").write_text(
        json.dumps(dict(documents=docs, sources=inventory), indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
