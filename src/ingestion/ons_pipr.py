"""Versioned ingestion for ONS Price Index of Private Rents workbooks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import math
import os
import posixpath
import re
import shutil
import sys
import tempfile
import tomllib
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

import pandas as pd


DATASET_URL = (
    "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/"
    "priceindexofprivaterentsukmonthlypricestatistics"
)
DEFAULT_DOWNLOAD_URL = (
    "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/"
    "datasets/priceindexofprivaterentsukmonthlypricestatistics/"
    "21october2026/priceindexofprivaterentsukmonthlypricestatistics.xlsx"
)
DEFAULT_RELEASE_ID = "2026-10-21"
TABLE_IDENTIFIER = "PIPR_Index_of_Private_Rents_UK_monthly_price_statistics"
OBSERVATION_SOURCE_NAME = "ONS PIPR"
GEOGRAPHY_REFERENCE_VERSION = "LAD_APR_2025_UK_NC_v2"
GEOGRAPHY_REFERENCE_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "LAD_APR_2025_UK_NC_v2/FeatureServer"
)
TRANSFORMATION_VERSION = "ons-pipr-ingestion-v1"
EXCLUDED_GEOGRAPHIES = {
    "E09000001": "City of London",
    "E06000053": "Isles of Scilly",
}
BEDROOM_COLUMNS = {
    1: "Rental price one bed",
    2: "Rental price two bed",
    3: "Rental price three bed",
}
REQUIRED_HEADINGS = {
    "Time period",
    "Area code",
    "Area name",
    *BEDROOM_COLUMNS.values(),
}
STANDARD_COLUMNS = [
    "observation_month",
    "local_authority_code",
    "local_authority_name",
    "bedroom_count",
    "average_monthly_rent_gbp",
    "source_name",
    "source_release_date",
    "source_vintage_id",
]
VALIDATED_COLUMNS = [*STANDARD_COLUMNS, "source_workbook_row"]
EXCEL_EPOCH = datetime(1899, 12, 30)
XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "office_rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "package_rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


class IngestionError(RuntimeError):
    """Raised when a source cannot be safely ingested."""


class WorkbookStructureError(IngestionError):
    """Raised when the workbook is not the expected ONS PIPR table."""


class DataValidationError(IngestionError):
    """Raised when parsed target observations fail quality gates."""


@dataclass(frozen=True)
class GeographyReference:
    eligible_names: dict[str, str]
    excluded_names: dict[str, str]
    version: str


@dataclass
class ValidationReport:
    release_id: str
    status: str = "failed"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_local_authorities: int = 0
    checked_bedroom_categories: list[int] = field(default_factory=list)
    observation_start: str | None = None
    observation_end: str | None = None
    observation_month_count: int = 0
    parsed_rows: int = 0
    validated_rows: int = 0
    missing_cells: int = 0
    missing_rent_values: int = 0
    duplicate_keys: int = 0
    missing_observations: list[dict[str, Any]] = field(default_factory=list)
    missing_gap_sequences: list[dict[str, Any]] = field(default_factory=list)
    value_errors: list[str] = field(default_factory=list)
    excluded_geographies: dict[str, str] = field(default_factory=dict)
    exclusion_observations: dict[str, int] = field(default_factory=dict)
    large_movement_warnings: list[dict[str, Any]] = field(default_factory=list)
    large_movement_count: int = 0
    large_movement_display_limit: int = 25
    large_movement_records: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "checked_local_authorities": self.checked_local_authorities,
            "checked_bedroom_categories": self.checked_bedroom_categories,
            "observation_start": self.observation_start,
            "observation_end": self.observation_end,
            "observation_month_count": self.observation_month_count,
            "parsed_rows": self.parsed_rows,
            "validated_rows": self.validated_rows,
            "missing_cells": self.missing_cells,
            "missing_rent_values": self.missing_rent_values,
            "duplicate_keys": self.duplicate_keys,
            "missing_observations": self.missing_observations,
            "missing_gap_sequences": self.missing_gap_sequences,
            "value_errors": self.value_errors,
            "excluded_geographies": self.excluded_geographies,
            "exclusion_observations": self.exclusion_observations,
            "large_movement_warnings": self.large_movement_warnings,
            "large_movement_count": self.large_movement_count,
            "large_movement_display_limit": self.large_movement_display_limit,
            "large_movement_displayed_count": len(self.large_movement_warnings),
        }

    def as_text(self) -> str:
        lines = [
            f"ONS PIPR validation: {self.status.upper()}",
            f"Source release: {self.release_id}",
            f"Local Authorities: {self.checked_local_authorities}",
            f"Bedroom categories: {', '.join(map(str, self.checked_bedroom_categories))}",
            (
                "Observation coverage: "
                f"{self.observation_start or 'unknown'} through "
                f"{self.observation_end or 'unknown'} "
                f"({self.observation_month_count} months)"
            ),
            f"Validated observations: {self.validated_rows}",
            f"Missing target cells: {self.missing_cells}",
            f"Missing or invalid rent values: {self.missing_rent_values}",
            f"Duplicate keys: {self.duplicate_keys}",
            "Known geographic exclusions: "
            + ", ".join(
                f"{code} {name}" for code, name in self.excluded_geographies.items()
            ),
        ]
        if self.errors:
            lines.extend(["", "Hard failures:", *[f"- {item}" for item in self.errors]])
        if self.warnings:
            lines.extend(["", "Warnings:", *[f"- {item}" for item in self.warnings]])
        if self.missing_gap_sequences:
            lines.extend(["", "Missing target sequences:"])
            for gap in self.missing_gap_sequences:
                lines.append(
                    "- "
                    f"{gap['local_authority_code']} {gap['local_authority_name']}, "
                    f"{gap['bedroom_count']} bed, {gap['gap_start_month']} through "
                    f"{gap['gap_end_month']} ({gap['gap_length_months']} months; "
                    f"{gap['classification']})"
                )
        if self.large_movement_warnings:
            lines.extend(
                [
                    "",
                    "Large year-over-year movements (review only): "
                    f"{self.large_movement_count} flagged; "
                    f"displaying {len(self.large_movement_warnings)} "
                    f"(limit {self.large_movement_display_limit}).",
                ]
            )
            for item in self.large_movement_warnings:
                lines.append(
                    "- "
                    f"{item['local_authority_code']} {item['local_authority_name']}, "
                    f"{item['bedroom_count']} bed, {item['origin_month']} to "
                    f"{item['target_month']}: {item['percent_change']:.1f}% "
                    f"(£{item['origin_rent_gbp']:.2f} to £{item['target_rent_gbp']:.2f})"
                )
        return "\n".join(lines) + "\n"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference)
    if letters is None:
        raise WorkbookStructureError(f"Invalid spreadsheet cell reference: {reference}")
    index = 0
    for letter in letters.group():
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def _resolve_zip_target(base_file: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_file), target))


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(node.text or "" for node in item.iter() if _local_name(node.tag) == "t")
        for item in root
    ]


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str | None:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(
            node.text or "" for node in cell.iter() if _local_name(node.tag) == "t"
        )
    value = cell.find("main:v", XLSX_NS)
    if value is None or value.text is None:
        return None
    if cell_type == "s":
        try:
            return shared_strings[int(value.text)]
        except (IndexError, ValueError) as exc:
            raise WorkbookStructureError("Invalid shared-string index in workbook.") from exc
    return value.text


def _find_target_table(
    archive: zipfile.ZipFile, table_identifier: str
) -> tuple[str, str, ET.Element]:
    table_parts = [
        name for name in archive.namelist() if re.fullmatch(r"xl/tables/table\d+\.xml", name)
    ]
    matches: list[tuple[str, ET.Element]] = []
    for part in table_parts:
        root = ET.fromstring(archive.read(part))
        if table_identifier in {root.attrib.get("name"), root.attrib.get("displayName")}:
            matches.append((part, root))
    if len(matches) != 1:
        raise WorkbookStructureError(
            f"Expected one table named {table_identifier!r}; found {len(matches)}."
        )
    table_part, table_root = matches[0]

    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    workbook_rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        item.attrib["Id"]: _resolve_zip_target("xl/workbook.xml", item.attrib["Target"])
        for item in workbook_rels
    }
    sheet_names: dict[str, str] = {}
    for sheet in workbook.findall("main:sheets/main:sheet", XLSX_NS):
        rel_id = sheet.attrib.get(f"{{{XLSX_NS['office_rel']}}}id")
        if rel_id in rel_targets:
            sheet_names[rel_targets[rel_id]] = sheet.attrib["name"]

    matching_sheets: list[tuple[str, str]] = []
    for sheet_part in sheet_names:
        rels_part = posixpath.join(
            posixpath.dirname(sheet_part),
            "_rels",
            posixpath.basename(sheet_part) + ".rels",
        )
        if rels_part not in archive.namelist():
            continue
        rels_root = ET.fromstring(archive.read(rels_part))
        for relationship in rels_root:
            if not relationship.attrib.get("Type", "").endswith("/table"):
                continue
            target_part = _resolve_zip_target(sheet_part, relationship.attrib["Target"])
            if target_part == table_part:
                matching_sheets.append((sheet_part, sheet_names[sheet_part]))
    if len(matching_sheets) != 1:
        raise WorkbookStructureError(
            f"Expected one worksheet linked to {table_identifier!r}; "
            f"found {len(matching_sheets)}."
        )
    sheet_part, sheet_name = matching_sheets[0]
    return sheet_part, sheet_name, table_root


def extract_pipr_rows(
    workbook_path: Path, table_identifier: str = TABLE_IDENTIFIER
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read the named PIPR Excel table without requiring an XLSX library."""
    workbook_path = Path(workbook_path)
    if not workbook_path.is_file():
        raise IngestionError(f"Workbook does not exist: {workbook_path}")
    if not zipfile.is_zipfile(workbook_path):
        raise WorkbookStructureError(f"File is not a readable XLSX archive: {workbook_path}")

    try:
        with zipfile.ZipFile(workbook_path) as archive:
            corrupt_member = archive.testzip()
            if corrupt_member is not None:
                raise WorkbookStructureError(
                    f"Workbook contains a corrupt ZIP member: {corrupt_member}"
                )
            required_parts = {"[Content_Types].xml", "xl/workbook.xml"}
            if not required_parts.issubset(archive.namelist()):
                raise WorkbookStructureError("XLSX archive is missing required workbook parts.")
            shared_strings = _read_shared_strings(archive)
            sheet_part, sheet_name, table = _find_target_table(archive, table_identifier)
            table_ref = table.attrib.get("ref", "")
            match = re.fullmatch(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", table_ref)
            if match is None:
                raise WorkbookStructureError(f"Invalid table range: {table_ref!r}")
            first_column = _column_index(match.group(1))
            header_row = int(match.group(2))
            last_row = int(match.group(4))
            table_columns = table.findall("main:tableColumns/main:tableColumn", XLSX_NS)
            headings = [item.attrib.get("name", "") for item in table_columns]
            missing_headings = sorted(REQUIRED_HEADINGS - set(headings))
            if missing_headings:
                raise WorkbookStructureError(
                    "PIPR table is missing required headings: "
                    + ", ".join(missing_headings)
                )
            if len(headings) != _column_index(match.group(3)) - first_column + 1:
                raise WorkbookStructureError(
                    "Table column metadata does not match its declared cell range."
                )
            required_offsets = {
                heading: headings.index(heading) + first_column
                for heading in REQUIRED_HEADINGS
            }
            rows: list[dict[str, Any]] = []
            checked_heading_row = False
            with archive.open(sheet_part) as worksheet:
                for _, element in ET.iterparse(worksheet, events=("end",)):
                    if _local_name(element.tag) != "row":
                        continue
                    row_number = int(element.attrib.get("r", "0"))
                    if row_number == header_row:
                        actual_headers = {
                            _column_index(cell.attrib["r"]): _cell_value(
                                cell, shared_strings
                            )
                            for cell in element
                            if _local_name(cell.tag) == "c"
                            and _column_index(cell.attrib.get("r", "")) in required_offsets.values()
                        }
                        mismatches = [
                            heading
                            for heading, column_index in required_offsets.items()
                            if actual_headers.get(column_index) != heading
                        ]
                        if mismatches:
                            raise WorkbookStructureError(
                                "Visible worksheet headings do not match the table metadata: "
                                + ", ".join(mismatches)
                            )
                        checked_heading_row = True
                    elif header_row < row_number <= last_row:
                        values = {
                            _column_index(cell.attrib["r"]): _cell_value(
                                cell, shared_strings
                            )
                            for cell in element
                            if _local_name(cell.tag) == "c"
                            and _column_index(cell.attrib.get("r", "")) in required_offsets.values()
                        }
                        rows.append(
                            {
                                "source_workbook_row": row_number,
                                **{
                                    heading: values.get(column_index)
                                    for heading, column_index in required_offsets.items()
                                },
                            }
                        )
                    element.clear()
            if not checked_heading_row:
                raise WorkbookStructureError(
                    f"Worksheet is missing table header row {header_row}."
                )
            if not rows:
                raise WorkbookStructureError("The named PIPR table contains no data rows.")
            metadata = {
                "table_identifier": table_identifier,
                "worksheet": sheet_name,
                "table_range": table_ref,
                "table_row_count": len(rows),
            }
            return rows, metadata
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise WorkbookStructureError(f"Unable to read XLSX workbook: {exc}") from exc


def load_geography_reference(
    path: Path, *, require_approved_cohort: bool = True
) -> GeographyReference:
    """Load the pinned, dated English LA list used for target selection."""
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {
                "gss_code",
                "local_authority_name",
                "reference_version",
                "target_eligible",
                "exclusion_reason",
            }
            if not required.issubset(reader.fieldnames or []):
                raise IngestionError("Geography reference is missing required columns.")
            entries = list(reader)
    except OSError as exc:
        raise IngestionError(f"Unable to read geography reference {path}: {exc}") from exc
    codes = [row["gss_code"].strip() for row in entries]
    if len(codes) != len(set(codes)):
        raise IngestionError("Geography reference contains duplicate GSS codes.")
    versions = {row["reference_version"].strip() for row in entries}
    if versions != {GEOGRAPHY_REFERENCE_VERSION}:
        raise IngestionError(
            f"Unexpected geography reference version: {sorted(versions)!r}"
        )
    eligible = {
        row["gss_code"].strip(): row["local_authority_name"].strip()
        for row in entries
        if row["target_eligible"].strip().lower() == "true"
    }
    excluded = {
        row["gss_code"].strip(): row["local_authority_name"].strip()
        for row in entries
        if row["target_eligible"].strip().lower() == "false"
    }
    if require_approved_cohort:
        if len(entries) != 296 or len(eligible) != 294 or excluded != EXCLUDED_GEOGRAPHIES:
            raise IngestionError(
                "The pinned geography reference must contain 296 English LAs, "
                "294 approved targets, and the two approved exclusions."
            )
    if not eligible or any(not re.fullmatch(r"E\d{8}", code) for code in codes):
        raise IngestionError("Geography reference contains invalid English GSS codes.")
    if any(
        row["target_eligible"].strip().lower() not in {"true", "false"}
        for row in entries
    ):
        raise IngestionError("Geography reference has an invalid target_eligible value.")
    if any(not row["exclusion_reason"].strip() for row in entries if row["gss_code"] in excluded):
        raise IngestionError("Every excluded geography must have a documented reason.")
    return GeographyReference(eligible, excluded, next(iter(versions)))


def _parse_month(value: Any, source_row: int) -> date:
    if value is None or str(value).strip() == "":
        raise DataValidationError(f"Missing observation month at workbook row {source_row}.")
    text = str(value).strip()
    try:
        numeric = float(text)
    except ValueError:
        numeric = math.nan
    if math.isfinite(numeric):
        if numeric <= 0:
            raise DataValidationError(
                f"Invalid Excel date serial {text!r} at workbook row {source_row}."
            )
        if not numeric.is_integer():
            raise DataValidationError(
                f"Excel observation date contains a time component at workbook row "
                f"{source_row}: {text!r}."
            )
        value_date = (EXCEL_EPOCH + timedelta(days=numeric)).date()
    else:
        parsed: date | None = None
        for fmt in ("%b-%y", "%b-%Y", "%Y-%m", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            raise DataValidationError(
                f"Ambiguous or invalid observation date {text!r} "
                f"at workbook row {source_row}."
            )
        value_date = parsed
    if value_date.day != 1:
        raise DataValidationError(
            f"Observation date is not the first of a month at workbook row {source_row}: "
            f"{value_date.isoformat()}."
        )
    return value_date


def _validate_release_id(release_id: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", release_id):
        raise IngestionError(f"Release identifier must be YYYY-MM-DD: {release_id!r}")
    try:
        return date.fromisoformat(release_id)
    except ValueError as exc:
        raise IngestionError(f"Release identifier is not a valid calendar date: {release_id}") from exc


def _release_id_from_official_url(source_url: str) -> str | None:
    parts = urlsplit(source_url)
    hostname = (parts.hostname or "").lower()
    if hostname != "ons.gov.uk" and not hostname.endswith(".ons.gov.uk"):
        return None

    candidates = [unquote(parts.path)]
    for uri in parse_qs(parts.query).get("uri", []):
        candidates.append(unquote(uri))
    for candidate in candidates:
        segments = [segment for segment in candidate.split("/") if segment]
        for index, segment in enumerate(segments):
            if segment != "priceindexofprivaterentsukmonthlypricestatistics":
                continue
            if index + 1 >= len(segments):
                continue
            edition = segments[index + 1]
            match = re.fullmatch(r"(\d{1,2})([A-Za-z]+)(\d{4})", edition)
            if match is None:
                continue
            try:
                return datetime.strptime(
                    f"{match.group(1)} {match.group(2)} {match.group(3)}",
                    "%d %B %Y",
                ).date().isoformat()
            except ValueError:
                raise IngestionError(
                    f"Official ONS URL contains an invalid edition identifier: {edition!r}"
                )
    raise IngestionError(
        "Cannot establish the PIPR edition from the official ONS URL; use the "
        "direct release workbook URL with an identifiable edition folder."
    )


def _validate_source_edition(
    release_id: str, source_url: str, local_workbook: Path | None
) -> None:
    _validate_release_id(release_id)
    url_release_id = _release_id_from_official_url(source_url)
    if url_release_id is not None and url_release_id != release_id:
        raise IngestionError(
            f"Release ID {release_id} does not match the edition {url_release_id} "
            "embedded in the official ONS workbook URL."
        )
    if url_release_id is None and local_workbook is None:
        raise IngestionError(
            "A direct, edition-identifiable official ONS workbook URL is required "
            "when no local workbook is supplied."
        )


def _validate_month_bound(value: str, parameter: str) -> pd.Timestamp:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise IngestionError(f"{parameter} must use YYYY-MM format: {value!r}")
    try:
        return pd.Timestamp(f"{value}-01")
    except ValueError as exc:
        raise IngestionError(f"{parameter} is not a valid calendar month: {value!r}") from exc


def _parse_rent(value: Any, code: str, source_row: int, bedroom: int) -> float:
    if value is None or str(value).strip() == "":
        raise DataValidationError(
            f"Missing {bedroom}-bed rent for {code} at workbook row {source_row}."
        )
    try:
        rent = float(str(value).strip())
    except ValueError as exc:
        raise DataValidationError(
            f"Non-numeric {bedroom}-bed rent {value!r} for {code} "
            f"at workbook row {source_row}."
        ) from exc
    if not math.isfinite(rent) or rent <= 0:
        raise DataValidationError(
            f"Rent must be finite and positive for {code}, {bedroom} bed, "
            f"workbook row {source_row}; received {value!r}."
        )
    return rent


def parse_long_observations(
    rows: list[dict[str, Any]],
    geography: GeographyReference,
    release_id: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Filter target geographies and transform the three wide rent fields."""
    source_release_date = _validate_release_id(release_id)
    records: list[dict[str, Any]] = []
    excluded_observations = {code: 0 for code in geography.excluded_names}
    unknown_english_codes: set[str] = set()
    value_errors: list[str] = []
    for row_index, row in enumerate(rows):
        source_row = int(row.get("source_workbook_row", row_index + 2))
        code_value = row.get("Area code")
        if code_value is None or not str(code_value).strip():
            raise DataValidationError(f"Missing area code at workbook row {source_row}.")
        code = str(code_value).strip()
        if code in geography.excluded_names:
            excluded_observations[code] += 1
            continue
        if code not in geography.eligible_names:
            if re.fullmatch(r"E0\d{7}", code):
                unknown_english_codes.add(code)
            continue
        area_name = str(row.get("Area name") or "").strip()
        expected_name = geography.eligible_names[code]
        if area_name != expected_name:
            raise DataValidationError(
                f"Area name/code mismatch at workbook row {source_row}: "
                f"{code} is {area_name!r}, expected {expected_name!r}."
            )
        observation_month = _parse_month(row.get("Time period"), source_row)
        for bedroom, heading in BEDROOM_COLUMNS.items():
            try:
                rent = _parse_rent(row.get(heading), code, source_row, bedroom)
            except DataValidationError as exc:
                value_errors.append(str(exc))
                rent = math.nan
            records.append(
                {
                    "observation_month": observation_month,
                    "local_authority_code": code,
                    "local_authority_name": area_name,
                    "bedroom_count": bedroom,
                    "average_monthly_rent_gbp": rent,
                    "source_name": OBSERVATION_SOURCE_NAME,
                    "source_release_date": source_release_date,
                    "source_vintage_id": release_id,
                    "source_workbook_row": source_row,
                }
            )
    if unknown_english_codes:
        raise DataValidationError(
            "Workbook contains English area codes absent from the pinned cohort: "
            + ", ".join(sorted(unknown_english_codes))
        )
    if not records:
        raise DataValidationError("No eligible English LA target rows were found.")
    frame = pd.DataFrame.from_records(records, columns=VALIDATED_COLUMNS)
    frame["observation_month"] = pd.to_datetime(frame["observation_month"])
    frame["source_release_date"] = pd.to_datetime(frame["source_release_date"])
    frame["local_authority_code"] = frame["local_authority_code"].astype("string")
    frame["local_authority_name"] = frame["local_authority_name"].astype("string")
    frame["bedroom_count"] = frame["bedroom_count"].astype("int8")
    frame["average_monthly_rent_gbp"] = frame["average_monthly_rent_gbp"].astype("float64")
    frame["source_name"] = frame["source_name"].astype("string")
    frame["source_vintage_id"] = frame["source_vintage_id"].astype("string")
    frame["source_workbook_row"] = frame["source_workbook_row"].astype("int32")
    frame.attrs["value_errors"] = value_errors
    return frame, {
        "excluded_geographies": geography.excluded_names,
        "exclusion_observations": excluded_observations,
        "source_release_date": source_release_date.isoformat(),
        "value_errors": value_errors,
    }


def _large_movements(
    frame: pd.DataFrame, warning_threshold_percent: float, display_limit: int = 25
) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
    movements: list[dict[str, Any]] = []
    if frame["average_monthly_rent_gbp"].isna().any() or frame.duplicated(
        ["local_authority_code", "bedroom_count", "observation_month"]
    ).any():
        return 0, movements, movements
    for (code, bedroom), series in frame.groupby(
        ["local_authority_code", "bedroom_count"], sort=False
    ):
        by_month = series.set_index("observation_month")["average_monthly_rent_gbp"]
        for origin, current in by_month.items():
            target = origin + pd.DateOffset(years=1)
            if target not in by_month.index:
                continue
            previous_rent = float(current)
            target_rent = float(by_month.loc[target])
            percent = (target_rent - previous_rent) / previous_rent * 100
            if abs(percent) >= warning_threshold_percent:
                movements.append(
                    {
                        "local_authority_code": str(code),
                        "local_authority_name": str(series["local_authority_name"].iloc[0]),
                        "bedroom_count": int(bedroom),
                        "origin_month": origin.strftime("%Y-%m"),
                        "target_month": target.strftime("%Y-%m"),
                        "origin_rent_gbp": previous_rent,
                        "target_rent_gbp": target_rent,
                        "percent_change": percent,
                    }
                )
    movements.sort(key=lambda item: abs(item["percent_change"]), reverse=True)
    return len(movements), movements[:display_limit], movements


def validate_panel(
    frame: pd.DataFrame,
    geography: GeographyReference,
    release_id: str,
    *,
    expected_start_month: str | None = None,
    expected_end_month: str | None = None,
    warning_threshold_percent: float = 20.0,
    require_complete_cohort: bool = True,
) -> ValidationReport:
    """Validate cohort coverage, monthly continuity, types, and rent values."""
    report = ValidationReport(
        release_id=release_id,
        checked_local_authorities=frame["local_authority_code"].nunique(),
        checked_bedroom_categories=sorted(
            int(value) for value in frame["bedroom_count"].unique()
        ),
        parsed_rows=len(frame),
        validated_rows=len(frame),
        excluded_geographies=geography.excluded_names,
    )
    if frame.empty:
        report.errors.append("No target observations were parsed.")
        return report
    dates = pd.DatetimeIndex(frame["observation_month"].drop_duplicates().sort_values())
    report.observation_start = dates[0].strftime("%Y-%m")
    report.observation_end = dates[-1].strftime("%Y-%m")
    expected_start = (
        _validate_month_bound(expected_start_month, "expected_start_month")
        if expected_start_month
        else dates[0]
    )
    expected_end = (
        _validate_month_bound(expected_end_month, "expected_end_month")
        if expected_end_month
        else dates[-1]
    )
    if (
        expected_start.day != 1
        or expected_end.day != 1
        or expected_end < expected_start
    ):
        report.errors.append(
            "Expected coverage bounds must be valid month starts in chronological order."
        )
        return report
    expected_dates = pd.date_range(expected_start, expected_end, freq="MS")
    report.observation_month_count = len(dates)
    unique_key_count = frame[
        ["local_authority_code", "bedroom_count", "observation_month"]
    ].drop_duplicates().shape[0]
    report.missing_cells = max(
        0,
        len(geography.eligible_names) * len(BEDROOM_COLUMNS) * len(expected_dates)
        - unique_key_count,
    )
    duplicated = frame.duplicated(
        ["local_authority_code", "bedroom_count", "observation_month"], keep=False
    )
    report.duplicate_keys = int(duplicated.sum())
    if report.duplicate_keys:
        report.duplicate_keys = int(
            frame.loc[
                duplicated,
                ["local_authority_code", "bedroom_count", "observation_month"],
            ]
            .drop_duplicates()
            .shape[0]
        )
    report.value_errors = getattr(frame, "attrs", {}).get("value_errors", [])
    report.missing_rent_values = int(
        frame["average_monthly_rent_gbp"].isna().sum()
    )
    expected_keys = {
        (code, bedroom, timestamp)
        for code in geography.eligible_names
        for bedroom in BEDROOM_COLUMNS
        for timestamp in expected_dates
    }
    observed_keys = set(
        frame[["local_authority_code", "bedroom_count", "observation_month"]]
        .itertuples(index=False, name=None)
    )
    missing_keys = expected_keys - observed_keys
    report.missing_cells = len(missing_keys)
    names = geography.eligible_names
    for code, bedroom, timestamp in sorted(missing_keys):
        report.missing_observations.append(
            {
                "local_authority_code": code,
                "local_authority_name": names[code],
                "bedroom_count": int(bedroom),
                "observation_month": timestamp.strftime("%Y-%m"),
            }
        )
    for code in sorted(geography.eligible_names):
        for bedroom in sorted(BEDROOM_COLUMNS):
            absent = [
                timestamp
                for timestamp in expected_dates
                if (code, bedroom, timestamp) in missing_keys
            ]
            if not absent:
                continue
            runs: list[list[pd.Timestamp]] = []
            current: list[pd.Timestamp] = []
            for timestamp in expected_dates:
                if timestamp in absent:
                    current.append(timestamp)
                elif current:
                    runs.append(current)
                    current = []
            if current:
                runs.append(current)
            series_present = any(
                observed_code == code and observed_bedroom == bedroom
                for observed_code, observed_bedroom, _ in observed_keys
            )
            for run in runs:
                if not series_present:
                    classification = "entirely_absent_series"
                elif run[0] == expected_dates[0]:
                    classification = "leading_missing_period"
                elif run[-1] == expected_dates[-1]:
                    classification = "trailing_missing_period"
                elif len(run) == 1:
                    classification = "isolated_internal_missing"
                else:
                    classification = "internal_consecutive_gap"
                report.missing_gap_sequences.append(
                    {
                        "local_authority_code": code,
                        "local_authority_name": names[code],
                        "bedroom_count": bedroom,
                        "gap_start_month": run[0].strftime("%Y-%m"),
                        "gap_end_month": run[-1].strftime("%Y-%m"),
                        "gap_length_months": len(run),
                        "classification": classification,
                    }
                )

    if require_complete_cohort and report.checked_local_authorities != len(geography.eligible_names):
        report.errors.append(
            f"Expected {len(geography.eligible_names)} eligible LAs, found "
            f"{report.checked_local_authorities}."
        )
    actual_codes = set(frame["local_authority_code"].astype(str))
    missing_codes = set(geography.eligible_names) - actual_codes
    extra_codes = actual_codes - set(geography.eligible_names)
    if missing_codes:
        report.errors.append(
            "Missing approved Local Authority codes: " + ", ".join(sorted(missing_codes))
        )
    if extra_codes:
        report.errors.append(
            "Unexpected Local Authority codes: " + ", ".join(sorted(extra_codes))
        )
    if require_complete_cohort and report.checked_bedroom_categories != [1, 2, 3]:
        report.errors.append(
            f"Expected bedroom categories [1, 2, 3], found "
            f"{report.checked_bedroom_categories}."
        )
    if not dates.equals(pd.DatetimeIndex(expected_dates)):
        report.errors.append(
            "Observed months do not exactly match expected coverage "
            f"{expected_dates[0]:%Y-%m} through {expected_dates[-1]:%Y-%m}."
        )
    if expected_start_month is not None and report.observation_start != expected_start_month:
        report.errors.append(
            f"Expected first month {expected_start_month}, found {report.observation_start}."
        )
    if expected_end_month is not None and report.observation_end != expected_end_month:
        report.errors.append(
            f"Expected last month {expected_end_month}, found {report.observation_end}."
        )
    if report.duplicate_keys:
        report.errors.append(f"Found {report.duplicate_keys} duplicate target keys.")
    if report.missing_cells:
        report.errors.append(
            f"Expected panel is missing {report.missing_cells} LA-bedroom-month cells."
        )
    if report.value_errors:
        report.errors.extend(report.value_errors)
    if report.missing_rent_values:
        report.errors.append(
            f"Found {report.missing_rent_values} null or invalid target rent values."
        )
    numeric_rents = frame["average_monthly_rent_gbp"].dropna()
    if (~numeric_rents.map(math.isfinite)).any() or (numeric_rents <= 0).any():
        report.errors.append("Target rent contains non-finite or non-positive values.")
    if frame["local_authority_name"].isna().any():
        report.errors.append("Local Authority name contains null values.")
    if release_id == DEFAULT_RELEASE_ID:
        if (report.observation_start, report.observation_end, len(dates), len(frame)) != (
            "2015-01",
            "2026-09",
            141,
            124_362,
        ):
            report.errors.append(
                "Reference release 2026-10-21 must contain 124,362 observations "
                "from 2015-01 through 2026-09."
            )
    if report.exclusion_observations and any(report.exclusion_observations.values()):
        report.warnings.append(
            "Workbook contains rows for explicitly excluded authorities; "
            "they were excluded from the target panel."
        )
    movement_count, displayed_movements, all_movements = _large_movements(
        frame, warning_threshold_percent
    )
    report.large_movement_count = movement_count
    report.large_movement_warnings = displayed_movements
    report.large_movement_records = all_movements
    if movement_count:
        report.warnings.append(
            f"{movement_count} year-over-year rent movements meet or exceed the "
            f"{warning_threshold_percent:g}% review threshold; displaying "
            f"{len(displayed_movements)}."
        )
    report.status = "passed" if not report.errors else "failed"
    return report


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _download_to_file(
    url: str, destination: Path, connect_timeout: float, read_timeout: float
) -> int:
    current_url = url
    for _ in range(6):
        parts = urlsplit(current_url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise IngestionError(f"Unsupported source URL: {current_url}")
        connection_class = (
            http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
        )
        connection = connection_class(parts.hostname, parts.port, timeout=connect_timeout)
        request_path = parts.path or "/"
        if parts.query:
            request_path += f"?{parts.query}"
        try:
            connection.connect()
            if connection.sock is not None:
                connection.sock.settimeout(read_timeout)
            connection.request(
                "GET",
                request_path,
                headers={"User-Agent": "rental-forecasting/0.1 ONS PIPR ingestion"},
            )
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location:
                    raise IngestionError(
                        f"ONS source returned HTTP {response.status} without a redirect target."
                    )
                current_url = urljoin(current_url, location)
                continue
            if response.status != 200:
                raise IngestionError(
                    f"ONS workbook download failed with HTTP {response.status} "
                    f"{response.reason}."
                )
            written = 0
            with destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
                    written += len(chunk)
                output.flush()
                os.fsync(output.fileno())
            content_length = response.getheader("Content-Length")
            if content_length is not None and written != int(content_length):
                raise IngestionError(
                    f"Incomplete ONS workbook download: received {written} of "
                    f"{content_length} bytes."
                )
            return written
        except (OSError, http.client.HTTPException) as exc:
            raise IngestionError(f"Unable to download ONS workbook from {url}: {exc}") from exc
        finally:
            connection.close()
    raise IngestionError("ONS workbook download exceeded the redirect limit.")


def _validate_xlsx(path: Path) -> dict[str, Any]:
    rows, workbook_metadata = extract_pipr_rows(path)
    if len(rows) == 0:
        raise WorkbookStructureError("Downloaded workbook contains no PIPR rows.")
    return workbook_metadata


def obtain_raw_snapshot(
    raw_root: Path,
    release_id: str,
    source_url: str,
    *,
    local_workbook: Path | None = None,
    connect_timeout: float = 15.0,
    read_timeout: float = 120.0,
) -> tuple[Path, dict[str, Any]]:
    """Create or integrity-check an immutable, release-specific raw snapshot."""
    _validate_source_edition(release_id, source_url, local_workbook)
    release_dir = Path(raw_root) / f"release={release_id}"
    raw_filename = "priceindexofprivaterentsukmonthlypricestatistics.xlsx"
    workbook_path = release_dir / raw_filename
    metadata_path = release_dir / "source_metadata.json"
    if release_dir.exists():
        if not workbook_path.is_file() or not metadata_path.is_file():
            raise IngestionError(
                f"Raw release directory is incomplete and will not be overwritten: {release_dir}"
            )
        with metadata_path.open(encoding="utf-8") as handle:
            metadata = json.load(handle)
        if metadata.get("source_release_id") != release_id:
            raise IngestionError("Existing raw snapshot has a conflicting release identifier.")
        actual_checksum = _sha256(workbook_path)
        if actual_checksum != metadata.get("raw_sha256"):
            raise IngestionError("Existing raw snapshot checksum does not match its metadata.")
        if workbook_path.stat().st_size != metadata.get("raw_file_size_bytes"):
            raise IngestionError("Existing raw snapshot size does not match its metadata.")
        if local_workbook is not None and _sha256(Path(local_workbook)) != actual_checksum:
            raise IngestionError(
                "The supplied workbook bytes differ from the immutable snapshot "
                f"already registered for release {release_id}."
            )
        _validate_xlsx(workbook_path)
        if metadata.get("source_url") != source_url:
            raise IngestionError(
                "Existing release identifier is registered to a different source URL."
            )
        return workbook_path, metadata

    release_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".release-{release_id}-", dir=release_dir.parent)
    )
    staged_workbook = staging_dir / raw_filename
    try:
        if local_workbook is not None:
            local_workbook = Path(local_workbook)
            if not local_workbook.is_file():
                raise IngestionError(f"Local workbook does not exist: {local_workbook}")
            shutil.copyfile(local_workbook, staged_workbook)
            retrieval_method = "local_file_copy"
        else:
            _download_to_file(source_url, staged_workbook, connect_timeout, read_timeout)
            retrieval_method = "official_http_download"
        if staged_workbook.stat().st_size == 0:
            raise IngestionError("Received an empty ONS workbook.")
        workbook_metadata = _validate_xlsx(staged_workbook)
        metadata = {
            "source_name": "ONS Price Index of Private Rents",
            "dataset_url": DATASET_URL,
            "source_url": source_url,
            "source_release_date": release_id,
            "source_release_id": release_id,
            "source_vintage_id": release_id,
            "published_at": None,
            "availability_note": (
                "The release date is not treated as an independently verified "
                "publication timestamp."
            ),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "retrieval_method": retrieval_method,
            "raw_filename": raw_filename,
            "raw_file_size_bytes": staged_workbook.stat().st_size,
            "raw_sha256": _sha256(staged_workbook),
            **workbook_metadata,
        }
        _write_json(staging_dir / "source_metadata.json", metadata)
        os.replace(staging_dir, release_dir)
        return workbook_path, metadata
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise


def _load_storage_root(config_path: Path) -> Path:
    config_path = Path(config_path).resolve()
    try:
        with config_path.open("rb") as handle:
            config = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise IngestionError(f"Unable to read storage configuration {config_path}: {exc}") from exc
    if config.get("backend", "local") != "local":
        raise IngestionError("This ingestion implementation supports local storage only.")
    local_root = Path(config.get("local_root", "./data"))
    return local_root if local_root.is_absolute() else config_path.parent.parent / local_root


def _parquet_checksum(path: Path) -> str:
    return _sha256(path)


def _write_parquet_temp(frame: pd.DataFrame, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(
        prefix=f".{destination.stem}-", suffix=".parquet.tmp", dir=destination.parent
    )
    os.close(handle)
    temporary = Path(name)
    try:
        frame.to_parquet(temporary, index=False, engine="pyarrow")
        round_trip = pd.read_parquet(temporary, engine="pyarrow")
        if len(round_trip) != len(frame):
            raise IngestionError(
                f"Parquet round-trip changed row count: {len(frame)} to {len(round_trip)}."
            )
        if list(round_trip.columns) != list(frame.columns):
            raise IngestionError("Parquet round-trip changed the output schema.")
        if round_trip.duplicated(
            ["local_authority_code", "bedroom_count", "observation_month"]
        ).any():
            raise IngestionError("Parquet round-trip produced duplicate target keys.")
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _check_existing_release(
    processed_dir: Path,
    validated_dir: Path,
    raw_metadata: dict[str, Any],
    geography: GeographyReference,
    expected_start_month: str,
    expected_end_month: str,
) -> dict[str, Any] | None:
    processed_parquet = processed_dir / "rent_observations.parquet"
    validated_parquet = validated_dir / "rent_observations.parquet"
    manifest_path = processed_dir / "manifest.json"
    complete_marker = processed_dir / "_SUCCESS.json"
    processed_exists = processed_dir.exists()
    validated_exists = validated_dir.exists()
    any_exists = processed_exists or validated_exists
    if not any_exists:
        return None
    release_id = str(raw_metadata.get("source_release_id", ""))
    if not release_id:
        raise IngestionError("Raw source metadata has no release identifier.")
    layer_manifests: dict[str, dict[str, Any]] = {}
    if processed_exists:
        layer_manifests["processed"] = _validate_existing_layer(
            processed_dir,
            "processed",
            raw_metadata,
            geography,
            expected_start_month,
            expected_end_month,
        )
    if validated_exists:
        layer_manifests["validated"] = _validate_existing_layer(
            validated_dir,
            "validated",
            raw_metadata,
            geography,
            expected_start_month,
            expected_end_month,
        )
    if len(layer_manifests) == 1:
        if complete_marker.exists():
            raise IngestionError(
                "A release completion marker exists but one output layer is missing."
            )
        return None
    manifest = layer_manifests["processed"]
    if layer_manifests["validated"] != manifest:
        raise IngestionError("Processed and validated release manifests disagree.")
    processed_frame = pd.read_parquet(processed_parquet, engine="pyarrow")
    validated_frame = pd.read_parquet(validated_parquet, engine="pyarrow")
    comparable_validated = validated_frame[STANDARD_COLUMNS]
    if not processed_frame.equals(comparable_validated):
        raise IngestionError("Processed and validated Parquet observations differ.")
    if complete_marker.exists():
        try:
            marker = json.loads(complete_marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IngestionError("Release completion marker is unreadable.") from exc
        if (
            marker.get("release_id") != release_id
            or marker.get("raw_sha256") != raw_metadata["raw_sha256"]
            or marker.get("manifest_sha256") != _sha256(manifest_path)
        ):
            raise IngestionError("Release completion marker conflicts with its manifest.")
    else:
        _write_json(
            complete_marker,
            {
                "release_id": release_id,
                "raw_sha256": raw_metadata["raw_sha256"],
                "manifest_sha256": _sha256(manifest_path),
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    return {
        "status": "reused",
        "raw_workbook": str(raw_metadata.get("raw_path", "")),
        "output_parquet": str(processed_parquet),
        "validated_parquet": str(validated_parquet),
        "manifest": str(manifest_path),
        "rows": int(manifest["validated_row_count"]),
        "validation_status": manifest["validation_outcome"],
    }


def _validate_existing_layer(
    directory: Path,
    layer: str,
    raw_metadata: dict[str, Any],
    geography: GeographyReference,
    expected_start_month: str,
    expected_end_month: str,
) -> dict[str, Any]:
    parquet_path = directory / "rent_observations.parquet"
    manifest_path = directory / "manifest.json"
    required_files = (
        parquet_path,
        manifest_path,
        directory / "validation_summary.txt",
        directory / "missing_observations.csv",
        directory / "missing_gap_sequences.csv",
    )
    if not all(path.is_file() for path in required_files):
        raise IngestionError(
            f"Existing {layer} output layer is incomplete and will not be overwritten."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IngestionError(f"Existing {layer} manifest is unreadable.") from exc
    if (
        "large_movement_detail_count" in manifest
        and not (directory / "large_rent_movements.csv").is_file()
    ):
        raise IngestionError(
            f"Existing {layer} layer is missing its full movement detail report."
        )
    release_id = raw_metadata.get("source_release_id")
    expected_identity = {
        "source_name": raw_metadata.get("source_name"),
        "source_url": raw_metadata.get("source_url"),
        "source_release_date": raw_metadata.get("source_release_date"),
        "source_release_id": release_id,
        "source_vintage_id": release_id,
        "raw_sha256": raw_metadata.get("raw_sha256"),
        "raw_file_size_bytes": raw_metadata.get("raw_file_size_bytes"),
        "table_identifier": raw_metadata.get("table_identifier"),
        "transformation_version": TRANSFORMATION_VERSION,
        "geography_reference_version": GEOGRAPHY_REFERENCE_VERSION,
        "validation_outcome": "passed",
    }
    mismatches = [
        key
        for key, expected in expected_identity.items()
        if manifest.get(key) != expected
    ]
    if mismatches:
        raise IngestionError(
            f"Existing {layer} manifest has inconsistent release metadata: "
            + ", ".join(mismatches)
        )
    manifest_start = manifest.get("expected_observation_start", expected_start_month)
    manifest_end = manifest.get("expected_observation_end", expected_end_month)
    if (manifest_start, manifest_end) != (expected_start_month, expected_end_month):
        raise IngestionError(
            f"Existing {layer} manifest has different expected coverage bounds."
        )
    if manifest.get("validation_status", "passed") != "passed":
        raise IngestionError(f"Existing {layer} manifest does not report validation passed.")
    checksum_key = f"{layer}_parquet_sha256"
    row_count_key = "validated_row_count"
    if manifest.get(checksum_key) != _sha256(parquet_path):
        raise IngestionError(f"Existing {layer} Parquet checksum does not match its manifest.")
    output_path_key = f"{layer}_output_path"
    if manifest.get(output_path_key) not in {str(parquet_path), None}:
        raise IngestionError(f"Existing {layer} manifest points to a different Parquet path.")
    try:
        frame = pd.read_parquet(parquet_path, engine="pyarrow")
    except (OSError, ValueError, ImportError) as exc:
        raise IngestionError(f"Existing {layer} Parquet cannot be read.") from exc
    expected_columns = VALIDATED_COLUMNS if layer == "validated" else STANDARD_COLUMNS
    if list(frame.columns) != expected_columns:
        raise IngestionError(f"Existing {layer} Parquet schema does not match the contract.")
    if (
        not pd.api.types.is_datetime64_any_dtype(frame["observation_month"])
        or frame["bedroom_count"].dtype != "int8"
        or frame["average_monthly_rent_gbp"].dtype != "float64"
        or not pd.api.types.is_string_dtype(frame["local_authority_code"])
        or not pd.api.types.is_string_dtype(frame["local_authority_name"])
        or not pd.api.types.is_string_dtype(frame["source_name"])
        or not pd.api.types.is_datetime64_any_dtype(frame["source_release_date"])
        or not pd.api.types.is_string_dtype(frame["source_vintage_id"])
        or (
            layer == "validated"
            and frame["source_workbook_row"].dtype != "int32"
        )
    ):
        raise IngestionError(f"Existing {layer} Parquet data types do not match the contract.")
    if len(frame) != manifest.get(row_count_key):
        raise IngestionError(f"Existing {layer} Parquet row count differs from its manifest.")
    if frame.empty or frame["local_authority_code"].nunique() != 294:
        raise IngestionError(f"Existing {layer} Parquet has an unexpected LA cohort.")
    if set(frame["local_authority_code"].astype(str)) != set(geography.eligible_names):
        raise IngestionError(f"Existing {layer} Parquet does not match the approved LA cohort.")
    if sorted(int(value) for value in frame["bedroom_count"].unique()) != [1, 2, 3]:
        raise IngestionError(f"Existing {layer} Parquet has unexpected bedroom categories.")
    key_columns = ["local_authority_code", "bedroom_count", "observation_month"]
    if frame.duplicated(key_columns).any():
        raise IngestionError(f"Existing {layer} Parquet contains duplicate observation keys.")
    if frame.isna().any().any():
        raise IngestionError(f"Existing {layer} Parquet contains null values.")
    if frame["local_authority_name"].astype(str).to_dict() != frame[
        "local_authority_code"
    ].astype(str).map(geography.eligible_names).to_dict():
        raise IngestionError(f"Existing {layer} Parquet has inconsistent LA names.")
    if (
        (frame["average_monthly_rent_gbp"] <= 0).any()
        or not frame["average_monthly_rent_gbp"].map(math.isfinite).all()
    ):
        raise IngestionError(f"Existing {layer} Parquet contains invalid rent values.")
    if frame["source_vintage_id"].astype(str).unique().tolist() != [release_id]:
        raise IngestionError(f"Existing {layer} Parquet has a conflicting source vintage.")
    expected_source_date = pd.Timestamp(raw_metadata["source_release_date"])
    if (
        frame["source_name"].astype(str).unique().tolist()
        != [OBSERVATION_SOURCE_NAME]
        or frame["source_release_date"].drop_duplicates().tolist()
        != [expected_source_date]
    ):
        raise IngestionError(f"Existing {layer} Parquet source metadata is inconsistent.")
    start = pd.Timestamp(frame["observation_month"].min()).strftime("%Y-%m")
    end = pd.Timestamp(frame["observation_month"].max()).strftime("%Y-%m")
    if (start, end) != (manifest.get("observation_start"), manifest.get("observation_end")):
        raise IngestionError(f"Existing {layer} Parquet coverage differs from its manifest.")
    months = pd.DatetimeIndex(frame["observation_month"].drop_duplicates().sort_values())
    if not months.equals(pd.date_range(months[0], months[-1], freq="MS")):
        raise IngestionError(f"Existing {layer} Parquet has discontinuous month coverage.")
    if len(frame) != 294 * 3 * len(months):
        raise IngestionError(f"Existing {layer} Parquet has missing cohort observations.")
    if (start, end) != (expected_start_month, expected_end_month):
        raise IngestionError(f"Existing {layer} Parquet differs from expected coverage.")
    if release_id == DEFAULT_RELEASE_ID and (
        len(months) != 141 or len(frame) != 124_362
    ):
        raise IngestionError("Existing reference release has unexpected coverage.")
    if layer == "validated" and frame["source_workbook_row"].isna().any():
        raise IngestionError("Existing validated Parquet has missing workbook row references.")
    if manifest.get("eligible_local_authority_count") != 294:
        raise IngestionError(f"Existing {layer} manifest has an unexpected geography cohort.")
    if manifest.get("excluded_geographies") != EXCLUDED_GEOGRAPHIES:
        raise IngestionError(f"Existing {layer} manifest has unexpected geography exclusions.")
    return manifest


def _publish_outputs(
    validated_frame: pd.DataFrame,
    processed_frame: pd.DataFrame,
    storage_root: Path,
    release_id: str,
    raw_workbook: Path,
    raw_metadata: dict[str, Any],
    workbook_metadata: dict[str, Any],
    geography: GeographyReference,
    report: ValidationReport,
) -> dict[str, Any]:
    release_component = f"release={release_id}"
    validated_dir = storage_root / "validated" / "ons_pipr" / release_component
    processed_dir = storage_root / "processed" / "ons_pipr" / release_component
    existing = _check_existing_release(
        processed_dir,
        validated_dir,
        {**raw_metadata, "raw_path": str(raw_workbook)},
        geography,
        report.observation_start or "",
        report.observation_end or "",
    )
    if existing is not None:
        return existing

    validated_final = validated_dir / "rent_observations.parquet"
    processed_final = processed_dir / "rent_observations.parquet"
    staging_base = storage_root / ".staging"
    staging_base.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f"ons-pipr-{release_id}-", dir=staging_base)
    )
    staged_validated_dir = staging_dir / "validated"
    staged_processed_dir = staging_dir / "processed"
    staged_validated = staged_validated_dir / "rent_observations.parquet"
    staged_processed = staged_processed_dir / "rent_observations.parquet"
    try:
        validated_temp = _write_parquet_temp(validated_frame, staged_validated)
        processed_temp = _write_parquet_temp(processed_frame, staged_processed)
        validated_checksum = _parquet_checksum(validated_temp)
        processed_checksum = _parquet_checksum(processed_temp)
        os.replace(validated_temp, staged_validated)
        os.replace(processed_temp, staged_processed)
        manifest = {
            **raw_metadata,
            "raw_path": str(raw_workbook),
            "workbook_table": workbook_metadata,
            "geography_reference_version": geography.version,
            "geography_reference_url": GEOGRAPHY_REFERENCE_URL,
            "geography_reference_path": "configs/ons_lad_apr2025_v2.csv",
            "eligible_local_authority_count": len(geography.eligible_names),
            "excluded_geographies": geography.excluded_names,
            "observation_start": report.observation_start,
            "observation_end": report.observation_end,
            "expected_observation_start": report.observation_start,
            "expected_observation_end": report.observation_end,
            "observation_month_count": report.observation_month_count,
            "parsed_wide_row_count": workbook_metadata["table_row_count"],
            "validated_row_count": report.validated_rows,
            "validation_outcome": report.status,
            "validation_errors": report.errors,
            "validation_warnings": report.warnings,
            "large_movement_review_rows": report.large_movement_warnings,
            "large_movement_count": report.large_movement_count,
            "large_movement_displayed_count": len(report.large_movement_warnings),
            "large_movement_detail_count": len(report.large_movement_records),
            "transformation_version": TRANSFORMATION_VERSION,
            "processed_output_path": str(processed_final),
            "processed_parquet_sha256": processed_checksum,
            "validated_output_path": str(validated_final),
            "validated_parquet_sha256": validated_checksum,
            "retrieved_at_utc": raw_metadata["retrieved_at_utc"],
        }
        manifest_path = staged_processed_dir / "manifest.json"
        validation_report_path = staged_processed_dir / "validation_summary.txt"
        validated_manifest_path = staged_validated_dir / "manifest.json"
        validated_report_path = staged_validated_dir / "validation_summary.txt"
        _write_json(manifest_path, manifest)
        _write_json(validated_manifest_path, manifest)
        report_text = report.as_text()
        validation_report_path.write_text(report_text, encoding="utf-8")
        validated_report_path.write_text(report_text, encoding="utf-8")
        _write_audit_csvs(staged_processed_dir, report)
        _write_audit_csvs(staged_validated_dir, report)
        validated_dir.parent.mkdir(parents=True, exist_ok=True)
        processed_dir.parent.mkdir(parents=True, exist_ok=True)
        for existing_dir, layer in (
            (validated_dir, "validated"),
            (processed_dir, "processed"),
        ):
            if existing_dir.exists():
                existing_manifest = _validate_existing_layer(
                    existing_dir,
                    layer,
                    {**raw_metadata, "raw_path": str(raw_workbook)},
                    geography,
                    report.observation_start or "",
                    report.observation_end or "",
                )
                if existing_manifest != manifest:
                    raise IngestionError(
                        f"Existing {layer} layer conflicts with the regenerated release; "
                        "it was not overwritten."
                    )
                existing_checksum = _sha256(
                    existing_dir / "rent_observations.parquet"
                )
                expected_checksum = manifest[f"{layer}_parquet_sha256"]
                if existing_checksum != expected_checksum:
                    raise IngestionError(
                        f"Existing {layer} content conflicts with the regenerated release."
                    )
        if not validated_dir.exists():
            os.rename(staged_validated_dir, validated_dir)
        if not processed_dir.exists():
            os.rename(staged_processed_dir, processed_dir)
        verified = _check_existing_release(
            processed_dir,
            validated_dir,
            {**raw_metadata, "raw_path": str(raw_workbook)},
            geography,
            report.observation_start or "",
            report.observation_end or "",
        )
        if verified is None:
            raise IngestionError("Release publication did not produce both output layers.")
        verified["status"] = "created"
        verified.update(
            {
                "validation_summary": str(processed_dir / "validation_summary.txt"),
                "raw_sha256": raw_metadata["raw_sha256"],
                "processed_parquet_sha256": processed_checksum,
                "observation_start": report.observation_start,
                "observation_end": report.observation_end,
                "local_authorities": report.checked_local_authorities,
                "bedroom_categories": report.checked_bedroom_categories,
                "missing_cells": report.missing_cells,
                "duplicate_keys": report.duplicate_keys,
                "warnings": report.warnings,
            }
        )
        return verified
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def _persist_failure_report(
    storage_root: Path, release_id: str, report: ValidationReport
) -> Path:
    failure_dir = (
        storage_root
        / "validation_reports"
        / "ons_pipr"
        / f"release={release_id}"
    )
    failure_dir.mkdir(parents=True, exist_ok=True)
    _write_audit_csvs(failure_dir, report)
    (failure_dir / "validation_summary.txt").write_text(
        report.as_text(), encoding="utf-8"
    )
    _write_json(failure_dir / "validation_summary.json", report.as_dict())
    return failure_dir / "validation_summary.txt"


def _write_audit_csvs(directory: Path, report: ValidationReport) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "missing_observations.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = [
            "local_authority_code",
            "local_authority_name",
            "bedroom_count",
            "observation_month",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report.missing_observations)
    with (directory / "missing_gap_sequences.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = [
            "local_authority_code",
            "local_authority_name",
            "bedroom_count",
            "gap_start_month",
            "gap_end_month",
            "gap_length_months",
            "classification",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report.missing_gap_sequences)
    with (directory / "large_rent_movements.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = [
            "local_authority_code",
            "local_authority_name",
            "bedroom_count",
            "origin_month",
            "target_month",
            "origin_rent_gbp",
            "target_rent_gbp",
            "percent_change",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report.large_movement_records)


def run_ingestion(
    *,
    config_path: Path,
    geography_path: Path,
    release_id: str = DEFAULT_RELEASE_ID,
    source_url: str = DEFAULT_DOWNLOAD_URL,
    local_workbook: Path | None = None,
    connect_timeout: float = 15.0,
    read_timeout: float = 120.0,
    warning_threshold_percent: float = 20.0,
    expected_start_month: str | None = None,
    expected_end_month: str | None = None,
) -> dict[str, Any]:
    """Download or reuse a workbook, validate it, and publish versioned Parquet."""
    _validate_source_edition(release_id, source_url, local_workbook)
    if connect_timeout <= 0 or read_timeout <= 0 or warning_threshold_percent <= 0:
        raise IngestionError("Timeouts and warning threshold must be positive.")
    if release_id == DEFAULT_RELEASE_ID:
        if expected_start_month not in {None, "2015-01"}:
            raise IngestionError("The reference release start month is fixed at 2015-01.")
        if expected_end_month not in {None, "2026-09"}:
            raise IngestionError("The reference release end month is fixed at 2026-09.")
        expected_start_month = "2015-01"
        expected_end_month = "2026-09"
    else:
        expected_start_month = expected_start_month or "2015-01"
        if expected_end_month is None:
            raise IngestionError(
                "Supply --expected-end-month for non-reference releases; "
                "the latest expected source month must be explicitly confirmed."
            )
    _validate_month_bound(expected_start_month, "expected_start_month")
    _validate_month_bound(expected_end_month, "expected_end_month")
    if pd.Timestamp(f"{expected_end_month}-01") < pd.Timestamp(
        f"{expected_start_month}-01"
    ):
        raise IngestionError("Expected coverage end month precedes its start month.")
    storage_root = _load_storage_root(config_path)
    geography = load_geography_reference(geography_path)

    try:
        workbook_path, raw_metadata = obtain_raw_snapshot(
            storage_root / "raw" / "ons_pipr",
            release_id,
            source_url,
            local_workbook=local_workbook,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
        )
    except WorkbookStructureError as exc:
        report = ValidationReport(
            release_id=release_id,
            errors=[str(exc)],
        )
        failure_report = _persist_failure_report(storage_root, release_id, report)
        raise DataValidationError(
            f"{exc} Validation report: {failure_report}"
        ) from exc
    reusable = _check_existing_release(
        storage_root / "processed" / "ons_pipr" / f"release={release_id}",
        storage_root / "validated" / "ons_pipr" / f"release={release_id}",
        {**raw_metadata, "raw_path": str(workbook_path)},
        geography,
        expected_start_month,
        expected_end_month,
    )
    if reusable is not None:
        return reusable
    report = ValidationReport(release_id=release_id)
    workbook_metadata: dict[str, Any] = {}
    try:
        rows, workbook_metadata = extract_pipr_rows(workbook_path)
        report.parsed_rows = len(rows)
        validated_frame, parse_metadata = parse_long_observations(
            rows, geography, release_id
        )
        report = validate_panel(
            validated_frame,
            geography,
            release_id,
            expected_start_month=expected_start_month,
            expected_end_month=expected_end_month,
            warning_threshold_percent=warning_threshold_percent,
        )
        report.parsed_rows = len(rows)
        report.excluded_geographies = parse_metadata["excluded_geographies"]
        report.exclusion_observations = parse_metadata["exclusion_observations"]
        if report.errors:
            raise DataValidationError("; ".join(report.errors))
        report.status = "passed"
    except (DataValidationError, WorkbookStructureError) as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        failure_report = _persist_failure_report(storage_root, release_id, report)
        raise DataValidationError(
            f"{exc} Validation report: {failure_report}"
        ) from exc

    processed_frame = validated_frame[STANDARD_COLUMNS].copy()
    processed_frame = processed_frame.sort_values(
        ["observation_month", "local_authority_code", "bedroom_count"],
        kind="stable",
        ignore_index=True,
    )
    validated_frame = validated_frame.sort_values(
        ["observation_month", "local_authority_code", "bedroom_count"],
        kind="stable",
        ignore_index=True,
    )
    raw_metadata = {
        **raw_metadata,
        "raw_path": str(workbook_path),
    }
    return _publish_outputs(
        validated_frame,
        processed_frame,
        storage_root,
        release_id,
        workbook_path,
        raw_metadata,
        workbook_metadata,
        geography,
        report,
    )


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download, validate, and version an ONS PIPR rent-level workbook."
    )
    parser.add_argument("--release-id", default=DEFAULT_RELEASE_ID)
    parser.add_argument("--source-url", default=DEFAULT_DOWNLOAD_URL)
    parser.add_argument(
        "--workbook",
        type=Path,
        help="Use a local XLSX file instead of downloading; its bytes are still snapshotted.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/storage.toml"),
        help="Existing storage configuration file.",
    )
    parser.add_argument(
        "--geography-reference",
        type=Path,
        default=Path("configs/ons_lad_apr2025_v2.csv"),
    )
    parser.add_argument("--connect-timeout", type=float, default=15.0)
    parser.add_argument("--read-timeout", type=float, default=120.0)
    parser.add_argument(
        "--expected-start-month",
        default=None,
        help="Expected first observation month (YYYY-MM); defaults to 2015-01.",
    )
    parser.add_argument(
        "--expected-end-month",
        help=(
            "Expected latest observation month (YYYY-MM), required for releases "
            "other than the fixed reference release."
        ),
    )
    parser.add_argument("--large-movement-warning-threshold-percent", type=float, default=20.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    try:
        result = run_ingestion(
            config_path=args.config,
            geography_path=args.geography_reference,
            release_id=args.release_id,
            source_url=args.source_url,
            local_workbook=args.workbook,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
            warning_threshold_percent=args.large_movement_warning_threshold_percent,
            expected_start_month=args.expected_start_month,
            expected_end_month=args.expected_end_month,
        )
    except (IngestionError, OSError, ValueError, KeyError) as exc:
        print(f"ONS PIPR ingestion failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
