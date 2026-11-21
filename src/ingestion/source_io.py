"""Task 008 I/O boundary, reusing existing immutable/security primitives."""

from __future__ import annotations

import http.client
import logging
import re
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from ingestion.boe import (
    IngestionError, publish, safe_http_headers, safe_http_metadata, sha, verify_bundle,
)

ALLOWED_HOSTS = frozenset({"www.ons.gov.uk", "www.gov.uk", "publicdata.landregistry.gov.uk"})
LOG = logging.getLogger(__name__)


def official_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
        raise IngestionError("Expected an official HTTPS source URL")
    return url


def fetch(url: str) -> tuple[bytes, dict]:
    official_url(url)
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with urlopen(Request(url, headers=headers), timeout=60) as response:
                official_url(response.url)
                body = response.read(128_000_001)
                length = response.headers.get("Content-Length")
                if not body or len(body) > 128_000_000 or (length and int(length) != len(body)):
                    raise IngestionError("Empty, oversized or incomplete response")
                return body, dict(url=url, resolved_url=response.url, status=response.status,
                    retrieval_started_at=started, retrieved_at=datetime.now(timezone.utc).isoformat(),
                    request_headers=headers, response_headers=safe_http_headers(response.headers))
        except (OSError, URLError, http.client.HTTPException) as exc:
            if isinstance(exc, HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise IngestionError(f"Source access failed: {exc}") from exc
            if attempt == 2:
                raise IngestionError(f"Source failed after three attempts: {exc}") from exc
            LOG.warning("Retrying source request (%s/3): %s", attempt + 1, exc)
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", value):
        raise IngestionError("Invalid snapshot/source identifier")
    return value


def storage_root(config_path: Path) -> Path:
    config_path = config_path.resolve()
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if config.get("backend") != "local":
        raise IngestionError("Only the existing local storage backend is implemented")
    root = Path(config["local_root"])
    return root if root.is_absolute() else config_path.parent.parent / root


def raw_source(root: Path, dataset: str, snapshot: str, name: str, url: str,
               downloader=fetch) -> tuple[bytes, dict]:
    official_url(url)
    directory = root / "raw" / dataset / f"snapshot={identifier(snapshot)}" / identifier(name)
    identity = {"url": url, "dataset": dataset, "snapshot_id": snapshot, "source": name}
    if directory.exists():
        manifest = verify_bundle(directory)
        if manifest["identity"] != identity:
            raise IngestionError("Immutable source request conflict")
    else:
        body, retrieval = downloader(url)
        if not body:
            raise IngestionError("Empty response")
        publish(directory, {"response.bin": body}, {"identity": identity,
            "retrieval": safe_http_metadata(retrieval), "source_sha256": sha(body)})
        manifest = verify_bundle(directory)
    return (directory / "response.bin").read_bytes(), manifest


def publish_tables(root: Path, dataset: str, snapshot: str, validated: dict,
                   processed: dict, info: dict) -> dict:
    relative = Path(dataset) / f"snapshot={identifier(snapshot)}"
    for layer, frames in (("validated", validated), ("processed", processed)):
        files = {name + ".parquet": frame.to_parquet(index=False) for name, frame in frames.items()}
        publish(root / layer / relative, files, info)
    return safe_http_metadata({**info, "processed_path": str(root / "processed" / relative)})
