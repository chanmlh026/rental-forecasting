"""Versioned ONS population, published area/density and migration source capture."""

from __future__ import annotations

import argparse
import http.client
import io
import json
import logging
import math
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

import openpyxl
import pandas as pd

from ingestion.boe import safe_http_headers, sha, verify_bundle
from ingestion.ons_pipr import load_geography_reference
from ingestion.source_io import (
    IngestionError,
    identifier,
    publish_tables,
    raw_source,
    storage_root,
)

DATASET = "ons_population"
VERSION = "ons-population-v1"
SOURCE_PATH = "/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/estimatesofthepopulationforenglandandwales"
CATALOGUE = "https://www.ons.gov.uk" + SOURCE_PATH
USER_AGENT = "RentalForecasting-Population/1.0"
LOG = logging.getLogger(__name__)


def source_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "www.ons.gov.uk" or parsed.fragment:
        raise IngestionError("Expected official ONS HTTPS source")
    if parsed.path == "/file":
        values = parse_qs(parsed.query)
        uri = values.get("uri", [])
        if (
            set(values) != {"uri"}
            or len(uri) != 1
            or not uri[0].startswith(SOURCE_PATH + "/")
            or not uri[0].endswith(".xlsx")
            or ".." in uri[0].split("/")
        ):
            raise IngestionError("Expected ONS population workbook")
    elif (
        not (
            parsed.path.startswith(SOURCE_PATH)
            or parsed.path.startswith(
                "/peoplepopulationandcommunity/populationandmigration/populationestimates/bulletins/populationestimatesforenglandandwales/"
            )
            or parsed.path
            in {
                "/help/termsandconditions",
                "/help/terms-conditions",
                "/help/fairusepolicy",
                "/help/fair-use-policy",
            }
        )
        or parsed.query
    ):
        raise IngestionError("Unexpected ONS population source document")
    return url


def fetch(
    url: str, *, contact_url: str | None = None, sleep=time.sleep, opener=urlopen
) -> tuple[bytes, dict]:
    """Serial caller; bounded retries honour seconds/date Retry-After up to 60s.

    A longer publisher wait stops this invocation rather than retrying early.
    HTTP 403 is terminal. No credentials or session headers are stored.
    """
    source_url(url)
    contact = urlsplit(contact_url or "")
    if (
        contact.scheme != "https"
        or not contact.netloc
        or contact.username
        or contact.password
        or contact.query
        or contact.fragment
    ):
        raise IngestionError(
            "ONS downloads require an owner-approved non-personal project contact URL"
        )
    headers = {
        "User-Agent": USER_AGENT + " (+" + contact_url + ")",
        "Accept-Encoding": "identity",
    }
    attempts = []
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with opener(Request(url, headers=headers), timeout=60) as response:
                source_url(response.url)
                if response.status != 200:
                    raise IngestionError("Unexpected source response status")
                body = response.read(128_000_001)
                length = response.headers.get("Content-Length")
                if (
                    not body
                    or len(body) > 128_000_000
                    or (length and int(length) != len(body))
                ):
                    raise IngestionError(
                        "Empty, oversized or incomplete population response"
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
                        f"population access denied/failed: HTTP {status}"
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
                    "population download failed after three attempts"
                ) from exc
            LOG.warning(
                "Retrying population source after %s seconds (attempt %s/3)",
                wait,
                attempt + 1,
            )
            sleep(wait)
    raise AssertionError("unreachable")


def load_inventory(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["source_catalogue"] != CATALOGUE or not data["editions"]:
            raise ValueError("dataset catalogue")
        ids = set()
        urls = set()
        for edition in data["editions"]:
            key = identifier(edition["edition_id"])
            source_url(edition["url"])
            if (
                key in ids
                or edition["url"] in urls
                or not re.fullmatch(r"[a-f0-9]{64}", edition["source_sha256"])
            ):
                raise ValueError("duplicate edition or invalid checksum")
            ids.add(key)
            urls.add(edition["url"])
            if (
                edition["kind"] not in {"summary", "detail"}
                or not 2011 <= edition["latest_reference_year"] <= 2100
            ):
                raise ValueError("edition contract")
            sheets = [t["sheet"] for t in edition["tables"]]
            if not sheets or len(sheets) != len(set(sheets)):
                raise ValueError("sheet contract")
            for table in edition["tables"]:
                if (
                    not (
                        table["sheet"] in {"MYE3", "MYE4", "MYE5"}
                        or table["sheet"].startswith("MYEB3")
                    )
                    or not table["title"]
                    or table["header_row"] < 1
                ):
                    raise ValueError("selected source table")
                headers = [v for v in table["column_labels"] if v]
                if len(headers) != len(set(headers)) or not headers:
                    raise ValueError("duplicate header")
        return data
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise IngestionError("Invalid ONS population source inventory") from exc


def xml_cells(body: bytes, sheet_name: str) -> dict:
    """Retain exact XML numeric literals and formula text alongside parsed values."""
    import posixpath
    import zipfile
    from xml.etree import ElementTree as ET

    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(body)) as book:
        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        relationship = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        sheet = next(
            s
            for s in workbook.findall("m:sheets/m:sheet", ns)
            if s.attrib["name"] == sheet_name
        )
        target = relationship[
            sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
        ]
        target = (
            target.lstrip("/")
            if target.startswith("/")
            else posixpath.normpath("xl/" + target)
        )
        if not target.startswith("xl/worksheets/"):
            raise IngestionError("Unexpected workbook worksheet relationship")
        root = ET.fromstring(book.read(target))
        result = {}
        for c in root.findall("m:sheetData/m:row/m:c", ns):
            value = c.find("m:v", ns)
            formula = c.find("m:f", ns)
            result[c.attrib["r"]] = dict(
                raw_xml_value=value.text if value is not None else None,
                formula=formula.text if formula is not None else None,
                xml_type=c.attrib.get("t", "n"),
            )
        return result


def selected_column(sheet: str, header: str, end_year: int):
    """Map only published fields; never calculate density, net migration or growth."""
    if sheet == "MYE3":
        names = {
            "Internal Migration Inflow": "internal_inflow",
            "Internal Migration Outflow": "internal_outflow",
            "Internal Migration Net": "internal_net",
            "International Migration Inflow": "international_inflow",
            "International Migration Outflow": "international_outflow",
            "International Migration Net": "international_net",
        }
        names = {k.casefold(): v for k, v in names.items()}
        return (
            (names[header.casefold()], end_year, "persons")
            if header.casefold() in names
            else None
        )
    if sheet == "MYE4":
        match = re.fullmatch(r"Mid-(20[0-9]{2})", header)
        return ("population", int(match[1]), "persons") if match else None
    if sheet == "MYE5":
        if header == "Area (sq km)":
            return ("land_area", None, "square_kilometres")
        match = re.fullmatch(r"(20[0-9]{2}) people per sq\. km2?", header)
        return (
            ("published_density", int(match[1]), "persons_per_square_kilometre")
            if match
            else None
        )
    match = re.fullmatch(
        r"(population|internal_in|internal_out|internal_net|international_in|international_out|international_net)_(20[0-9]{2})",
        header,
    )
    if match:
        measure = {
            "internal_in": "internal_inflow",
            "internal_out": "internal_outflow",
            "international_in": "international_inflow",
            "international_out": "international_outflow",
        }.get(match[1], match[1])
        return measure, int(match[2]), "persons"
    return None


def numeric_cell(cell, xml: dict) -> tuple[float | None, str, str]:
    from decimal import Decimal, InvalidOperation

    raw = cell.value
    if xml.get("formula"):
        text = xml.get("raw_xml_value") or ""
        kind = "formula_cached" if text else "formula_without_cached_value"
    elif getattr(cell, "data_type", "") == "n" and raw is not None:
        text = xml.get("raw_xml_value")
        if text is None:
            raise IngestionError("Numeric source cell has no XML value")
        kind = "numeric"
    else:
        text = "" if raw is None else str(raw)
        return None, "missing" if raw is None else "source_marker", text
    if not text:
        return None, kind, text
    try:
        value = Decimal(text)
        if not value.is_finite() or not math.isfinite(float(value)):
            raise ValueError("non-finite source value")
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise IngestionError("Invalid cached/numeric source value") from exc
    return float(value), kind, text


def parse_workbook(body: bytes, edition: dict, provenance: dict, cohort: dict):
    """Source cells retain edition/sheet identity; all source geographies remain."""
    from openpyxl.utils import get_column_letter

    try:
        book = openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=False)
    except Exception as exc:
        raise IngestionError("Invalid ONS population XLSX workbook") from exc
    records = []
    notes = []
    schema = []
    try:
        for sheet_name in [
            s
            for s in book.sheetnames
            if s.lower()
            in {
                "cover sheet",
                "notes",
                "contents",
                "geography guide",
                "related publications",
            }
        ]:
            sheet = book[sheet_name]
            for rn, row in enumerate(sheet.iter_rows(), 1):
                for cn, cell in enumerate(row, 1):
                    if cell.value is not None:
                        notes.append(
                            dict(
                                edition_id=edition["edition_id"],
                                source_sheet=sheet_name,
                                source_cell=f"{get_column_letter(cn)}{rn}",
                                text=str(cell.value),
                                source_style_id=getattr(cell, "_style_id", 0),
                                source_number_format=getattr(
                                    cell, "number_format", "General"
                                ),
                            )
                        )
        publication_evidence = [
            n["text"]
            for n in notes
            if n["source_sheet"].lower() == "cover sheet"
            and ("publish" in n["text"].lower() or "date" in n["text"].lower())
        ]
        geography_notes = [
            n["text"]
            for n in notes
            if "geograph" in n["text"].lower() or "boundar" in n["text"].lower()
        ]
        for contract in edition["tables"]:
            sn = contract["sheet"]
            if sn not in book.sheetnames:
                raise IngestionError("Expected source worksheet absent")
            sheet = book[sn]
            hr = contract["header_row"]
            rows = sheet.iter_rows()
            top = [next(rows) for _ in range(hr)]
            headers = ["" if c.value is None else str(c.value) for c in top[-1]]
            trim = lambda values: tuple(v for v in values if v)
            if str(top[0][0].value) != contract["title"] or trim(headers) != trim(
                contract["column_labels"]
            ):
                raise IngestionError("Population workbook title/header schema changed")
            if headers[:3] not in (
                ["Code", "Name", "Geography"],
                ["ladcode23", "laname23", "country"],
                ["ladcode21", "laname21", "country"],
            ):
                raise IngestionError("Unexpected source geography schema")
            vintage = (
                "2021"
                if headers[0] == "ladcode21"
                else (
                    "2023"
                    if headers[0] == "ladcode23"
                    else (
                        "2021"
                        if "2021localauthority" in edition["edition_slug"]
                        else "2023"
                    )
                )
            )
            columns = {
                i: selected_column(sn, h, edition["latest_reference_year"])
                for i, h in enumerate(headers)
            }
            columns = {i: value for i, value in columns.items() if value is not None}
            measures = {x[0] for x in columns.values()}
            expected = (
                {"population"}
                if sn == "MYE4"
                else (
                    {"land_area", "published_density"}
                    if sn == "MYE5"
                    else {
                        "internal_inflow",
                        "internal_outflow",
                        "internal_net",
                        "international_inflow",
                        "international_outflow",
                        "international_net",
                    }
                )
            )
            if sn.startswith("MYEB3"):
                expected = expected | {"population"}
            if measures != expected:
                raise IngestionError("Selected source measure contract is incomplete")
            year_sets = {
                measure: {y for m, y, _ in columns.values() if m == measure}
                for measure in measures
            }
            for measure, years in year_sets.items():
                if measure == "land_area":
                    continue
                first = (
                    2011
                    if measure in {"population", "published_density"}
                    else edition["latest_reference_year"] if sn == "MYE3" else 2012
                )
                if years != set(range(first, edition["latest_reference_year"] + 1)):
                    raise IngestionError(
                        "Unexpected reference years or incomplete component columns"
                    )
            raw = xml_cells(body, sn)
            seen = set()
            area_count = 0
            for rn, row in enumerate(rows, hr + 1):
                code = "" if row[0].value is None else str(row[0].value)
                if not re.fullmatch(r"[EKNSW][0-9]{8}", code):
                    for cn, cell in enumerate(row, 1):
                        if cell.value is not None:
                            if isinstance(cell.value, str) and re.match(
                                r"^[EKNSW][0-9]", cell.value
                            ):
                                raise IngestionError(
                                    "Malformed source geography identifier"
                                )
                            notes.append(
                                dict(
                                    edition_id=edition["edition_id"],
                                    source_sheet=sn,
                                    source_cell=f"{get_column_letter(cn)}{rn}",
                                    text=str(cell.value),
                                    source_style_id=getattr(cell, "_style_id", 0),
                                    source_number_format=getattr(
                                        cell, "number_format", "General"
                                    ),
                                )
                            )
                    continue
                if code in seen:
                    raise IngestionError("Duplicate source geography row")
                seen.add(code)
                area_count += 1
                name = str(row[1].value or "")
                level = str(row[2].value or "")
                if not name or not level:
                    raise IngestionError("Source geography identity incomplete")
                for cn, (measure, year, unit) in columns.items():
                    cell = row[cn]
                    coordinate = f"{get_column_letter(cn+1)}{rn}"
                    xml = raw.get(coordinate, {})
                    value, kind, text = numeric_cell(cell, xml)
                    migration = measure.startswith(("internal_", "international_"))
                    flags = [
                        "source_publication_timezone_unverified",
                        "geography_notes_require_review",
                    ]
                    if measure == "land_area":
                        flags.append("area_reference_year_not_separately_specified")
                    if (
                        value is not None
                        and value < 0
                        and measure
                        in {
                            "population",
                            "land_area",
                            "published_density",
                            "internal_inflow",
                            "internal_outflow",
                            "international_inflow",
                            "international_outflow",
                        }
                    ):
                        flags.append("negative_non_net_source_value")
                    records.append(
                        dict(
                            edition_id=edition["edition_id"],
                            source_sheet=sn,
                            source_row=rn,
                            source_column=cn + 1,
                            source_cell=coordinate,
                            source_code=code,
                            source_name=name,
                            source_geography_type=level,
                            source_geography_vintage=vintage,
                            measure=measure,
                            reference_year=year,
                            reference_date=f"{year}-06-30" if year else "",
                            period_start=f"{year-1}-07-01" if migration else "",
                            period_end=f"{year}-06-30" if migration else "",
                            period_basis=(
                                "twelve_months_to_mid_year"
                                if migration
                                else (
                                    "mid_year_stock"
                                    if year
                                    else "source_geography_area_without_reference_year"
                                )
                            ),
                            unit=unit,
                            value=value,
                            value_kind=kind,
                            source_value_text=text,
                            source_value_json=json.dumps(cell.value, default=str),
                            source_xml_value=xml.get("raw_xml_value") or "",
                            source_formula=xml.get("formula") or "",
                            source_header=headers[cn],
                            source_style_id=getattr(cell, "_style_id", 0),
                            source_number_format=getattr(
                                cell, "number_format", "General"
                            ),
                            source_style_json=json.dumps(
                                list(book._cell_styles[getattr(cell, "_style_id", 0)])
                            ),
                            flags_json=json.dumps(flags),
                            exact_cohort_code_match=code in cohort,
                            source_url=provenance["identity"]["url"],
                            source_sha256=provenance["source_sha256"],
                            retrieved_at=provenance["retrieval"]["retrieved_at"],
                            source_snapshot_id=provenance["identity"]["snapshot_id"],
                        )
                    )
            if not seen:
                raise IngestionError("No source geography records")
            schema.append(
                dict(
                    edition_id=edition["edition_id"],
                    source_sheet=sn,
                    title=contract["title"],
                    header_row=hr,
                    headers_json=json.dumps(headers),
                    source_areas=area_count,
                    source_geography_vintage=vintage,
                    publication_evidence_json=json.dumps(publication_evidence),
                    geography_evidence_json=json.dumps(geography_notes),
                    source_publication_timezone="unverified",
                    source_url=edition["url"],
                )
            )
    finally:
        book.close()
    return records, notes, schema


def derive_audits(observations: pd.DataFrame, cohort: dict):
    coverage = []
    geo = []
    names = {name: code for code, name in cohort.items()}
    for (edition, sheet, measure, year), group in observations.groupby(
        ["edition_id", "source_sheet", "measure", "reference_year"],
        dropna=False,
        sort=True,
    ):
        matches = group[group.exact_cohort_code_match]
        codes = set(group.source_code)
        coverage.append(
            dict(
                edition_id=edition,
                source_sheet=sheet,
                measure=measure,
                reference_year=None if pd.isna(year) else int(year),
                source_areas=len(group),
                exact_cohort_matches=len(matches),
                numeric_cohort_values=int(matches.value.notna().sum()),
                source_numeric_values=int(group.value.notna().sum()),
                source_kind_counts_json=json.dumps(
                    group.value_kind.value_counts().to_dict(), sort_keys=True
                ),
                unmatched_target_codes_json=json.dumps(sorted(set(cohort) - codes)),
                unmatched_source_codes_json=json.dumps(sorted(codes - set(cohort))),
                missing_numeric_cohort_codes_json=json.dumps(
                    sorted(matches.loc[matches.value.isna(), "source_code"])
                ),
            )
        )
    areas = observations[
        [
            "edition_id",
            "source_sheet",
            "source_code",
            "source_name",
            "source_geography_type",
            "source_geography_vintage",
        ]
    ].drop_duplicates()
    for row in areas.to_dict("records"):
        code = row["source_code"]
        name = row["source_name"]
        geo.append(
            {
                **row,
                "exact_cohort_code_match": code in cohort,
                "same_name_target_code": names.get(name, ""),
                "relationship": (
                    "exact_code_match"
                    if code in cohort
                    else (
                        "same_name_different_code"
                        if name in names
                        else "outside_target_cohort"
                    )
                ),
                "reference_name": cohort.get(code, ""),
                "name_differs_on_exact_code": code in cohort and cohort[code] != name,
                "mapping_applied": False,
            }
        )
    for (edition, sheet), group in areas.groupby(
        ["edition_id", "source_sheet"], sort=True
    ):
        for code in sorted(set(cohort) - set(group.source_code)):
            geo.append(
                dict(
                    edition_id=edition,
                    source_sheet=sheet,
                    source_code="",
                    source_name="",
                    source_geography_type="",
                    source_geography_vintage="",
                    exact_cohort_code_match=False,
                    same_name_target_code=code,
                    relationship="target_without_exact_source_code_not_source_missingness",
                    reference_name=cohort[code],
                    name_differs_on_exact_code=False,
                    mapping_applied=False,
                )
            )
    return pd.DataFrame(coverage), pd.DataFrame(geo)


def offline_fetch(url):
    raise IngestionError(
        "Offline run: source response absent; approved non-personal ONS contact required before any download"
    )


def ingest(
    root: Path,
    snapshot: str,
    *,
    inventory: Path = Path("configs/ons_population_sources.json"),
    reference: Path = Path("configs/ons_lad_apr2025_v2.csv"),
    downloader=offline_fetch,
    sleep=time.sleep,
) -> dict:
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
            raise IngestionError("Immutable population output request conflict")
    documents = []
    sources = {}
    records = []
    notes = []
    schema = []
    for name, doc in contract["documents"].items():
        body, manifest = raw_source(
            root, DATASET, snapshot, name, doc["url"], downloader=downloader
        )
        if sha(body) != doc["source_sha256"]:
            raise IngestionError("Investigated source document changed")
        sources[name] = manifest
        documents.append(
            dict(
                source=name,
                url=doc["url"],
                source_sha256=sha(body),
                retrieved_at=manifest["retrieval"]["retrieved_at"],
                content=body.decode("utf-8-sig"),
            )
        )
    if not any(
        "Open Government Licence" in d["content"]
        for d in documents
        if d["source"] == "licence"
    ):
        raise IngestionError("ONS licence evidence requires review")
    for edition in contract["editions"]:
        key = edition["edition_id"]
        target = root / "raw" / DATASET / f"snapshot={snapshot}" / key
        if not target.exists():
            sleep(1.5)
        body, manifest = raw_source(
            root, DATASET, snapshot, key, edition["url"], downloader=downloader
        )
        if sha(body) != edition["source_sha256"]:
            raise IngestionError(
                "Investigated workbook checksum changed; do not overwrite contract/snapshot"
            )
        sources[key] = manifest
        cells, annotation, structure = parse_workbook(body, edition, manifest, cohort)
        records.extend(cells)
        notes.extend(annotation)
        schema.extend(structure)
    frame = (
        pd.DataFrame(records)
        .sort_values(["edition_id", "source_sheet", "source_row", "source_column"])
        .reset_index(drop=True)
    )
    if frame.duplicated(
        ["edition_id", "source_sheet", "source_code", "measure", "reference_year"]
    ).any():
        raise IngestionError("Duplicate population source observation key")
    frame["reference_year"] = frame.reference_year.astype("Int64")
    frame["value"] = pd.to_numeric(frame.value).astype("float64")
    coverage, geography = derive_audits(frame, cohort)
    tables = dict(
        observations=frame,
        coverage=coverage,
        geography_audit=geography,
        notes=pd.DataFrame(notes),
        schema=pd.DataFrame(schema),
        documents=pd.DataFrame(documents),
    )
    info = dict(
        identity=identity,
        transformation_version=VERSION,
        sources=sources,
        source_contract=contract,
        validation=dict(
            editions=len(contract["editions"]),
            observations=len(frame),
            source_sheets=len(schema),
            source_kind_counts=frame.value_kind.value_counts().to_dict(),
        ),
        licence="Crown copyright; Office for National Statistics; Open Government Licence v3.0; retain exceptions/source attribution",
        exact_point_in_time=False,
        vintage_policy="Separate native source editions and sheets; no model-input vintage selected",
        geography_policy="Original codes/names/vintage evidence; no mappings",
        area_reference_policy="Area source cell without a separate reference year retained once per source area/edition; not broadcast across years",
        acquisition_mode="Offline verified retained source files; further automated ONS downloads require owner-approved non-personal project contact",
    )
    return publish_tables(root, DATASET, snapshot, tables, tables, info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    parser.add_argument(
        "--inventory", type=Path, default=Path("configs/ons_population_sources.json")
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
