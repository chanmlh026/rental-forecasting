"""Discover approved official planning assets; reuse immutable bundles on resume."""

import csv
import io
import json
from html.parser import HTMLParser
from pathlib import Path
from ingestion.mhclg_planning import acquire, PAGE, RELEASE

ROOT = Path("data")
SNAPSHOT = "2026-11-22-task012"
OUT = Path("reports/data_audits/012")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(
                v
                for k, v in attrs
                if k == "href"
                and v
                and v.startswith("https://assets.publishing.service.gov.uk/media/")
            )


def main():
    documents = {}
    for name, url in [
        ("terms", "https://www.gov.uk/help/terms-conditions"),
        ("robots", "https://www.gov.uk/robots.txt"),
        ("page", PAGE),
        ("release", RELEASE),
        (
            "technical_notes",
            RELEASE
            + "/planning-applications-in-england-april-to-june-2026-technical-notes",
        ),
        (
            "statistical_release",
            RELEASE
            + "/planning-applications-in-england-april-to-june-2026-statistical-release",
        ),
    ]:
        body, meta = acquire(ROOT, SNAPSHOT, name, url)
        documents[name] = dict(url=url, source_sha256=meta["source_sha256"])
        if name == "page":
            page = body
    parser = Links()
    parser.feed(page.decode("utf-8"))
    sources = []
    findings = []
    for table in ["PS1", "PS2"]:
        for kind in ["full", "recent"]:
            urls = sorted(
                set(
                    u
                    for u in parser.links
                    if "/" + table + "_data_" in u
                    and u.endswith(".csv")
                    and ("last_four" in u) == (kind == "recent")
                )
            )
            if len(urls) != 1:
                raise ValueError("Ambiguous official CSV links: " + repr(urls))
            url = urls[0]
            name = table.lower() + "_" + kind
            body, meta = acquire(ROOT, SNAPSHOT, name, url)
            reader = csv.reader(io.StringIO(body.decode("cp1252")))
            preamble = []
            for columns in reader:
                if columns[:4] == ["Region", "LPANM", "LPACD", "Quarter"]:
                    break
                preamble.append(columns)
                if len(preamble) > 10:
                    raise ValueError("Planning CSV header not found")
            else:
                raise ValueError("Planning CSV header not found")
            count = 0
            periods = set()
            first = None
            last = None
            for row in reader:
                count += 1
                first = first or row
                last = row
                periods.add(row[3])
            sources.append(
                dict(
                    edition_id=name,
                    table=table,
                    kind=kind,
                    url=url,
                    source_sha256=meta["source_sha256"],
                    columns=columns,
                    preamble=preamble,
                )
            )
            finding = dict(
                edition_id=name,
                bytes=len(body),
                rows=count,
                columns=len(columns),
                first=first[:12],
                last=last[:12],
                first_column_values=sorted(periods),
            )
            findings.append(finding)
            print(
                name,
                "rows",
                count,
                "columns",
                len(columns),
                "preamble_rows",
                len(preamble),
                "periods",
                min(periods),
                max(periods),
                flush=True,
            )
    url = next(
        u for u in parser.links if u.endswith("/District_Matters_-_Data_dictionary.pdf")
    )
    body, meta = acquire(ROOT, SNAPSHOT, "district_dictionary", url)
    documents["district_dictionary"] = dict(
        url=url, source_sha256=meta["source_sha256"]
    )
    contract = dict(
        dataset="MHCLG PS1/PS2 district planning statistics",
        documents=documents,
        sources=sources,
    )
    Path("configs/mhclg_planning_sources.json").write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "source-investigation.json").write_text(
        json.dumps(findings, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
