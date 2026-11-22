"""Offline metadata consolidation. Run with Python from any working directory.

Reads existing tracked audit evidence only; never opens ingested datasets or URLs.
The explicit judgements below are audit classifications, not availability rules.
"""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
inputs = {}
rows = []


def read(path):
    raw = (ROOT / path).read_bytes()
    inputs[path] = hashlib.sha256(raw).hexdigest()
    return raw.decode("utf-8-sig")


def audit(task, name):
    path = f"reports/data_audits/{task}/{name}"
    return json.loads(read(path)), path


def add(source, indicator, edition, period, classification, vintage, refs,
        limitation, date=None, month=None, timing_note=None):
    rows.append(dict(
        record_id=f"{source}:{edition}", source=source, indicator=indicator,
        edition=edition, observation_period=period,
        publication_class=classification, publication_date=date,
        publication_month=month, publication_window=None,
        timing_scope="Named edition/history evidence unit, not every observation's first release",
        timing_note=timing_note or "No verified intraday availability/timezone inferred.",
        original_observation_release_dates="Not established across the full historical span",
        numerical_vintage=vintage,
        vintage_scope="Relative to original publication of the observations, not the retrieval date",
        evidence_refs=refs, geography_or_series_limitations=limitation,
        pit_support=("Named dated edition potentially usable on/after its release, subject to geography, definitions and cutoff verification; not a full first-release history"
                     if classification in ("A", "B", "C") else
                     "Exact historical eligibility not established by this evidence unit"),
        remaining_assumption="Historical first-release timing and original values remain unproven wherever not explicitly evidenced; no fallback authorised",
    ))


vintage = list(csv.DictReader(io.StringIO(read("reports/data_audits/005.1/vintage_comparison.csv"))))
add("PIPR", "Monthly rents: approved 294-LA target", "2026-10-21", "2015-01 to 2026-09", "A", "Later vintage retained",
    ["docs/006-ons-pipr-ingestion.md", "docs/005.1-ons-pipr-workbook-coverage-audit.md"],
    "Reference boundaries; A/B1 preserved. Release label establishes date, not an independently verified publication timestamp.", date="2026-10-21")
add("PIPR", "Monthly rents: archive comparison", "2024-03 archive", "2015-01 to 2024-02", "B", "Later vintage retained",
    ["reports/data_audits/005.1/vintage_comparison.csv"],
    "Archive lacks Barnsley/Sheffield reference codes; 81.91–84.08% of compared cells differ. No attribution to revision versus geography inferred.", month=vintage[0]["archive_release_month"])

infl, ip = audit("008", "validation-evidence.json")
for x in infl["inflation"]:
    for label, date, end in [(x["prior_version"], x["prior_release_date"], "2026-09"),
                             ("current-Nov2026", x["current_release_date"], x["observation_end"])]:
        add("CPI/CPIH", x["series_id"], f'{x["series_id"]}-{label}',
            f'{x["observation_start"]} to {end}', "A", "Mixed vintage coverage", [ip + "#/inflation", ip + "#/inflation_sources"],
            "UK series; two retained editions, zero overlap revisions in this pair only. Earlier first-release vintages not established.", date=date)
for month, date in [("2026-08", "2026-10-21"), ("2026-09", "2026-11-18")]:
    add("UKHPI", "AveragePrice and Index", month, f"LA history 1995-01 to {month}", "A", "Mixed vintage coverage", [ip + "#/hpi", "docs/008-ons-inflation-and-uk-hpi-ingestion.md"],
        "Verified LA-code joins, native names retained/reference output names (Issue E). Two releases do not supply full original LA vintages; aggregate revision matrices are not LA vintage evidence.", date=date)

bank, bp = audit("007", "validation-evidence.json")
add("Bank Rate", "Official effective rate event history", "2026-11-21-task007", "1975-01-20 to 2026-11-05 (259 events)", "D", "Vintage unresolved", [bp + "#/bank_rate", "docs/007.1-iumzid4-historical-revisions-and-publication-vintages.md"],
    "Effective dates are evidenced; original announcement timestamps are not. Latest publicly announced AND effective rate remains approved; no monthly lag.",
    timing_note="Effective event dates are not publication dates. Retrieval is not announcement availability.")
iumz, zp = audit("007.1", "observation-tests.json")
add("IUMZID4", "BTL mortgage rate", "2026-11-21-task007 history", "2012-01 to 2026-10 (178 months; 336 history rows)", "D", "Mixed vintage coverage", [bp + "#/iumzid4", zp],
    "Approved earliest recorded value, including provisional, preserved. Earliest retained update is not certified first public availability; historical cadence changes and unknown source timezone prevent extrapolation of current schedule.")
for x in iumz["tests"]:
    add("IUMZID4", "Selected retained update-history test", x["observation_month"], x["observation_month"], "D", "Vintage unresolved", [zp + "#/tests"],
        f'Earliest retained update {x["earliest_retained_update_timestamp"]}; initial_publication_date={x["initial_publication_date"]}. Retained values identifiable, original release not certified.',
        timing_note="Source update timestamp retained verbatim; not promoted to a publication date or assigned a timezone.")

ashe, ap = audit("009.2", "validation-evidence.json")
for x in ashe["editions"]:
    eid = x["edition_id"]
    date = "2026-10-22" if eid in ("2026provisional", "2025revised") else None
    vc = "Original vintage retained" if "provisional" in eid else ("Later vintage retained" if "revised" in eid else "Vintage unresolved")
    add("ASHE", "8.7a residence/all employees/both sexes/median gross annual earnings", eid, str(x["observation_year"]), "A" if date else "D", vc,
        [ap + "#/editions", "reports/data_audits/009.1/publication-evidence.json"],
        "Native geography/methodology and pay/CV flags retained. Provisional-labelled values are identifiable provisional vintages, not proof of first-publication date. Old web-page update labels and generic October cadence do not prove old release timing.", date=date)
add("ASHE", "Residence ad hoc 11165: historical geography comparator", "11165", "2015–2017 inspected; advertised 2003–2017", "A", "Later vintage retained", ["reports/data_audits/014.2/README.md"],
    "April 2019 boundaries; separate historical comparator, not a substituted production edition. Publication in 2020 cannot establish availability in 2015–2017.", date="2020-01-23")

umb, up = audit("009.3", "archive-evidence.json")
add("Nomis UMB", "Model-based unemployment rate", "2026-11-22-task009-4", "87 rolling annual periods ending 2004-12 to 2026-06", "D", "Later vintage retained", ["reports/data_audits/009.4/validation-evidence.json", "docs/009.3-umb-unemployment-availability-and-quality-investigation.md"],
    "2026-10-20 dataset update is not a demonstrated original release date for every period. Annual overlapping reference periods, quarterly updates, missing cells and future dimension placeholders remain distinct.")
for x, date in zip(umb["archives"], ["2022-08-16", "2022-04-12"]):
    add("Nomis UMB", "M01 archived rate comparator", x["source"], "1996/97 onward; see archive source columns for end period", "A", "Later vintage retained", [up + "#/archives"],
        "Archived edition values available, not every observation's original values. Early 1996/97 is March–February; later rolling annual windows differ. Both files claim final edition; preserve note inconsistency. No automatic substitution for Nomis.", date=date)

pop, pp = audit("010", "source-investigation.json")
for e in pop["editions"]:
    year = e["latest_reference_year"]
    date = {2025:"2026-07-29", 2024:"2025-07-30", 2023:"2024-07-15", 2022:"2024-07-15"}[year]
    detailed = e["kind"] == "detail"
    indicator = "Population and migration components" if detailed else "Population, density and latest-year migration components"
    period = f"Population 2011–{year}; migration " + (f"2012–{year}" if detailed else str(year))
    add("Population/density/migration", indicator, e["edition_id"], period, "A", "Mixed vintage coverage", [pp + "#/editions"],
        "Native 2021/2023 boundary sheets remain distinct; compatible modern-code assumption is not polygon validation. Summary migration is latest-year only; revisions/Census rebasing preclude treating backcasts as original values. " +
        ("Retained cover explicitly dates replacement tables 15 July 2024, replacing 23 November 2023 tables; original 2023 values not established by that statement." if year == 2022 else "Retained cover states edition publication date."), date=date)
for edition, period, date, indicator in [("Table125", "Stock at 31 March, 2001–2025", "2026-05-21", "Unrounded dwelling stock"),
                                          ("Table123", "Financial years 2012-13 to 2024-25", "2025-11-20", "New-build completions and net additional dwellings")]:
    add("MHCLG stock" if edition == "Table125" else "MHCLG supply", indicator, edition, period, "A", "Later vintage retained", ["reports/data_audits/011/source-findings.json#/publication_evidence", "reports/data_audits/011/README.md"],
        "Retained edition includes historical revised/adjusted values; complete original archives absent. Preserve boundary, quality/imputation and precision flags. Table122 remains audit-only; identical Table123 URL aliases are one edition.", date=date)

baseline, gap_path = audit("014.10", "consolidation-validation.json")
for reference in sorted({ref.split("#")[0] for row in rows for ref in row["evidence_refs"]}):
    read(reference)
coverage = dict(ashe_incomplete_retained_inputs=baseline["ASHE_no_complete_retained_edition"],
                population_advertised_not_acquired=pop["pending_downloads"],
                note="Coverage gaps are not extra missing publication-date records; no new downloads under ISS-022.")
summary = {}
for source in sorted({r["source"] for r in rows}):
    group = [r for r in rows if r["source"] == source]
    summary[source] = dict(records=len(group), publication_counts={c:sum(r["publication_class"] == c for r in group) for c in ["A","B","C","D","N/A"]},
                           numerical_vintage_counts=dict(collections.Counter(r["numerical_vintage"] for r in group)),
                           historical_availability_assumption_required=True)
payload = dict(schema_version=1, counting_unit="Named edition or explicitly labelled history/test evidence unit; overlapping spans must not be summed as observations or interpreted as a percent of historical months",
               classification_definitions={"A":"Exact edition publication date supported", "B":"Edition publication month supported", "C":"Publication-month window supported", "D":"Publication timing unresolved", "N/A":"Not applicable with explanation"},
               inputs_sha256=inputs, records=rows, source_summary=summary, coverage_gaps=coverage,
               global_limitations="Date-level evidence is not intraday cutoff verification; identifiable edition values are not automatically original observation values. Zero C/N/A records means none justified, not missing classification work.")
(OUT / "publication-evidence-matrix.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
lines = ["| Source | Evidence units | A | B | C | D | N/A | Numerical vintage counts |", "|---|---:|---:|---:|---:|---:|---:|---|"]
for source, s in summary.items():
    counts = " | ".join(str(s["publication_counts"][c]) for c in ["A","B","C","D","N/A"])
    vcs = "; ".join(f"{k}: {v}" for k,v in s["numerical_vintage_counts"].items())
    lines.append(f'| {source} | {s["records"]} | {counts} | {vcs} |')
(OUT / "source-summary.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
print(json.dumps(dict(records=len(rows), counts=dict(collections.Counter(r["publication_class"] for r in rows)), sources=len(summary))))
