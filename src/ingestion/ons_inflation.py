"""ONS CPI/CPIH monthly observations by retained source vintage."""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from ingestion.source_io import IngestionError, fetch, publish_tables, raw_source, storage_root

ONS = "https://www.ons.gov.uk"
SERIES = {
    "D7G7": ("CPI", "annual_inflation_rate", "%", "CPI ANNUAL RATE 00: ALL ITEMS"),
    "D7BT": ("CPI", "index", "Index, base year = 100", "CPI INDEX 00: ALL ITEMS"),
    "L55O": ("CPIH", "annual_inflation_rate", "%", "CPIH ANNUAL RATE 00: ALL ITEMS"),
    "L522": ("CPIH", "index", "Index, base year = 100", "CPIH INDEX 00: ALL ITEMS"),
}
VERSION = "ons-inflation-v1"


def series_path(code: str) -> str:
    return f"/economy/inflationandpriceindices/timeseries/{code.lower()}/mm23"


def parse_month(text: str) -> str:
    if not re.fullmatch(r"\d{4} [A-Z]{3}", text):
        raise IngestionError(f"Invalid monthly reference: {text!r}")
    try:
        return datetime.strptime(text, "%Y %b").strftime("%Y-%m")
    except ValueError as exc:
        raise IngestionError("Invalid reference month") from exc


def parse_series(body: bytes, code: str, version: str) -> tuple[pd.DataFrame, dict]:
    try:
        source = json.loads(body)
        desc = source["description"]
        concept, measure, unit, title = SERIES[code]
        if desc["cdid"] != code or desc["datasetId"] != "MM23" or desc["unit"] != unit:
            raise IngestionError("ONS series identity/dataset/units changed")
        if not desc["title"].startswith(title + " ") or not source["uri"].startswith(series_path(code)):
            raise IngestionError("ONS measure description or URI changed")
        bases = re.findall(r"(\d{4})\s*=\s*100", desc["title"])
        if len(bases) != 1:
            raise IngestionError("Missing/ambiguous source index base")
        base = bases[0]
        if measure == "index" and not re.search(rf"{base}\s*=\s*100", desc.get("keyNote", "")):
            raise IngestionError("Inconsistent index-base metadata")
        release_raw = desc["releaseDate"]
        release_date = datetime.fromisoformat(release_raw.replace("Z", "+00:00")).date()
        rows = []
        for item in source["months"]:
            month = parse_month(item["date"])
            if item.get("sourceDataset") != "MM23":
                raise IngestionError("Monthly observation belongs to another dataset")
            text = item["value"]
            value = None if text == "" else float(text)
            if value is not None and (not math.isfinite(value) or (measure == "index" and value <= 0)):
                raise IngestionError("Invalid source numeric value")
            updated = item.get("updateDate", "")
            if updated:
                datetime.fromisoformat(updated.replace("Z", "+00:00"))
            rows.append(dict(series_id=code, concept=concept, measure=measure,
                observation_month=month, source_reference_text=item["date"],
                value=value, source_value_text=text, unit=unit, index_base_year=base,
                source_version_id=version, source_release_date=release_date,
                source_release_timestamp=release_raw, source_updated_at=updated,
                source_attributes_json=json.dumps(item, sort_keys=True)))
        if not rows:
            raise IngestionError("No monthly source observations")
        frame = pd.DataFrame(rows).sort_values("observation_month").reset_index(drop=True)
        if frame.observation_month.duplicated().any():
            raise IngestionError("Duplicate monthly observations")
        latest = frame.iloc[-1]
        if latest.observation_month != parse_month(desc["date"]) or latest.source_value_text != desc["number"]:
            raise IngestionError("Incomplete source or inconsistent latest observation")
        if latest.observation_month > release_date.strftime("%Y-%m"):
            raise IngestionError("Observation after source release")
        expected = pd.period_range(frame.observation_month.min(), frame.observation_month.max(), freq="M").astype(str)
        report = dict(series_id=code, source_version_id=version,
            observation_start=frame.observation_month.min(), observation_end=frame.observation_month.max(),
            observation_count=len(frame), missing_months=sorted(set(expected) - set(frame.observation_month)),
            missing_values=int(frame.value.isna().sum()), description=desc,
            version_inventory=source.get("versions", []),
            additional_metadata={key: val for key, val in source.items() if key not in {"months", "quarters", "years", "description"}})
        return frame, report
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise IngestionError(f"Invalid ONS JSON source: {exc}") from exc


def ingest(root: Path, snapshot: str, *, include_previous: bool = True, downloader=fetch) -> dict:
    frames, reports, sources = [], [], {}
    for code in SERIES:
        url = ONS + series_path(code) + "/data"
        body, provenance = raw_source(root, "ons_inflation", snapshot, code + "-current", url, downloader)
        frame, report = parse_series(body, code, "current")
        versions = report["version_inventory"]
        versions_to_read = []
        if include_previous and versions:
            previous = max(versions, key=lambda v: v["updateDate"])
            if not re.fullmatch(re.escape(series_path(code)) + r"/previous/v\d+", previous["uri"]):
                raise IngestionError("Unexpected historical-version URI")
            versions_to_read.append(previous)
        entries = [(frame, report, provenance, code + "-current")]
        for previous in versions_to_read:
            label = previous["uri"].rsplit("/", 1)[-1]
            raw, meta = raw_source(root, "ons_inflation", snapshot, code + "-" + label,
                ONS + previous["uri"] + "/data", downloader)
            past, past_report = parse_series(raw, code, label)
            if past.source_release_date.iloc[0] > frame.source_release_date.iloc[0]:
                raise IngestionError("Historical source release is newer than current")
            entries.append((past, past_report, meta, code + "-" + label))
        for data, validation, meta, source_id in entries:
            data["source_snapshot_id"] = snapshot
            data["source_sha256"] = meta["source_sha256"]
            data["retrieved_at"] = meta["retrieval"]["retrieved_at"]
            frames.append(data)
            reports.append(validation)
            sources[source_id] = meta
    observations = pd.concat(frames, ignore_index=True)
    if observations.duplicated(["series_id", "source_version_id", "observation_month"]).any():
        raise IngestionError("Duplicate vintage observations")
    info = dict(identity={"dataset": "ons_inflation", "snapshot_id": snapshot,
        "include_previous": include_previous}, transformation_version=VERSION,
        sources=sources, validation=reports, exact_point_in_time=False,
        vintage_policy="Preserve each retained release; no first-release selection",
        licence_url="https://www.ons.gov.uk/help/terms-conditions",
        attribution="Source: Office for National Statistics; Crown copyright; OGL v3.0")
    return publish_tables(root, "ons_inflation", snapshot, {"observations": observations},
        {"observations": observations}, info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        result = ingest(storage_root(args.config), args.snapshot_id)
        print(json.dumps({"processed_path": result["processed_path"],
            "coverage": [{k: r[k] for k in ("series_id", "source_version_id", "observation_start", "observation_end", "observation_count", "missing_months", "missing_values")} for r in result["validation"]]}, indent=2))
    except (IngestionError, OSError, ValueError) as exc:
        parser.exit(1, f"ONS inflation ingestion failed: {exc}\n")


if __name__ == "__main__":
    main()
