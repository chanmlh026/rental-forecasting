# 011. MHCLG Housing Supply and Dwelling Stock Production Ingestion

## Objective

Implement production-ready, reproducible ingestion for three official MHCLG housing datasets:

- Table 122 — Net additional dwellings.
- Table 123 — Housing supply components, including new-build completions.
- Table 125 — Dwelling stock, including vacant dwellings.

Preserve original source values, historical periods, geography, revisions, imputation indicators and publisher notes.

Do not perform preprocessing, geographic harmonisation, feature engineering or modelling.

## 1. Project Baseline

Start from the latest clean `main`, following the merge of PR #10.

Before implementation:

- Follow `AGENTS.md` and `docs/ENGINEERING_STANDARDS.md`.
- Review the existing Data Architecture and Dictionary.
- Review the relevant source investigations and evidence.
- Review existing ingestion architecture, tests and storage conventions.
- Check the Issue Register and applicable dependencies.
- Confirm the repository remains private.

Reuse established ingestion infrastructure wherever appropriate.

Archive the original task prompt and follow existing documentation and execution-time requirements.

## 2. Approved Sources

Use the official MHCLG publications:

**Table 122 and Table 123**

https://www.gov.uk/government/statistical-data-sets/live-tables-on-net-supply-of-housing

**Table 125**

https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants

Verify current publisher access conditions, licensing requirements, file identities and source versions before acquisition.

Use source files and historical coverage already investigated in the repository as the initial baseline.

Do not substitute unofficial datasets without owner approval.

## 3. Required Source Measures

### Table 122 — Net Additional Dwellings

Preserve annual net additions and relevant original published components.

- Reporting period: April–March financial year.
- Previously inspected history: 2001–02 to 2024–25.
- Geographic level: English Local Authority district.

Net additions may be negative and must not automatically be treated as invalid.

Preserve the distinction between net additions and new-build completions.

### Table 123 — New-Build Completions

Preserve the published `New build` component and associated source information.

- Reporting period: April–March financial year.
- Previously inspected history: 2012–13 to 2024–25.

Retain relevant source components, annotations, imputation indicators and original workbook formatting where necessary to interpret the data.

Do not confuse annual new-build completions with quarterly housebuilding statistics.

### Table 125 — Dwelling Stock

Ingest the published unrounded dwelling stock observations.

- Reference date: 31 March.
- Previously inspected history: 2001–2025.
- Measure: total dwelling stock, including vacant properties.

Retain relevant rounded values where needed for source audit, while preserving the unrounded observations as the intended future denominator candidate.

Do not confuse dwelling stock with the number of households or private rented properties.

Do not calculate housing supply ratios in this task.

## 4. Historical Coverage and Geography

Preserve the original source geography and its historical changes.

The existing investigation identified different exact-code coverage across historical years, including newer authorities and predecessor areas.

Requirements:

- Retain published LA codes and names.
- Preserve original geographic periods and definitions.
- Measure exact matches against the approved 294-LA reference.
- Report unmatched and historically changed identifiers.
- Preserve source observations that cannot yet be mapped.
- Distinguish code discrepancies from genuinely missing data.

Do not apply geographic mappings or boundary adjustments.

Geography harmonisation remains a Phase 2 decision under ISS-003.

## 5. Data Acquisition and Provenance

Implement reproducible acquisition and immutable source storage.

For each source file:

- Record the official URL and source identity.
- Preserve the original source file.
- Record retrieval timestamp and checksum.
- Retain publication and revision information where available.
- Preserve relevant source notes and footnotes.
- Validate schema and expected source structure.
- Support safe retries, interruptions and recovery.
- Prevent overwriting of previously validated releases.

Respect publisher rate limits and applicable access conditions.

Do not retain unsafe HTTP metadata or credentials.

Maintain separate source vintages where appropriate.

## 6. Source Quality Preservation

Pay particular attention to the known MHCLG data-quality limitations.

These include:

- Publisher imputation indicators.
- Cell colouring and formatting used to identify imputed values.
- Provisional or revised observations.
- Census-related stock adjustments.
- Changing housing-supply components.
- Historical notes and inconsistent note-year labels.
- Negative net additions.
- Missing values and changes in geography.

Where cell formatting carries meaning, preserve enough original formatting information to reconstruct the published quality indicators.

Do not silently discard flagged values.

Do not invent completeness, outlier or confidence thresholds.

## 7. Dataset Validation

Provide independent source reconciliation for each table.

### Table 122

Verify:

- Financial-year coverage.
- Published net additions.
- Relevant source components.
- Negative-value preservation.
- Geography and historical coverage.

### Table 123

Verify:

- `New build` identification by source sheet and year.
- Published completion counts.
- Imputation and style indicators.
- Original source annotations.
- Historical geography coverage.

### Table 125

Verify:

- Unrounded dwelling stock values.
- Correct 31 March reference dates.
- Original source geography.
- Publisher revisions and Census-related notes.
- Historical coverage.

### Cross-Dataset Checks

Assess whether relevant records use compatible:

- Geography.
- Reporting periods.
- Measurement definitions.
- Publication vintages.

Report inconsistencies without performing transformations to eliminate them.

Do not construct supply-per-stock ratios or assume stock changes must equal reported net additions.

## 8. Automated Tests

Implement focused tests covering:

- Source identification and schema changes.
- Historical periods.
- Original geography preservation.
- Numeric and missing values.
- Negative net additions.
- Publisher imputation indicators.
- Workbook formatting and notes.
- Revision preservation.
- Duplicate observations.
- Interrupted acquisition.
- Immutable snapshots.
- Offline reproducibility.
- Existing-data preservation.

Run focused tests during development.

Run the full regression suite and relevant independent source audits once the implementation reaches the final validation checkpoint.

Avoid unnecessary repeated tests when code, source inputs and configuration remain unchanged.

## 9. Methodological Restrictions

Do not:

- Calculate new housing-supply ratios.
- Select stock denominator timing.
- Harmonise LA geography.
- Impute missing values.
- Apply statistical outlier filtering.
- Combine incompatible source vintages.
- Join the datasets to rental targets.
- Conduct correlation or feature selection.
- Train forecasting models.
- Change existing predictor definitions without approval.

The proposed denominator timing and any supply-stock compatibility decisions remain for Phase 2.

## 10. Issue Management

Review and update relevant issues:

- ISS-003 — Geographic compatibility.
- ISS-004 — Historical availability and vintages.
- ISS-011 — Publisher quality and imputation indicators.
- ISS-012 — Historical completeness.
- ISS-020 — Outstanding repository security exposure.

Review ISS-022 only for any actual applicability to the sources used; do not extend an ONS-specific restriction to MHCLG without evidence.

Record significant new findings in the existing Issue Register.

Do not close issues merely because ingestion succeeds.

Keep ISS-020 Open and the repository private.

## 11. Efficient Development Workflow

Use three stages.

**Stage A — Implementation and validation**

Acquire and validate the approved source files, implement ingestion, create reproducible audits and run required tests.

**Stage B — Documentation and PR**

After validation:

- Complete necessary task documentation.
- Update the Data Dictionary and development journal.
- Record actual execution time.
- Check the final diff and security implications.
- Commit, push and create one PR against `main`.

Do not repeat the full regression suite solely for documentation or PR creation unless previous evidence has been invalidated.

**Stage C — Independent Review**

Stop for independent owner review.

Do not merge automatically.

## 12. Acceptance Criteria

Task 011 is ready for independent review when:

1. All three approved MHCLG source tables are ingested for their verified accessible historical scope.
2. Original values, source geography, reference periods and revisions are preserved.
3. Imputation and publisher quality indicators are retained.
4. Independent source reconciliations pass.
5. Historical coverage and geography discrepancies are documented.
6. Automated tests and offline reproducibility checks pass.
7. Previously validated datasets remain unchanged.
8. Relevant documentation and issues are updated.
9. Source access, licensing and security checks are completed.
10. One PR is opened without automatic merging.

If critical validation fails, preserve the evidence and report the blocker instead of forcing completion.

## 13. Final Report

Provide:

- Source files and editions ingested.
- Historical coverage by table.
- Total observations and geographic coverage.
- Missing values and source quality flags.
- Original and unmatched LA identifiers.
- Revisions and publication limitations.
- Independent source reconciliation results.
- Test results.
- Data preservation evidence.
- Access and licensing findings.
- Issue Register changes.
- Outstanding owner decisions.
- Branch, commit and PR information.
- Measured task execution time and limitations.

Classify the outcome as **PASS**, **PASS WITH CONDITIONS**, **BLOCKED** or **FAIL**.

Do not describe source-level ingestion as a completed modelling dataset.

## Implementation and validation report - 22 November 2026

**PASS WITH CONDITIONS for source-level ingestion.** All three approved tables
are ingested and independently reconciled. Native cross-publication precision,
publisher quality/notes, historical geography and availability limitations remain
conditions; no modelling dataset or supply/stock ratio is produced.

### Baseline, source identity and access

PR #10 was verified merged as **88a8d9ff6805779ad34d25dc6b5f16b3fdfd507d**.
Private clean main was fast-forwarded to that baseline before creating
`feature/011-mhclg-housing-ingestion`. Initial working tree was clean. The original
pre-remediation checkout was untouched. The supplied attachment is archived
verbatim above and measured work uses the existing single CSV row for Task 011.

The two owner-approved GOV.UK pages were inspected before acquisition, together
with [GOV.UK terms](https://www.gov.uk/help/terms-conditions) and robots rules.
Official MHCLG/GOV.UK material is Crown copyright/OGL v3.0 with attribution and
exceptions; publisher/data identity and source notes are retained. The checked
robots rules do not disallow the approved paths. No account, credential, cookie
replay, personal contact or unapproved alternate dataset was used. Serial
requests, a non-personal descriptive User-Agent, ordinary TLS and bounded retries
respect Retry-After (long waits/access denial stop rather than bypassing limits).
ISS-022 was reviewed for actual applicability: no checked evidence extends the
ONS-specific contact restriction to MHCLG/GOV.UK. No ONS requests were made and
ISS-022 remains Open in its original scope.

Nine immutable raw bundles are retained: two publication pages, terms, robots,
and five attachment URLs representing three distinct ODS workbooks. The two pages
cross-link Tables 122/123 using different asset IDs; each pair was verified
byte-identical. Both request identities/checksums/timestamps are preserved and only
three distinct workbooks are parsed. An initial discovery identity assertion
stopped on the different URLs; raw comparison established aliases rather than
an unapproved source replacement. No successful request was needlessly repeated.

The current cover publication dates are **20 November 2025** for Tables 122/123
and **21 May 2026** for Table 125. The stock page's later update date is separately
preserved, not used as proof of a changed Table 125 release. Source reference
periods, publication strings and retrieval times remain distinct. Historical
provisional/revised flags and Census-related notes are retained, without claiming
a complete first-publication/vintage archive or choosing an availability lag.

### Implementation and storage

`src/ingestion/mhclg_housing.py` implements a source-specific acquisition boundary
for the approved GOV.UK/official-assets hosts, pinned inventory validation and native
ODS parsing. It reuses existing immutable publication/checksum/safe-HTTP primitives,
`configs/storage.toml`, the approved geography reference and existing dependencies.
No shared ingestion module, dependency, infrastructure or earlier dataset changed.
`configs/mhclg_housing_sources.json` pins each inspected asset hash, exact source
table/title/header and byte-identical alias relationship.

The sparse ZIP/XML reader expands meaningful logical rows/cells while avoiding
allocation of repeated empty spreadsheet grids. Original ODS explicit spaces,
tabs/line breaks and style inheritance are preserved. Stored numeric XML literals
and displayed text remain separate; formulas retain their source expression and
cached published value, without recalculation. Missing and `[x]` source markers
are not replaced by zero, and negative net additions remain valid numeric values.

Seven identical validated/processed source tables are published under the existing
`mhclg_housing/snapshot=2026-11-22-task011/` layers:

- `observations`: source table/sheet/row/column identity, original current/former/
  DCLG codes and names, source level evidence, measure, financial-year dates or
  31 March stock date, unit, exact XML/value/display/formula data, inherited style
  evidence, original cell XML, markers/linked notes, quality flags and complete
  request/checksum/retrieval provenance.
- `coverage`: source/target-code and numeric/marker coverage by native table,
  sheet, measure and period, with unmatched identifiers and imputation-signal counts.
- `geography_audit`: original source rows/codes/names and exact-reference matches,
  with no mapping applied. Unmatched target IDs remain in coverage reports.
- `notes`: original cover, Notes, contents, preambles/headers/footer cells and XML.
- `styles`: original named/automatic style and numeric-format definitions in XML;
  observations also carry resolved inherited properties and style provenance.
- `schema`: exact inspected headers/titles, source row counts and periods.
- `documents`: original retained publication/policy text, URLs and source provenance.

Raw ODS files preserve the complete workbook, including original annotations,
all source styles/formatting and worksheets. Same-argument reruns reuse verified
requests; interrupted acquisition/publication retains successful requests and
validated outputs. Corrupted/changed sources, schemas, references or completed
outputs fail closed. New bytes/contract changes require review and a new snapshot,
never overwriting a validated release. Raw/data outputs remain ignored by Git.

### Historical coverage and publisher quality

| Source | Verified history | Observations | Geography evidence |
|---|---|---:|---|
| Table 122, LT_122 | FY 2001-02 to 2024-25 | 10104 | 421 native rows, 417 GSS codes plus uncoded aggregates |
| Table 123, 13 annual sheets | FY 2012-13 to 2024-25 | 70546 | 377 distinct GSS codes across history; rows/components vary by year |
| Table 125, rounded/unrounded | 31 March 2001-2025 | 21350 | 427 coded areas per sheet, including predecessor/aggregate areas |

Total **102000** observations comprise **98366** numeric cells and **3634** source
markers. Latest direct target-code coverage is **292**. Historical numeric target
coverage reproduces Task 006.2: Tables 122/125 **272-292**, and Table 123 `New build`
**277-292**. Exact current-code matches with historical `[x]` values are reported
separately from codes not present in a year-specific sheet. Native rows with
legacy IDs or no GSS code are retained with original row identity. Barnsley/
Sheffield and the first-year Gateshead code discrepancies remain unresolved;
source names are not a mapping or proof of effective-boundary equivalence.

Table 123 retains all published source components/PDR columns, not only New build;
new build is identified by its source header per year. Its annual financial-year
measure is not the quarterly housebuilding return. Component additions/removals,
Census adjustments and manual publisher notes remain separate source information.
Two 2020-21/2021-22 headers say only `Of which under PDR`; the literal auxiliary
label is retained without inferring a subtype. Table 125 unrounded observations
are identified as a future denominator candidate, with rounded values separate
for audit; neither is a household count or private-rented-only measure.

Original cell styling explicitly identifies **451** red-filled imputation cells;
**584** cells carry imputation authority/year row notes. Their union is **584**.
These signals and the source's warning about authority-level interpretation are
preserved separately; the combined flag is True when explicitly signalled and
null otherwise, not proof that unflagged data are unimputed. Table 122 historical
narrative lists remain linked through period notes without declaring every
observation in those periods imputed. No values are dropped or corrected.

Table 123's provisional/revised Notes year labels lag later source sheets: **7216**
and **7544** observation flags respectively. Table 125 unrounded repeats rounding
wording, flagged on **10675** observations while retaining the original unrounded
numbers. These inconsistencies are preserved for later interpretation under
ISS-011. Source rounding never establishes Census accuracy or a new quality cutoff.

### Independent reconciliation and cross-dataset assessment

The independent audit uses separate ODS XML/value/repeated-cell/style resolution
logic, without calling production parsing/field/style helpers. It reconciles all
**102000** source cells, **589** original note cells and **276** coverage rows,
including source values/precision, display text, identifiers, periods/units,
formulas, inherited styles, imputation indicators and request provenance. The two
official asset aliases are independently hash-verified; source observations and
request identities are validated separately. All seven validated/processed tables
agree. A downloader that raises on acquisition verifies offline rerun: **423**
data files remain byte-for-byte unchanged, including **388** pre-task files and
all nine raw bundles. No data changed to obtain a successful comparison.

The initial cross-table audit incorrectly asserted unconditional equality between
stored Table 122 and Table 123 net totals. It stopped before offline rerun, and
its original full failure receipt was preserved with a checksum under ignored
`data/validation_reports/`; the small historical receipt links that artifact.
Read-only diagnosis verified native integer versus fractional unrounded storage:
for example, England FY 2012-13 is stored as **130611** in Table 122 and
**130611.10963238429** in Table 123, while both display **130,611**. Table 123's
cover explicitly states figures are unrounded and retains Census-adjustment
context. Some half-dwelling cases have different displayed rounding as well.

Among **4530** numeric same-code/period comparisons, **2925** stored values differ;
maximum observed absolute difference is **0.5 dwelling**, and **98** displayed
values also differ. These are observed facts, not a new tolerance or certified
universal rounding mechanism. The unsupported equality gate was replaced by the
owner-requested compatibility report. Both sources, raw literals and display
strings remain unchanged; no rounding, adjustment, preferred value or synthetic
reconciliation is introduced. Mandatory exact reconciliation against each source's
own XML remains a hard gate. The historical stopped-gate receipt is not erased or
rewritten as a source-data equality PASS.

All units are dwellings, but financial-year flows and 31 March stock have distinct
periods, publisher revisions/Census calibration and publication vintages. The
assessment does not assert stock changes equal net additions, select stock timing
or construct ratios. Future compatibility/precision/source selection belongs to
the approved Phase 2 checkpoint under ISS-009/011; current source-preserving
ingestion can proceed with documented limitations without resolving that decision.

### Tests, recovery and security

- **36 focused MHCLG tests passed in 3.53 seconds**, covering original/native
  periods/codes, negative/missing values, inherited red styles, row imputation notes,
  notes/formats, stock sheets/revisions, source/schema changes, duplicates, sparse
  repeated cells, interrupted acquisition/publication, immutable outputs, offline
  reuse, corruption, unsafe headers and bounded/terminal HTTP handling.
- **302 full regression tests passed in 53.16 seconds** for the final production
  implementation/configuration. After diagnosis of the unsupported cross-table
  audit, **two additional focused audit regression cases passed in 0.60 seconds**.
  Production code/configuration/data were unchanged by that audit correction;
  no unnecessary full-suite rerun was performed.
- Preliminary production gates stopped on explicit ODS spacing omitted by initial
  inspection and on a literal standalone PDR label. Source hashes/values did not
  change; corrected exact representations and focused tests passed before output
  publication. Preserved diagnostic evidence explains both stops.
- Project-source and cleaned-local-history Gitleaks 8.30.1 scans passed with zero
  findings, using the existing official checksum-verified tool. Raw checksums and
  safe HTTP metadata were inspected directly. Lock/Black/whitespace checks and
  `git fsck --strict` passed (only informational dangling objects). Final staged
  checks/documentation review follow without another source/full-test rerun.

These checks do not certify removal from retained old remote PR/history/caches
or external copies; ISS-020 remains Open. No credential/session replay, history
rewrite, visibility change, unapproved source or deployment was introduced.

### Dependencies, evidence and timing checkpoint

Proceed with documented limitations. ISS-003/004/009/011/012 remain Open with new
source/compatibility/quality evidence. ISS-020 remains Open. ISS-022 was reviewed
and remains ONS-specific; it is not an MHCLG ingestion blocker. No new overlapping
issue or issue closure is required. No current owner decision is needed to retain
these native source inputs; geographic harmonisation, historical availability,
precision/compatibility policies and stock denominator timing remain future owner
decisions. No growth, ratio, imputation, target join, correlation or model is made.

[Reproduction and evidence index](../reports/data_audits/011/README.md) links the
source investigation, exact schema corrections, preserved historical failure,
passing audit, source findings, security evidence and pre-task checksums. The
original task and acceptance criteria above remain verbatim. The dedicated branch
will be committed/pushed and one PR opened for independent review; no automatic
merge is authorised.

Stage A source investigation/implementation, tests, offline audit/diagnosis and
security: **2026-11-22T10:29:47+00:00 to 2026-11-22T10:57:35+00:00**,
**1668 seconds / 60 = 27.800000 minutes**. Whole-second UTC clock-tool precision.
Measured test durations are evidence within the continuous stage, not extra
time added to it; separate activity/wait intervals were not timed. Tool/network/access-review waits are included,
not separately timed or subtracted. Stage B documentation/PR preparation begins
at that cutoff; final total and review receipt follow below. Stage C owner review
is pending and has not been timed.


## Independent-review handoff and final timing - 22 November 2026

**Completed; PASS WITH CONDITIONS for source-level ingestion.** Implementation
commit **d5d81d04a9d682598ad96346020a37505eb94fc4** is pushed on
`feature/011-mhclg-housing-ingestion`. [PR #11](https://github.com/chanmlh026/rental-forecasting/pull/11)
targets unchanged cleaned main **88a8d9ff6805779ad34d25dc6b5f16b3fdfd507d**.
GitHub confirms OPEN, unmerged and mergeable; repository private and auto-merge
disabled. The PR contains 20 authorised implementation/configuration/test/audit/
documentation files, no datasets or unrelated ingestion/dependency changes.
The original full stopped-gate artifact remains in ignored validation reports,
linked by its checksum-preserving historical receipt. Source values remain intact.

Independent owner review is the next checkpoint; no merge was requested or
performed. Native precision differences, geography/quality/availability issues
and denominator decisions remain explicit conditions under the existing issues;
no issue is closed. ISS-020 remains Open and ISS-022 stays ONS-specific. There is
no outstanding critical per-source ingestion discrepancy; future feature/input
compatibility decisions are not implied by ingestion success. No model-ready
claim, source substitution, ratio or denominator date is introduced.

No full-suite or ingestion rerun was performed solely for documentation/PR
preparation. Exact validated code/configuration hashes, source evidence, prompt/
CSV, Markdown/link/UTF-8/table and final staged secret/whitespace checks passed.
The status API reports no commit statuses and no CI workflow is configured;
302 local regression tests plus two focused audit tests are not represented as CI.
A transient first Git push DNS/thread failure was retried successfully without
changing the commit or data.

| Measured stage (UTC) | Recorded interval | Minutes |
|---|---|---:|
| A: source investigation/implementation/testing/audits/security | 2026-11-22T10:29:47+00:00 to 2026-11-22T10:57:35+00:00 | 27.800000 |
| B: documentation and PR preparation | 2026-11-22T10:57:35+00:00 to 2026-11-22T11:08:02+00:00 | 10.450000 |
| Total measured session | 2295 seconds divided by 60 | 38.250000 |

Whole-second UTC clock-tool precision; one continuous work session. Reported test
durations are within the stage totals, not extra time added to them. Tool/network/
access-review waits and the initial push retry are included, not separately timed
or subtracted; no active-CPU estimate or separate overlapping interval is inferred.
Cutoff follows implementation push, PR creation and metadata/privacy/status checks.
This final receipt/timing/evidence-note write, documentation-only commit/push,
remote read-back and final response are outside the cutoff. Stage C independent
review remains pending and is not timed. The single shared Task 011 CSV row
retains this actual start/end/duration and Completed status.
