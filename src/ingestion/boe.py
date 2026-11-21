"""Immutable Bank of England financing source snapshots; no monthly features."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import http.client
import json
import logging
import math
import re
import shutil
import tempfile
import time
import tomllib
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

import pandas as pd

VERSION = "boe-ingestion-v1"
BASE = "https://www.bankofengland.co.uk/boeapps/database/"
BANK_URL = BASE + "Bank-Rate.asp"
HEADERS = {"User-Agent": "Mozilla/5.0"}
LOG = logging.getLogger(__name__)


class IngestionError(RuntimeError):
    """The source or stored snapshot cannot be safely promoted."""


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def xml_url(end: date) -> str:
    return BASE + "_iadb-fromshowcolumns.asp?" + urlencode({
        "CodeVer": "new", "xml.x": "yes", "Datefrom": "01/Jan/2012",
        "Dateto": end.strftime("%d/%b/%Y"), "SeriesCodes": "IUMZID4",
        "UsingCodes": "Y", "VPD": "Y", "VFD": "Y", "VUD": "A",
        "VUDdate": "03/Jun/2007",
    })


def fetch(url: str) -> tuple[bytes, dict]:
    """Bounded retries for transport/transient HTTP failures, never for bad data."""
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=60) as response:
                if urlsplit(response.url).hostname != "www.bankofengland.co.uk":
                    raise IngestionError("Unexpected source redirect")
                body = response.read(20_000_001)
                if not body or len(body) > 20_000_000:
                    raise IngestionError("Empty or oversized source response")
                length = response.headers.get("Content-Length")
                if length and int(length) != len(body):
                    raise IngestionError("Incomplete source response")
                return body, dict(url=url, resolved_url=response.url,
                    request_headers=HEADERS, response_headers=dict(response.headers),
                    status=response.status, retrieval_started_at=started,
                    retrieved_at=datetime.now(timezone.utc).isoformat())
        except (OSError, URLError, http.client.HTTPException) as exc:
            if isinstance(exc, HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise IngestionError(f"Source access failed: {exc}") from exc
            if attempt == 2:
                raise IngestionError(f"Source access failed after 3 attempts: {exc}") from exc
            LOG.warning("Source request failed; retry %s: %s", attempt + 1, exc)
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def number(value: str) -> float:
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise IngestionError(f"Invalid rate: {value!r}") from exc
    if not math.isfinite(result):
        raise IngestionError(f"Non-finite rate: {value!r}")
    return result


def timestamp(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError) as exc:
        raise IngestionError(f"Invalid source update timestamp: {value!r}") from exc
    return value  # Deliberately no timezone inference.


def parse_iumzid4(body: bytes) -> tuple[dict[str, pd.DataFrame], dict]:
    if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
        raise IngestionError("XML entities/DOCTYPE are not supported")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise IngestionError(f"Malformed source XML: {exc}") from exc
    series = [n for n in root.iter() if n.get("SCODE")]
    if len(series) != 1 or series[0].get("SCODE") != "IUMZID4":
        raise IngestionError("Expected exactly the IUMZID4 series")
    if not any(n.get("FREQ_CODE") == "M" for n in series[0]):
        raise IngestionError("Expected monthly series frequency")
    if not any(n.get("CAT_NAME") == "OUTPUT IN" and n.get("CAT_VAL") == "%" for n in series[0]):
        raise IngestionError("Expected percentage units")
    metadata = [{"tag": n.tag, "attributes": n.attrib, "text": n.text}
                for n in series[0].iter() if not n.get("TIME") and
                n.tag.rsplit("}", 1)[-1] != "Revision"]
    history, current, selected = [], [], []
    months = set()
    for obs in (n for n in series[0].iter() if n.get("TIME")):
        try:
            day = date.fromisoformat(obs.get("TIME"))
        except (ValueError, TypeError) as exc:
            raise IngestionError("Invalid observation date") from exc
        month = day.strftime("%Y-%m")
        if day.day != calendar.monthrange(day.year, day.month)[1] or month in months:
            raise IngestionError("Duplicate month or non-month-end observation")
        months.add(month)
        events = []
        notes = ET.tostring(obs, encoding="unicode")
        def event(node, update, origin):
            fields = [key for key in ("PROV_VALUE", "OBS_VALUE") if key in node.attrib]
            if len(fields) != 1:
                raise IngestionError("Expected one provisional or final value per event")
            key = fields[0]
            return dict(observation_month=month, source_observation_date=day,
                rate_percent=number(node.get(key)), source_value_text=node.get(key),
                observation_status="provisional" if key == "PROV_VALUE" else "final",
                source_updated_at=timestamp(update), record_origin=origin,
                source_attributes_json=json.dumps(node.attrib, sort_keys=True))
        for rev in obs:
            if rev.tag.rsplit("}", 1)[-1] == "Revision":
                events.append(event(rev, rev.get("UPDATE_TIMESTAMP"), "revision"))
        now = event(obs, obs.get("LAST_UPDATED"), "current")
        current.append({**now, "source_notes_xml": notes})
        # Revision streams may repeat the current state. Coalesce only that
        # redundant representation; duplicate revision records are a hard error.
        keys = [(e["source_updated_at"], e["observation_status"]) for e in events]
        if len(keys) != len(set(keys)):
            raise IngestionError("Duplicate revision events")
        at_latest = [e for e in events if e["source_updated_at"] == now["source_updated_at"]]
        if at_latest:
            if any((e["rate_percent"], e["observation_status"]) !=
                   (now["rate_percent"], now["observation_status"]) for e in at_latest):
                raise IngestionError("Conflicting current and revision states")
        else:
            events.append(now)
        events.sort(key=lambda e: e["source_updated_at"])
        if events[-1]["source_updated_at"] > now["source_updated_at"]:
            raise IngestionError("Revision newer than current state")
        if len({e["source_updated_at"] for e in events}) != len(events):
            raise IngestionError("Ambiguous event ordering")
        for index, item in enumerate(events):
            history.append({**item, "event_order": index + 1})
        selected.append({**events[0], "event_order": 1,
            "first_release_evidence_status": "earliest_recorded_not_certified",
            "history_evidence": "revision_records" if keys else "current_update_only",
            "pre_introduction_backfill": month < "2016-10",
            "source_notes_xml": notes})
    if not months:
        raise IngestionError("No monthly observations")
    ordered = sorted(months)
    expected = pd.period_range(ordered[0], ordered[-1], freq="M").astype(str).tolist()
    if ordered != expected or ordered[0] != "2012-01":
        raise IngestionError("Incomplete historical monthly coverage")
    bounds = [n for n in series[0] if n.get("FIRST_OBS")]
    if len(bounds) != 1 or bounds[0].get("FIRST_OBS")[:7] != ordered[0] or bounds[0].get("LAST_OBS")[:7] != ordered[-1]:
        raise IngestionError("Observation coverage conflicts with source bounds")
    return {"current": pd.DataFrame(current).sort_values("observation_month"),
            "history": pd.DataFrame(history).sort_values(["observation_month", "event_order"]),
            "selected": pd.DataFrame(selected).sort_values("observation_month")}, {
                "source_metadata": metadata, "observation_start": ordered[0],
                "observation_end": ordered[-1], "observation_count": len(months),
                "history_count": len(history), "original_publication_complete": False,
                "source_timestamp_timezone": "unverified"}


class BankTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.cell = None
        self.rows = []
        self.row = []
        self.closed = False

    def handle_starttag(self, tag, attrs):
        if tag == "table" and dict(attrs).get("id") == "stats-table":
            if self.active or self.closed:
                raise IngestionError("Multiple Bank Rate tables")
            self.active = True
        if self.active and tag == "tr":
            self.row = []
        if self.active and tag in {"td", "th"}:
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if self.active and tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join(self.cell.split()))
            self.cell = None
        if self.active and tag == "tr":
            self.rows.append(self.row)
        if self.active and tag == "table":
            self.active, self.closed = False, True


def parse_bank_rate(body: bytes) -> tuple[dict[str, pd.DataFrame], dict]:
    parser = BankTable()
    parser.feed(body.decode("utf-8-sig"))
    if not parser.closed or not parser.rows or parser.rows[0] != ["Date Changed", "Rate"]:
        raise IngestionError("Missing/incomplete Bank Rate table or changed headings")
    rows = []
    # Python's rolling two-digit-year pivot is unsuitable for future updates.
    # The official table begins in 1975; 75-99 belong to 1900, 00-74 to 2000.
    for row in parser.rows[1:]:
        if len(row) != 2 or not re.fullmatch(r"\d{2} [A-Za-z]{3} \d{2}", row[0]):
            raise IngestionError(f"Malformed Bank Rate row: {row}")
        year = int(row[0][-2:])
        try:
            effective = datetime.strptime(row[0][:-2] + str((1900 if year >= 75 else 2000) + year), "%d %b %Y").date()
        except ValueError as exc:
            raise IngestionError("Invalid effective date") from exc
        rows.append(dict(effective_date=effective, rate_percent=number(row[1]),
                         source_date_text=row[0], source_value_text=row[1]))
    days = [r["effective_date"] for r in rows]
    if not days or days != sorted(set(days), reverse=True):
        raise IngestionError("Bank Rate dates unordered, duplicated or conflicting")
    if days[-1] != date(1975, 1, 20):
        raise IngestionError("Bank Rate history truncated or historical boundary changed")
    frame = pd.DataFrame(rows).sort_values("effective_date")
    return {"events": frame}, dict(observation_start=days[-1].isoformat(),
        observation_end=days[0].isoformat(), observation_count=len(rows),
        availability="effective_dates_only_not_announcement_timestamps")


def write_json(path: Path, value: dict):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_bundle(directory: Path) -> dict:
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        for name, checksum in manifest["checksums"].items():
            if sha((directory / name).read_bytes()) != checksum:
                raise IngestionError(f"Stored checksum conflict: {directory / name}")
        return manifest
    except (OSError, ValueError, KeyError) as exc:
        raise IngestionError(f"Incomplete/corrupt snapshot: {directory}") from exc


def publish(directory: Path, files: dict[str, bytes], info: dict):
    """Publish a complete immutable directory; interrupted staging is never read."""
    directory.parent.mkdir(parents=True, exist_ok=True)
    checksums = {name: sha(body) for name, body in files.items()}
    if directory.exists():
        prior = verify_bundle(directory)
        if prior["checksums"] != checksums or prior["identity"] != info["identity"]:
            raise IngestionError(f"Immutable snapshot conflict: {directory}")
        return
    stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=directory.parent))
    try:
        for name, body in files.items():
            (stage / name).write_bytes(body)
        write_json(stage / "manifest.json", {**info, "checksums": checksums})
        try:
            stage.rename(directory)
        except OSError:
            if not directory.exists():
                raise
            prior = verify_bundle(directory)
            if prior["checksums"] != checksums or prior["identity"] != info["identity"]:
                raise IngestionError("Concurrent snapshot conflict")
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def ingest(root: Path, dataset: str, snapshot_id: str, end: date,
           downloader=fetch) -> dict:
    if dataset not in {"iumzid4", "bank_rate"} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", snapshot_id):
        raise IngestionError("Invalid dataset or snapshot identifier")
    url = xml_url(end) if dataset == "iumzid4" else BANK_URL
    identity = dict(dataset=dataset, snapshot_id=snapshot_id, url=url)
    relative = Path("bank_of_england") / dataset / f"snapshot={snapshot_id}"
    raw = root / "raw" / relative
    if raw.exists():
        raw_info = verify_bundle(raw)
        if raw_info["identity"] != identity:
            raise IngestionError("Snapshot identifier reused for a different request")
        body = (raw / "response.bin").read_bytes()
    else:
        body, retrieval = downloader(url)
        raw_info = dict(identity=identity, retrieval=retrieval, source_sha256=sha(body))
        publish(raw, {"response.bin": body}, raw_info)
        raw_info = verify_bundle(raw)
    parser = parse_iumzid4 if dataset == "iumzid4" else parse_bank_rate
    frames, report = parser(body)
    if dataset == "iumzid4" and report["observation_end"] > end.strftime("%Y-%m"):
        raise IngestionError("Source observations beyond requested range")
    processed = root / "processed" / relative
    validated = root / "validated" / relative
    # Check selected values in every completed prior snapshot, never substitute a
    # later revision when a future response loses an earlier retained event.
    parent = processed.parent
    for prior_dir in parent.glob("snapshot=*") if parent.exists() else []:
        prior_info = verify_bundle(prior_dir)
        if prior_dir == processed or prior_info["retrieval"]["retrieved_at"] > raw_info["retrieval"]["retrieved_at"]:
            continue
        if dataset == "iumzid4":
            prior = pd.read_parquet(prior_dir / "selected.parquet")
            overlap = prior.merge(frames["selected"], on="observation_month", suffixes=("_old", "_new"))
            for column in ("rate_percent", "source_updated_at", "observation_status"):
                if (overlap[column + "_old"] != overlap[column + "_new"]).any():
                    raise IngestionError("Selected earliest record changed across snapshots; owner review required")
            if not set(prior.observation_month).issubset(set(frames["selected"].observation_month)):
                raise IngestionError("Previously ingested months disappeared")
        else:
            prior = pd.read_parquet(prior_dir / "events.parquet")
            new = frames["events"].set_index("effective_date")
            for row in prior.itertuples():
                if row.effective_date not in new.index or new.loc[row.effective_date, "rate_percent"] != row.rate_percent:
                    raise IngestionError("Previously retained Bank Rate event changed or disappeared")
    info = dict(identity=identity, transformation_version=VERSION,
        source_sha256=sha(body), retrieval=raw_info["retrieval"], validation=report,
        source_name="Bank of England Database", units="percent",
        attribution="Copyright Governor and Company of the Bank of England; OGL v3.0",
        legal_url="https://www.bankofengland.co.uk/legal")
    for frame in frames.values():
        frame["source_id"] = "IUMZID4" if dataset == "iumzid4" else "bank_rate"
        frame["source_snapshot_id"] = snapshot_id
        frame["source_sha256"] = sha(body)
        frame["retrieved_at"] = raw_info["retrieval"]["retrieved_at"]
    source_frames = {k: v for k, v in frames.items() if k != "selected"}
    publish(validated, {k + ".parquet": v.to_parquet(index=False) for k, v in source_frames.items()}, info)
    outputs = {k: v for k, v in frames.items() if k in {"selected", "history", "events"}}
    publish(processed, {k + ".parquet": v.to_parquet(index=False) for k, v in outputs.items()}, info)
    return {**info, "raw_path": str(raw), "validated_path": str(validated),
            "processed_path": str(processed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["iumzid4", "bank_rate", "all"], default="all")
    parser.add_argument("--snapshot-id", required=True, help="Immutable retrieval identifier; reuse for offline reruns")
    parser.add_argument("--end-date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument("--config", type=Path, default=Path("configs/storage.toml"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    try:
        config_path = args.config.resolve()
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        if config.get("backend") != "local":
            raise IngestionError("Only configured local storage is implemented")
        root = Path(config["local_root"])
        if not root.is_absolute():
            root = config_path.parent.parent / root
        for dataset in (["bank_rate", "iumzid4"] if args.dataset == "all" else [args.dataset]):
            print(json.dumps(ingest(root, dataset, args.snapshot_id, args.end_date), indent=2))
    except (IngestionError, OSError, ValueError) as exc:
        parser.exit(1, f"Bank of England ingestion failed: {exc}\n")


if __name__ == "__main__":
    main()
