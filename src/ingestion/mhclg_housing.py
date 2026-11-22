"""Immutable MHCLG housing source capture; preserve native ODS values and quality."""

from __future__ import annotations
import argparse
import http.client
import io
import json
import logging
import math
import re
import time
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

import pandas as pd
from ingestion.boe import IngestionError, publish, safe_http_headers, sha, verify_bundle
from ingestion.ons_pipr import load_geography_reference
from ingestion.source_io import identifier, publish_tables, storage_root

DATASET = "mhclg_housing"
VERSION = "mhclg-housing-v1"
USER_AGENT = "RentalForecasting-MHCLG/1.0 (public aggregate statistics)"
LOG = logging.getLogger(__name__)
PAGES = {
    "supply_page": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-net-supply-of-housing",
    "stock_page": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants",
    "terms": "https://www.gov.uk/help/terms-conditions",
    "robots": "https://www.gov.uk/robots.txt",
}
NS = {
    "o": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "x": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "s": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "f": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
}


def attr(node, prefix, name, default=None):
    return node.attrib.get("{" + NS[prefix] + "}" + name, default)


def source_url(url):
    p = urlsplit(url)
    if p.scheme != "https" or p.query or p.fragment or p.username or p.password:
        raise IngestionError("Expected unauthenticated official MHCLG HTTPS URL")
    if p.netloc == "www.gov.uk":
        if url not in PAGES.values():
            raise IngestionError("Unexpected MHCLG document URL")
    elif p.netloc == "assets.publishing.service.gov.uk":
        if not re.fullmatch(
            r"/media/[A-Za-z0-9_-]+/(Live_Table_12[23]|LiveTable125)[.]ods", p.path
        ):
            raise IngestionError("Unexpected MHCLG ODS asset identity")
    else:
        raise IngestionError("Unofficial MHCLG host")
    return url


def fetch(url: str, *, sleep=time.sleep, opener=urlopen) -> tuple[bytes, dict]:
    """Serial caller; bounded retries honour seconds/date Retry-After up to 60s.

    A longer publisher wait stops this invocation rather than retrying early.
    HTTP 403 is terminal. No credentials or session headers are stored.
    """
    source_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    attempts = []
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with opener(Request(url, headers=headers), timeout=60) as response:
                source_url(response.url)
                if response.status != 200:
                    raise IngestionError("Unexpected source response status")
                body = response.read(32_000_001)
                length = response.headers.get("Content-Length")
                if (
                    not body
                    or len(body) > 32_000_000
                    or (length and int(length) != len(body))
                ):
                    raise IngestionError(
                        "Empty, oversized or incomplete MHCLG response"
                    )
                return body, dict(
                    url=url,
                    resolved_url=response.url,
                    status=200,
                    request_headers=headers,
                    response_headers=safe_http_headers(response.headers),
                    retrieval_started_at=started,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    prior_attempts=attempts,
                )
        except (OSError, URLError, http.client.HTTPException) as exc:
            status = exc.code if isinstance(exc, HTTPError) else None
            wait = 2**attempt
            record = dict(
                status=status,
                retrieval_started_at=started,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
            if isinstance(exc, HTTPError):
                record["response_headers"] = safe_http_headers(exc.headers)
                retry = exc.headers.get("Retry-After")
                exc.close()
                if status not in {429, 500, 502, 503, 504}:
                    raise IngestionError(
                        f"MHCLG access denied/failed: HTTP {status}"
                    ) from exc
                if retry:
                    try:
                        wait = (
                            int(retry)
                            if retry.isdigit()
                            else math.ceil(
                                (
                                    parsedate_to_datetime(retry)
                                    - datetime.now(timezone.utc)
                                ).total_seconds()
                            )
                        )
                        wait = max(0, wait)
                    except (TypeError, ValueError, OverflowError) as error:
                        raise IngestionError(
                            "Invalid publisher Retry-After; stop"
                        ) from error
                    if wait > 60:
                        raise IngestionError(
                            "Publisher Retry-After exceeds 60s; stop and resume later"
                        ) from exc
            attempts.append(record)
            if attempt == 2:
                raise IngestionError(
                    "MHCLG download failed after three attempts"
                ) from exc
            LOG.warning(
                "Retrying MHCLG source after %s seconds (attempt %s/3)",
                wait,
                attempt + 1,
            )
            sleep(wait)
    raise AssertionError("unreachable")


def acquire(root, snapshot, name, url, downloader=fetch):
    source_url(url)
    directory = (
        root / "raw" / DATASET / f"snapshot={identifier(snapshot)}" / identifier(name)
    )
    identity = dict(dataset=DATASET, snapshot_id=snapshot, source=name, url=url)
    if directory.exists():
        meta = verify_bundle(directory)
        if meta.get("identity") != identity:
            raise IngestionError("Immutable MHCLG request conflict")
    else:
        time.sleep(1.0)
        body, meta = downloader(url)
        if not body or meta.get("status") != 200 or not meta.get("retrieved_at"):
            raise IngestionError("Failed/incomplete MHCLG source response")
        publish(
            directory,
            {"response.bin": body},
            dict(identity=identity, retrieval=meta, source_sha256=sha(body)),
        )
        meta = verify_bundle(directory)
    body = (directory / "response.bin").read_bytes()
    if meta.get("source_sha256") != sha(body):
        raise IngestionError("MHCLG raw checksum metadata conflict")
    return body, meta


def ods_document(body):
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            if (
                archive.read("mimetype")
                != b"application/vnd.oasis.opendocument.spreadsheet"
            ):
                raise ValueError("ODS mimetype")
            if sum(i.file_size for i in archive.infolist()) > 128_000_000:
                raise ValueError("Oversized decompressed ODS")
            content = ET.fromstring(archive.read("content.xml"))
            style = ET.fromstring(archive.read("styles.xml"))
        return content, style
    except (ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise IngestionError("Invalid MHCLG ODS source") from exc


def ods_text(node):
    if node.tag == "{" + NS["x"] + "}s":
        count = int(attr(node, "x", "c", "1"))
        if not 1 <= count <= 4096:
            raise IngestionError("Unexpected repeated ODS text spacing")
        return " " * count
    if node.tag == "{" + NS["x"] + "}tab":
        return "\t"
    if node.tag == "{" + NS["x"] + "}line-break":
        return "\n"
    return (node.text or "") + "".join(
        ods_text(child) + (child.tail or "") for child in node
    )


def sparse_rows(table, width=None):
    """Expand only actual cells; empty repeated trailing grids never allocate."""
    rn = 1
    for row in table.findall(".//t:table-row", NS):
        repeat = int(attr(row, "t", "number-rows-repeated", "1"))
        cells = {}
        cn = 1
        if not 1 <= repeat <= 1_048_576:
            raise IngestionError("Invalid ODS repeated row count")
        for cell in row:
            if cell.tag not in {
                "{" + NS["t"] + "}table-cell",
                "{" + NS["t"] + "}covered-table-cell",
            }:
                continue
            count = int(attr(cell, "t", "number-columns-repeated", "1"))
            if not 1 <= count <= 16384:
                raise IngestionError("Invalid ODS repeated column count")
            text = "\n".join(ods_text(p) for p in cell.findall("x:p", NS))
            populated = bool(
                text
                or attr(cell, "o", "value") is not None
                or attr(cell, "t", "formula")
            )
            if populated or (width is not None and cn <= width):
                if populated and cn + count > 4097:
                    raise IngestionError("Unexpected populated ODS width")
                for col in range(
                    cn,
                    min(
                        cn + count,
                        (
                            (width + 1)
                            if width is not None and not populated
                            else cn + count
                        ),
                    ),
                ):
                    cells[col] = (cell, text)
            cn += count
        if any(
            text or attr(cell, "o", "value") is not None or attr(cell, "t", "formula")
            for cell, text in cells.values()
        ):
            if repeat > 4096:
                raise IngestionError("Unexpected repeated populated rows")
            for offset in range(repeat):
                yield rn + offset, cells
        rn += repeat


def load_inventory(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if {s["table_id"] for s in data["sources"]} != {"122", "123", "125"} or len(
            data["sources"]
        ) != 3:
            raise ValueError("required tables")
        ids = set()
        urls = set()
        for source in data["sources"] + data.get("aliases", []):
            key = identifier(source["edition_id"])
            source_url(source["url"])
            if (
                key in ids
                or source["url"] in urls
                or not re.fullmatch("[a-f0-9]{64}", source["source_sha256"])
            ):
                raise ValueError("duplicate source/checksum")
            ids.add(key)
            urls.add(source["url"])
        for source in data["sources"]:
            if not source["tables"]:
                raise ValueError("missing source tables")
            sheets = [t["sheet"] for t in source["tables"]]
            if len(set(sheets)) != len(sheets):
                raise ValueError("duplicate sheets")
            for table in source["tables"]:
                if (
                    not table["title"]
                    or table["header_row"] < 1
                    or not table["column_labels"]
                ):
                    raise ValueError("source schema")
        for name, doc in data["documents"].items():
            identifier(name)
            source_url(doc["url"])
        return data
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise IngestionError("Invalid MHCLG source inventory") from exc


def financial_year(label):
    match = re.match(r"^(20[0-9]{2})-([0-9]{2})(?:$| )", label)
    if match is None or (int(match[1]) + 1) % 100 != int(match[2]):
        raise IngestionError("Invalid source financial year")
    year = int(match[1])
    return f"{year}-{year+1}", f"{year}-04-01", f"{year+1}-03-31", year + 1


def style_catalogue(content, styles):
    definitions = {}
    default = {}
    records = []
    for origin, root in (("styles.xml", styles), ("content.xml", content)):
        for container in list(root):
            if container.tag not in {
                "{" + NS["o"] + "}styles",
                "{" + NS["o"] + "}automatic-styles",
            }:
                continue
            for node in container:
                name = attr(node, "s", "name")
                if name is not None:
                    records.append(
                        dict(
                            style_name=name,
                            style_family=attr(node, "s", "family", ""),
                            origin=origin,
                            style_xml=ET.tostring(node, encoding="unicode"),
                        )
                    )
                if (
                    node.tag == "{" + NS["s"] + "}style"
                    and attr(node, "s", "family") == "table-cell"
                ):
                    definitions[name] = node
                if (
                    node.tag == "{" + NS["s"] + "}default-style"
                    and attr(node, "s", "family") == "table-cell"
                ):
                    default = {
                        child.tag.split("}")[-1]: dict(child.attrib) for child in node
                    }
    cache = {}

    def resolve(name, seen=None):
        if name in cache:
            return cache[name]
        if not name:
            return {k: dict(v) for k, v in default.items()}
        if name not in definitions:
            raise IngestionError("Unknown ODS source cell style")
        seen = set() if seen is None else set(seen)
        if name in seen:
            raise IngestionError("Cyclic source style inheritance")
        seen.add(name)
        node = definitions[name]
        props = resolve(attr(node, "s", "parent-style-name", ""), seen)
        props = {k: dict(v) for k, v in props.items()}
        for child in node:
            props.setdefault(child.tag.split("}")[-1], {}).update(child.attrib)
        cache[name] = props
        return props

    return resolve, records


def default_styles(table, width):
    columns = {}
    cn = 1
    row_defaults = {}
    rn = 1
    populated_rows = {r for r, _ in sparse_rows(table)}
    for column in table.findall(".//t:table-column", NS):
        count = int(attr(column, "t", "number-columns-repeated", "1"))
        style = attr(column, "t", "default-cell-style-name", "")
        for col in range(cn, min(cn + count, width + 1)):
            columns[col] = style
        cn += count
    for row in table.findall(".//t:table-row", NS):
        count = int(attr(row, "t", "number-rows-repeated", "1"))
        style = attr(row, "t", "default-cell-style-name", "")
        if style:
            for actual_row in populated_rows:
                if rn <= actual_row < rn + count:
                    row_defaults[actual_row] = style
        rn += count
    return columns, row_defaults


def cell_value(cell, text):
    from decimal import Decimal, InvalidOperation

    raw = attr(cell, "o", "value") if cell is not None else None
    kind = attr(cell, "o", "value-type", "") if cell is not None else ""
    if kind == "float":
        if raw is None:
            raise IngestionError("Numeric ODS cell lacks its source value")
        try:
            number = Decimal(raw)
            if not number.is_finite() or not math.isfinite(float(number)):
                raise ValueError("non-finite")
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise IngestionError("Invalid MHCLG source number") from exc
        return float(number), "numeric", raw
    if kind in {"currency", "percentage", "date", "time", "boolean"}:
        raise IngestionError("Unexpected source value type for dwelling count")
    return None, "missing" if not text else "source_marker", text


def measure_name(header):
    label = " ".join(header.split()).casefold()
    known = {
        "new build": "new_build_completions",
        "net additions": "net_additional_dwellings",
        "net conversions": "net_conversions",
        "net change of use": "net_change_of_use",
        "net other gains and losses": "net_other_gains_and_losses",
        "demolitions": "demolitions",
        "adjustment to census 2021": "census_2021_adjustment",
    }
    if label in known:
        return known[label]
    if label == "of which under pdr":
        return "of_which_under_pdr_unspecified_source_label"
    if label.startswith("of which under pdr:"):
        return re.sub("[^a-z0-9]+", "_", label).strip("_")
    raise IngestionError("Unexpected Table 123 component definition")


def parse_source(body, source, provenance, cohort):
    content, styles = ods_document(body)
    resolve, style_records = style_catalogue(content, styles)
    source_id = source["edition_id"]
    table_id = source["table_id"]
    tables = {attr(t, "t", "name"): t for t in content.findall(".//t:table", NS)}
    expected = {t["sheet"] for t in source["tables"]}
    if not expected <= set(tables):
        raise IngestionError("Expected MHCLG worksheet missing")
    notes = []
    schema = []
    observations = []
    global_text = "\n".join(
        text
        for table in tables.values()
        for _, cells in sparse_rows(table)
        for _, text in cells.values()
    )
    red_definition = (
        table_id == "123" and "Cells filled in red are imputed figures." in global_text
    )
    note_lookup = {}
    if "Notes" in tables:
        for _, cells in sparse_rows(tables["Notes"]):
            marker = cells.get(1, (None, ""))[1]
            text = cells.get(2, (None, ""))[1]
            if marker.startswith("["):
                note_lookup[marker] = text
    for sn, table in tables.items():
        if sn in expected:
            continue
        for rn, cells in sparse_rows(table):
            for cn, (cell, text) in cells.items():
                notes.append(
                    dict(
                        edition_id=source_id,
                        source_sheet=sn,
                        source_row=rn,
                        source_column=cn,
                        text=text,
                        source_style_name=attr(cell, "t", "style-name", ""),
                        source_cell_xml=ET.tostring(cell, encoding="unicode"),
                    )
                )
    for contract in source["tables"]:
        sn = contract["sheet"]
        table = tables[sn]
        hr = contract["header_row"]
        width = max(map(int, contract["column_labels"]))
        rows = list(sparse_rows(table, width=width))
        row_map = dict(rows)
        if row_map.get(1, {}).get(1, (None, ""))[1] != contract["title"]:
            raise IngestionError("MHCLG source table title changed")
        headers = {str(c): text for c, (_, text) in row_map.get(hr, {}).items() if text}
        if headers != contract["column_labels"]:
            raise IngestionError("MHCLG header schema changed")
        code_col, name_col = (2, 3) if table_id == "125" else (3, 4)
        if "ONS code" not in headers[str(code_col)].replace("\n", " "):
            raise IngestionError("Source geography field changed")
        selected = {}
        for col, label in headers.items():
            col = int(col)
            if col <= name_col or label == "Notes":
                continue
            if table_id == "123":
                period, start, end, year = financial_year(sn)
                measure = measure_name(label)
                refdate = ""
            elif table_id == "122":
                period, start, end, year = financial_year(label)
                measure = "net_additional_dwellings"
                refdate = ""
            else:
                match = re.fullmatch(r"(20[0-9]{2})(?: .*)?", label)
                if match is None:
                    raise IngestionError("Invalid stock reference year")
                year = int(match[1])
                period = str(year)
                start = end = ""
                refdate = f"{year}-03-31"
                measure = (
                    "dwelling_stock_unrounded"
                    if sn.endswith("unrounded")
                    else "dwelling_stock_rounded"
                )
            selected[col] = (measure, period, start, end, year, refdate, label)
        if (
            not selected
            or table_id == "123"
            and "new_build_completions" not in {x[0] for x in selected.values()}
        ):
            raise IngestionError("Required MHCLG source measure absent")
        if len({(x[0], x[1]) for x in selected.values()}) != len(selected):
            raise IngestionError("Duplicate source measure/period column")
        cols, defaults = default_styles(table, width)
        seen = set()
        records = 0
        sheet_preamble = "\n".join(
            text for rn, cells in rows if rn < hr for _, text in cells.values()
        )
        for rn, cells in rows:
            if rn <= hr:
                for cn, (cell, text) in cells.items():
                    if text:
                        notes.append(
                            dict(
                                edition_id=source_id,
                                source_sheet=sn,
                                source_row=rn,
                                source_column=cn,
                                text=text,
                                source_style_name=attr(cell, "t", "style-name", ""),
                                source_cell_xml=ET.tostring(cell, encoding="unicode"),
                            )
                        )
                continue
            code = cells.get(code_col, (None, ""))[1]
            name = cells.get(name_col, (None, ""))[1]
            has_values = any(
                c in cells
                and (cells[c][1] or attr(cells[c][0], "o", "value") is not None)
                for c in selected
            )
            if not name or not has_values:
                for cn, (cell, text) in cells.items():
                    if text:
                        notes.append(
                            dict(
                                edition_id=source_id,
                                source_sheet=sn,
                                source_row=rn,
                                source_column=cn,
                                text=text,
                                source_style_name=attr(cell, "t", "style-name", ""),
                                source_cell_xml=ET.tostring(cell, encoding="unicode"),
                            )
                        )
                continue
            if code:
                if not re.fullmatch("E[0-9]{8}", code):
                    raise IngestionError("Unexpected original MHCLG geography code")
                if code in seen:
                    raise IngestionError("Duplicate MHCLG geography observation")
                seen.add(code)
            records += 1
            row_note = (
                cells.get(width, (None, ""))[1]
                if headers[str(width)] == "Notes"
                else ""
            )
            name_markers = re.findall(r"\[[^]]+\]", name + " " + row_note)
            note1 = (
                table_id == "123"
                and "[note 1]" in name_markers
                and "imputed" in note_lookup.get("[note 1]", "")
            )
            former = cells.get(1 if table_id == "125" else 2, (None, ""))[1]
            dclg = "" if table_id == "125" else cells.get(1, (None, ""))[1]
            level = (
                "published_GSS_coded_area"
                if code
                else (
                    "published_legacy_coded_area"
                    if former or dclg
                    else "published_aggregate_without_GSS_code"
                )
            )
            for cn, (
                measure,
                period,
                start,
                end,
                year,
                refdate,
                label,
            ) in selected.items():
                cell, text = cells.get(cn, (None, ""))
                value, kind, value_text = cell_value(cell, text)
                raw_style = (
                    attr(cell, "t", "style-name", "") if cell is not None else ""
                )
                effective = raw_style or defaults.get(rn, "") or cols.get(cn, "")
                props = resolve(effective)
                background = props.get("table-cell-properties", {}).get(
                    "{" + NS["f"] + "}background-color", ""
                )
                red = background.casefold() == "#ff0000"
                imputed = True if note1 or (red and red_definition) else None
                marks = re.findall(
                    r"\[[^]]+\]",
                    label
                    + " "
                    + contract["title"]
                    + " "
                    + name
                    + " "
                    + text
                    + " "
                    + row_note,
                )
                related = {
                    m: note_lookup[m] for m in sorted(set(marks)) if m in note_lookup
                }
                flags = [
                    "native_source_geography_no_mapping",
                    "historical_availability_unverified",
                ]
                if (
                    table_id == "123"
                    and any("2023-24" in v for k, v in related.items() if k == "[p]")
                    and sn == "2024-25"
                ):
                    flags.append("publisher_provisional_note_year_differs_from_sheet")
                if table_id == "123" and "[r]" in related:
                    years = re.findall(r"20[0-9]{2}-[0-9]{2}", related["[r]"])
                    if years and sn not in years:
                        flags.append("publisher_revised_note_year_differs_from_sheet")
                if (
                    table_id == "125"
                    and sn.endswith("unrounded")
                    and "nearest ten" in sheet_preamble
                ):
                    flags.append("unrounded_sheet_carries_rounded_wording")
                observations.append(
                    dict(
                        edition_id=source_id,
                        table_id=table_id,
                        source_sheet=sn,
                        source_row=rn,
                        source_column=cn,
                        source_code=code,
                        source_name=name,
                        former_ons_code=former,
                        dclg_code=dclg,
                        source_geography_type=level,
                        measure=measure,
                        period=period,
                        source_period_label=(
                            label if table_id != "123" else contract["title"]
                        ),
                        reference_year=year,
                        period_start=start,
                        period_end=end,
                        reference_date=refdate,
                        unit="dwellings",
                        value=value,
                        value_kind=kind,
                        source_value_text=value_text,
                        source_display_text=text,
                        source_xml_value=(
                            attr(cell, "o", "value", "") if cell is not None else ""
                        ),
                        source_value_type=(
                            attr(cell, "o", "value-type", "")
                            if cell is not None
                            else ""
                        ),
                        source_formula=(
                            attr(cell, "t", "formula", "") if cell is not None else ""
                        ),
                        source_header=label,
                        source_cell_style_name=raw_style,
                        effective_style_name=effective,
                        effective_style_properties_json=json.dumps(
                            props, sort_keys=True
                        ),
                        source_row_default_style=defaults.get(rn, ""),
                        source_column_default_style=cols.get(cn, ""),
                        source_background_color=background,
                        source_cell_xml=(
                            ET.tostring(cell, encoding="unicode")
                            if cell is not None
                            else ""
                        ),
                        source_row_note_text=row_note,
                        source_markers_json=json.dumps(marks),
                        related_note_text_json=json.dumps(related, sort_keys=True),
                        publisher_imputation_row_note=bool(note1),
                        publisher_red_fill=red,
                        publisher_red_imputation_definition=red_definition,
                        publisher_imputation_flag=imputed,
                        imputation_mentioned_in_related_notes=any(
                            "imput" in v.lower() for v in related.values()
                        ),
                        future_denominator_candidate=measure
                        == "dwelling_stock_unrounded",
                        exact_cohort_code_match=code in cohort,
                        flags_json=json.dumps(flags),
                        source_url=source["url"],
                        source_sha256=provenance["source_sha256"],
                        retrieved_at=provenance["retrieval"]["retrieved_at"],
                        source_snapshot_id=provenance["identity"]["snapshot_id"],
                    )
                )
        if not records:
            raise IngestionError("No MHCLG source geography records")
        schema.append(
            dict(
                edition_id=source_id,
                table_id=table_id,
                source_sheet=sn,
                title=contract["title"],
                header_row=hr,
                column_labels_json=json.dumps(headers),
                source_area_rows=records,
                periods_json=json.dumps(sorted({x[1] for x in selected.values()})),
            )
        )
    return (
        observations,
        notes,
        [dict(edition_id=source_id, **r) for r in style_records],
        schema,
    )


def audits(frame, cohort):
    coverage = []
    geo = []
    for (edition, sheet, measure, period), group in frame.groupby(
        ["edition_id", "source_sheet", "measure", "period"], sort=True
    ):
        matched = group[group.exact_cohort_code_match]
        coverage.append(
            dict(
                edition_id=edition,
                source_sheet=sheet,
                measure=measure,
                period=period,
                source_area_rows=len(group),
                source_GSS_codes=group.loc[
                    group.source_code.ne(""), "source_code"
                ].nunique(),
                exact_cohort_matches=len(matched),
                numeric_cohort_values=int(matched.value.notna().sum()),
                numeric_source_values=int(group.value.notna().sum()),
                source_markers_json=json.dumps(
                    group.value_kind.value_counts().to_dict(), sort_keys=True
                ),
                unmatched_target_codes_json=json.dumps(
                    sorted(set(cohort) - set(group.source_code))
                ),
                unmatched_source_codes_json=json.dumps(
                    sorted(set(group.source_code) - set(cohort) - {""})
                ),
                missing_numeric_cohort_codes_json=json.dumps(
                    sorted(matched.loc[matched.value.isna(), "source_code"])
                ),
                imputation_indicator_cells=int(
                    group.publisher_imputation_flag.fillna(False).sum()
                ),
            )
        )
    for (edition, sheet), group in frame.groupby(
        ["edition_id", "source_sheet"], sort=True
    ):
        for r in (
            group[
                [
                    "source_row",
                    "source_code",
                    "source_name",
                    "former_ons_code",
                    "dclg_code",
                    "source_geography_type",
                ]
            ]
            .drop_duplicates()
            .to_dict("records")
        ):
            geo.append(
                dict(
                    edition_id=edition,
                    source_sheet=sheet,
                    **r,
                    exact_cohort_code_match=r["source_code"] in cohort,
                    reference_name=cohort.get(r["source_code"], ""),
                    mapping_applied=False,
                )
            )
    return pd.DataFrame(coverage), pd.DataFrame(geo)


def ingest(
    root,
    snapshot,
    *,
    inventory=Path("configs/mhclg_housing_sources.json"),
    reference=Path("configs/ons_lad_apr2025_v2.csv"),
    downloader=fetch,
):
    identifier(snapshot)
    contract = load_inventory(inventory)
    cohort = load_geography_reference(reference).eligible_names
    identity = dict(
        dataset=DATASET,
        snapshot_id=snapshot,
        inventory_sha256=sha(inventory.read_bytes()),
        geography_reference_sha256=sha(reference.read_bytes()),
        transformation_version=VERSION,
    )
    for layer in ("validated", "processed"):
        target = root / layer / DATASET / f"snapshot={snapshot}"
        if target.exists() and verify_bundle(target).get("identity") != identity:
            raise IngestionError("Immutable MHCLG output identity conflict")
    sources = {}
    documents = []
    records = []
    notes = []
    style_records = []
    schema = []
    for key, doc in contract["documents"].items():
        body, meta = acquire(root, snapshot, key, doc["url"], downloader)
        sources[key] = meta
        if sha(body) != doc["source_sha256"]:
            raise IngestionError("Investigated MHCLG source document changed")
        documents.append(
            dict(
                source=key,
                url=doc["url"],
                source_sha256=sha(body),
                retrieved_at=meta["retrieval"]["retrieved_at"],
                content=body.decode("utf-8-sig"),
            )
        )
    if not any(
        "Open Government Licence" in d["content"]
        for d in documents
        if d["source"] == "terms"
    ):
        raise IngestionError("MHCLG licence evidence requires review")
    for source in contract["sources"] + contract.get("aliases", []):
        body, meta = acquire(
            root, snapshot, source["edition_id"], source["url"], downloader
        )
        sources[source["edition_id"]] = meta
        if sha(body) != source["source_sha256"]:
            raise IngestionError(
                "Investigated MHCLG workbook changed; preserve snapshot/contract"
            )
        if "equivalent_primary" in source:
            if source["source_sha256"] != next(
                x["source_sha256"]
                for x in contract["sources"]
                if x["edition_id"] == source["equivalent_primary"]
            ):
                raise IngestionError("MHCLG attachment aliases are not identical")
            continue
        cells, annotations, styles, structure = parse_source(body, source, meta, cohort)
        records.extend(cells)
        notes.extend(annotations)
        style_records.extend(styles)
        schema.extend(structure)
    frame = (
        pd.DataFrame(records)
        .sort_values(["edition_id", "source_sheet", "source_row", "source_column"])
        .reset_index(drop=True)
    )
    if frame.duplicated(
        ["edition_id", "source_sheet", "source_row", "measure", "period"]
    ).any():
        raise IngestionError("Duplicate MHCLG source observation")
    frame["value"] = pd.to_numeric(frame.value).astype("float64")
    frame["publisher_imputation_flag"] = frame.publisher_imputation_flag.astype(
        "boolean"
    )
    coverage, geography = audits(frame, cohort)
    tables = dict(
        observations=frame,
        coverage=coverage,
        geography_audit=geography,
        notes=pd.DataFrame(notes),
        styles=pd.DataFrame(style_records),
        schema=pd.DataFrame(schema),
        documents=pd.DataFrame(documents),
    )
    info = dict(
        identity=identity,
        sources=sources,
        source_contract=contract,
        validation=dict(
            source_workbooks=len(contract["sources"]),
            attachment_aliases=len(contract.get("aliases", [])),
            observations=len(frame),
            source_sheets=len(schema),
            numeric_cells=int(frame.value.notna().sum()),
            imputation_indicator_cells=int(
                frame.publisher_imputation_flag.fillna(False).sum()
            ),
        ),
        geography_policy="Original current/former/DCLG identifiers and row identity; no maps",
        stock_denominator_timing="Unselected; source stock dates retained; no ratios",
        source_vintage_policy="Separate immutable source bytes; no modelling vintage or exact historic availability claim",
        exact_point_in_time=False,
        licence="Crown copyright / MHCLG; Open Government Licence v3.0 with attribution and exceptions",
        imputation_policy="Explicit Table 123 row note/red-fill indicators retained; no signal is null, not proof of no imputation. Narrative period notes retained without applying imputation to every authority.",
    )
    return publish_tables(root, DATASET, snapshot, tables, tables, info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    parser.add_argument(
        "--inventory", type=Path, default=Path("configs/mhclg_housing_sources.json")
    )
    parser.add_argument(
        "--geography-reference",
        type=Path,
        default=Path("configs/ons_lad_apr2025_v2.csv"),
    )
    args = parser.parse_args()
    info = ingest(
        storage_root(args.config),
        args.snapshot_id,
        inventory=args.inventory,
        reference=args.geography_reference,
    )
    print(
        json.dumps(
            {
                "dataset": DATASET,
                "snapshot_id": args.snapshot_id,
                "validation": info["validation"],
                "processed_path": info["processed_path"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
