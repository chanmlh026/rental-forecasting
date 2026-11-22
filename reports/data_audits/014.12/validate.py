"""Offline artifact checks, not independent source-data validation."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = "b66211dae66170ec53f257d06aa86f3f7afec741"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def baseline(path):
    return git("show", f"{BASE}:{path}")


m = json.loads((OUT / "publication-evidence-matrix.json").read_text(encoding="utf-8"))
generated = [OUT / "publication-evidence-matrix.json", OUT / "source-summary.md"]
prior_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in generated]
subprocess.run(["python", "-X", "utf8", str(OUT / "consolidate.py")], check=True, capture_output=True)
assert prior_hashes == [hashlib.sha256(p.read_bytes()).hexdigest() for p in generated]
for path in [OUT / "README.md", OUT / "source-summary.md"]:
    for ref in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if not ref.startswith("http"):
            assert (path.parent / ref.split("#")[0]).exists(), ref
assert len(m["records"]) == 76
assert len({r["record_id"] for r in m["records"]}) == 76
counts = collections.Counter(r["publication_class"] for r in m["records"])
assert counts == {"A":27, "B":1, "D":48}
for path, digest in m["inputs_sha256"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
for r in m["records"]:
    assert bool(r["publication_date"]) == (r["publication_class"] == "A")
    assert bool(r["publication_month"]) == (r["publication_class"] == "B")
    assert r["publication_window"] is None
    if r["publication_date"]:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["publication_date"])
    for ref in r["evidence_refs"]:
        assert (ROOT / ref.split("#")[0]).is_file(), ref
    assert r["original_observation_release_dates"] != r["publication_date"]
for source, s in m["source_summary"].items():
    rows = [r for r in m["records"] if r["source"] == source]
    assert len(rows) == s["records"] == sum(s["publication_counts"].values())
    assert collections.Counter(r["numerical_vintage"] for r in rows) == s["numerical_vintage_counts"]
    for c, n in s["publication_counts"].items():
        assert sum(r["publication_class"] == c for r in rows) == n
assert sum(s["records"] for s in m["source_summary"].values()) == 76
assert len(m["coverage_gaps"]["ashe_incomplete_retained_inputs"]) == 8
assert len(m["coverage_gaps"]["population_advertised_not_acquired"]) == 5
old = json.loads((ROOT / "reports/data_audits/014.10/consolidation-validation.json").read_text(encoding="utf-8"))
assert m["coverage_gaps"]["ashe_incomplete_retained_inputs"] == old["ASHE_no_complete_retained_edition"]
pop = json.loads((ROOT / "reports/data_audits/010/source-investigation.json").read_text(encoding="utf-8"))
for e in pop["editions"]:
    text = json.dumps(e["notes"], ensure_ascii=False)
    row = next(r for r in m["records"] if r["source"] == "Population/density/migration" and r["edition"] == e["edition_id"])
    day = {"2026-07-29":"29 July 2026", "2025-07-30":"30 July 2025", "2024-07-15":"15 July 2024"}[row["publication_date"]]
    assert day in text
    if e["latest_reference_year"] == 2022:
        assert "23 November 2023" in text and "replace" in text
for path in ["docs/data-architecture-and-dictionary.md", "docs/development-journal/02-data-preparation.md", "docs/issue-register.md"]:
    assert (ROOT / path).read_text(encoding="utf-8").startswith(baseline(path)), path
issue_text = (ROOT / "docs/issue-register.md").read_text(encoding="utf-8")
entries = [line for line in issue_text.splitlines() if line.startswith("| ISS-")]
assert len(entries) == 22
for issue in ["003","004","022"]:
    assert "| Open |" in next(line for line in entries if line.startswith(f"| ISS-{issue} |"))
timing = list(csv.reader(io.StringIO((ROOT / "docs/task-execution-log.csv").read_text(encoding="utf-8"))))
before = list(csv.reader(io.StringIO(baseline("docs/task-execution-log.csv"))))
assert timing[:len(before)] == before
assert all(len(row) == 7 for row in timing)
assert len({row[0] for row in timing[1:]}) == len(timing)-1
assert sum(row[0] == "014.12" for row in timing) == 1
changed = git("diff", "--name-only", BASE).splitlines() + git("ls-files", "--others", "--exclude-standard").splitlines()
allowed_docs = {"docs/task-execution-log.csv", "docs/data-architecture-and-dictionary.md", "docs/issue-register.md", "docs/development-journal/02-data-preparation.md", "docs/014.12-consolidate-historical-publication-evidence-and-temporal-gaps.md"}
assert all(path in allowed_docs or path.startswith("reports/data_audits/014.12/") for path in changed), changed
for path in changed:
    text = (ROOT / path).read_text(encoding="utf-8")
    assert not re.search(r"^(?:<{7}|={7}|>{7})(?: |$)", text, re.M), path
    assert not re.search(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)", text), path
subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
connectivity = subprocess.run(["git", "fsck", "--connectivity-only"], cwd=ROOT, capture_output=True, text=True, check=True)
result = dict(status="PASS WITH CONDITIONS", matrix_records=76, publication_counts=dict(counts),
    numerical_vintage_counts=dict(collections.Counter(r["numerical_vintage"] for r in m["records"])),
    source_groups=10, decisions=7, input_hashes_verified=len(m["inputs_sha256"]),
    checks=["deterministic offline regeneration", "local report links", "unique records and source totals", "date/null consistency and evidence paths", "population replacement dates verified against retained notes", "eight ASHE cases and five unacquired population files separate", "prior dictionary/journal and all 22 issue records preserved", "ISS-003/004/022 Open", "prior timing rows and seven columns preserved", "documentation/audit-only diff", "conflict-marker and credential-pattern scan", "git diff --check", "git fsck --connectivity-only"],
    git_connectivity="Pass; existing dangling objects retained, no connectivity failure",
    limitations="Offline artifact validation only, not independent source/statistical validation. Original publication evidence is not recreated. Production tests not run: no production changes.")
(OUT / "validation-receipt.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result))
