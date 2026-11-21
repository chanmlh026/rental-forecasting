"""Task 007.2 local verification; never print or export original header values.

Run from repository root. Reuses the existing Task 007 audit without downloads,
compares every existing snapshot file before/after, and records counts only.
"""

import json
import runpy
import subprocess
from http.cookies import SimpleCookie
from pathlib import Path

from ingestion.boe import safe_http_metadata, sha

BASELINE = "321962d0683a1e01953115e8b9f2e555cb8dd3b6"
EVIDENCE_PATH = "reports/data_audits/007/validation-evidence.json"
SENSITIVE_NAMES = {
    "cookie", "set-cookie", "set-cookie2", "authorization", "proxy-authorization",
    "authentication-info", "www-authenticate", "proxy-authenticate",
    "x-api-key", "x-auth-token", "x-session-id",
}


def header_field_count(value):
    if isinstance(value, dict):
        return sum((key.lower() in SENSITIVE_NAMES) + header_field_count(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return sum(header_field_count(item) for item in value)
    return 0


def snapshot_hashes():
    files = []
    for layer in ("raw", "validated", "processed"):
        parent = Path("data") / layer / "bank_of_england"
        files.extend(p for p in parent.rglob("*") if p.is_file())
    if not files:
        raise AssertionError("Existing Task 007 snapshots required")
    return {p.as_posix(): sha(p.read_bytes()) for p in files}


def main():
    original = json.loads(subprocess.check_output(
        ["git", "show", f"{BASELINE}:{EVIDENCE_PATH}"], text=True, encoding="utf-8"))
    before = snapshot_hashes()
    runpy.run_path("reports/data_audits/007/validate_live.py", run_name="__main__")
    after = snapshot_hashes()
    assert before == after, "An existing snapshot file changed"
    current = json.loads(Path(EVIDENCE_PATH).read_text(encoding="utf-8"))
    assert current == safe_http_metadata(original), "Non-header evidence changed"
    assert header_field_count(current) == 0

    # Search other tracked Task 007/007.1 artifacts for these specific cookie
    # values as well as structured header keys. Values never leave memory.
    cookie_values = set()
    def collect_cookies(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() == "set-cookie":
                    cookies = SimpleCookie()
                    cookies.load(item)
                    cookie_values.update(cookie.value for cookie in cookies.values())
                else:
                    collect_cookies(item)
        elif isinstance(value, list):
            for item in value:
                collect_cookies(item)
    collect_cookies(original)
    assert cookie_values, "Expected to identify original cookie values for scoped scan"
    task_files = subprocess.check_output(
        ["git", "ls-files", "reports/data_audits/007", "reports/data_audits/007.1",
         "docs/007*", "src/ingestion/boe.py", "tests/test_boe.py"], text=True).splitlines()
    cookie_value_hits = [name for name in task_files if any(
        value in Path(name).read_text(encoding="utf-8") for value in cookie_values)]
    assert not cookie_value_hits, "A known cookie value remains in a tracked task artifact"

    scanned = {}
    paths = subprocess.check_output(
        ["git", "ls-files", "reports/data_audits/007", "reports/data_audits/007.1"],
        text=True).splitlines()
    for name in paths:
        if name.endswith(".json"):
            value = json.loads(Path(name).read_text(encoding="utf-8"))
            scanned[name] = header_field_count(value)
            assert scanned[name] == 0
    # Inspect reachable historical versions locally, without displaying values.
    affected = []
    commits = subprocess.check_output(["git", "rev-list", "--all"], text=True).splitlines()
    for commit in commits:
        result = subprocess.run(["git", "show", f"{commit}:{EVIDENCE_PATH}"],
                                capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0 and header_field_count(json.loads(result.stdout)):
            affected.append(commit)
    report = {
        "task": "007.2", "baseline_commit": BASELINE,
        "baseline_sensitive_header_fields": header_field_count(original),
        "current_sensitive_header_fields": 0,
        "evidence_unchanged_except_header_exclusion": True,
        "existing_snapshot_files_checked": len(before),
        "all_existing_snapshot_file_hashes_unchanged": before == after,
        "parquet_files_unchanged": sum(name.endswith(".parquet") for name in before),
        "json_evidence_scanned": scanned,
        "task_artifact_files_checked_for_known_cookie_values": len(task_files),
        "known_cookie_value_matches_in_current_task_artifacts": len(cookie_value_hits),
        "reachable_commits_with_original_header_fields": affected,
        "history_rewritten": False,
        "legacy_local_manifests": "Preserved unchanged; filtered in memory before reuse/export.",
        "limitation": "Cookie validity, expiry and access scope are not verified; no session replay attempted.",
    }
    Path("reports/data_audits/007.2/validation-evidence.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Existing snapshot files unchanged: {len(before)}; current evidence contains no sensitive header fields; non-header evidence unchanged.")


if __name__ == "__main__":
    main()
