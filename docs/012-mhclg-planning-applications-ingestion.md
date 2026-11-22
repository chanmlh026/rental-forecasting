# 012. MHCLG Planning Applications and Residential Permissions Ingestion — Phase 1

## Objective

Complete Task 012 as part of **Phase 1 — Data Ingestion**, implementing reproducible ingestion of official MHCLG planning application statistics and investigating the availability of Local Authority-level residential dwelling-unit permissions.

**Important: Phase 2 — Data Preparation has already started in a separate workstream. However, Task 012 belongs entirely to Phase 1.**

All Task 012 development activity, source investigation, ingestion evidence and journal updates must remain within the established Phase 1 workflow.

Do not modify Phase 2 decisions, documentation or development history unless separately authorised.

## 1. Repository Baseline and Stage Ownership

Start from the latest clean `main`, which includes the merged Task 011 and its approved Table 123 modelling-source decision.

Before making changes:

- Read `AGENTS.md` and `docs/ENGINEERING_STANDARDS.md`.
- Review the existing Data Architecture and Dictionary.
- Review Task 006.2 planning-source investigation and retained evidence.
- Review the existing ingestion implementation and validation conventions.
- Check the Issue Register and relevant dependencies.
- Confirm the repository remains private.

### Stage ownership

This task belongs to:

**Phase 1 — Data Ingestion**

Primary development journal:

`docs/development-journal/01-data-ingestion.md`

The following journal belongs to a different stage and must not be modified:

`docs/development-journal/02-data-preparation.md`

Do not infer task ownership from whichever development journal was created or modified most recently.

Historical Phase 1 work remains Phase 1 work, even when performed after Phase 2 activities have begun.

## 2. Approved Data Sources

Primary source:

https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics

Investigate and ingest relevant official MHCLG PS1/PS2 planning statistics, prioritising PS2 residential planning application decisions.

Reuse existing repository evidence.

The previous investigation established:

- Recent PS2 coverage from 2025 Q3 to 2026 Q2.
- 294 exact project-cohort codes in each inspected quarter.
- Numeric major and minor residential granted-application measures.
- CSV encoding and preamble requirements.
- Corrected publications and potential historical definition changes.

Extend the investigation to the relevant historical series, prioritising the project modelling period beginning in 2015.

Retain earlier history where useful, without assuming that all historical definitions are comparable.

Verify source availability, access conditions, licensing and original file identity before acquisition.

## 3. Required Planning Measures

Preserve the original published measures, including:

- Major residential planning applications granted.
- Minor residential planning applications granted.
- Relevant application decisions and totals needed for reconciliation.
- Source categories, descriptions and metadata.

Maintain the distinction between:

1. Number of planning applications or decisions.
2. Number of residential dwelling units permitted.

These are different measures.

Do not convert application counts into dwelling-unit counts or treat the two as interchangeable.

Do not construct modelling features during ingestion.

## 4. Original Geography and Historical Coverage

Preserve the original Local Planning Authority identifiers, names and geographical definitions.

Measure:

- Historical quarterly coverage.
- Original authority-code availability.
- Exact-code matches against the 294-LA project cohort.
- Missing or changed identifiers.
- Category and boundary changes.
- Records outside the modelling cohort where relevant.

Do not assume Local Planning Authority responsibilities always correspond exactly to Local Authority district boundaries.

Do not implement geographical harmonisation.

All such decisions remain within the existing Phase 2 workstream.

## 5. Publication Dates, Revisions and Provenance

Preserve the available source information, including:

- Original reporting quarters.
- Period start and end dates.
- Published source values.
- Publication dates where verified.
- Retrieval timestamps.
- Release identifiers and checksums.
- Corrected or revised publication versions.
- Publisher quality indicators and missing-value markers.

Do not overwrite earlier immutable snapshots.

Do not claim complete historical point-in-time availability without supporting evidence.

## 6. Residential Dwelling-Units Investigation

Investigate whether suitable Local Authority-level residential dwelling-unit permission statistics are available.

Assess:

- Official source definitions.
- Historical coverage.
- Geographic coverage.
- Reporting frequency.
- Publication dates.
- Access and reuse rights.

The previous investigation found that England-level Glenigan rolling annual totals do not establish a suitable Local Authority-level source.

Do not infer local dwelling-unit counts from national totals or application-decision counts.

Do not acquire restricted or unapproved third-party datasets.

If a suitable source is identified, provide the evidence and seek separate owner authorisation before ingestion.

If no suitable source is available, document the finding under the existing issues and proceed with the independently authorised PS1/PS2 ingestion.

Do not delay completion indefinitely because the separate dwelling-units source remains unresolved.

## 7. Reproducible Production Ingestion

Implement ingestion consistent with existing Phase 1 architecture and engineering conventions.

Requirements:

- Immutable raw source storage.
- Validated source configuration.
- Safe HTTP metadata handling.
- Original value and metadata preservation.
- Robust parsing and schema validation.
- Historical and quarterly coverage audits.
- Duplicate detection.
- Interrupted acquisition and recovery.
- Preservation of previously validated datasets.
- Offline reproducibility.
- No unnecessary new dependencies or infrastructure.

Keep production ingestion logic within the existing `src/ingestion/` structure and use established configuration and audit conventions.

Do not introduce Phase 2 transformation or feature-engineering logic into this task.

## 8. Independent Source Validation

Produce reproducible validation evidence covering:

- Source observations against original files.
- Residential granted-application measures.
- Original reporting periods.
- Historical geographic coverage.
- Source revisions and corrections.
- Missing values and quality markers.
- Source checksums and provenance.
- Preservation of existing datasets.

Independently reconcile the ingested values with their official sources wherever practical.

Report limitations without applying premature source-quality or modelling thresholds.

## 9. Testing

Provide relevant automated tests for:

- Source parsing and encoding.
- Original measure definitions.
- Reporting quarters.
- Historical geography.
- Missing and revised observations.
- Data integrity.
- Duplicate prevention.
- Immutable snapshots.
- Recovery from failures.
- Offline reruns.
- Security and source preservation.

Run focused tests during implementation and the full regression suite at the final technical validation checkpoint.

Do not repeat expensive validation solely for documentation or PR creation if production code and validated inputs remain unchanged.

## 10. Strict Phase 1 Documentation Boundary

### Phase 1 journal

Record significant Task 012 development events in:

`docs/development-journal/01-data-ingestion.md`

Follow the existing journal conventions:

- Date and task reference.
- Event or trigger.
- Human-directed decisions.
- AI implementation and validation activities.
- Outcome and status.
- Supporting evidence and references.

Append new events chronologically and preserve existing history.

Do not duplicate the same event across stage journals.

### Phase 1 task archive

Save the original Task 012 prompt, subsequent instructions and implementation findings in the existing `docs/` task-archive convention.

Use the appropriate Task 012 document.

Do not place the Task 012 prompt or report in the Phase 2 journal.

### Phase 1 source evidence

Keep Task 012 source investigation, independent source audits and validation artefacts under the established Phase 1 audit convention, such as:

`reports/data_audits/012/`

Use existing repository conventions rather than creating a new documentation structure.

### Shared documentation

The following existing documents may be updated where necessary:

- `docs/data-architecture-and-dictionary.md`
- `docs/issue-register.md`
- `docs/task-execution-log.csv`
- `README.md`, only if required to document the new ingestion interface

These are shared project-level records, not exclusive Phase 2 documents.

Ensure updates are clearly attributable to Task 012 and Phase 1 source-ingestion findings.

**Do not modify, overwrite, reorganise or append to:**

`docs/development-journal/02-data-preparation.md`

Do not reopen, revise or implement Phase 2 methodological decisions as part of Task 012.

This includes previously recorded Phase 2 geography decisions.

If Task 012 reveals a new dependency affecting Phase 2, record the factual finding in the shared Issue Register and provide a reference for subsequent Phase 2 consideration. Do not make or implement the Phase 2 decision in this task.

## 11. Relevant Issue Management

Review applicable issues, including:

- ISS-003 — Historical geography.
- ISS-004 — Historical publication availability.
- ISS-010 — Local residential dwelling-unit source.
- ISS-011 — Data quality and source indicators.
- ISS-012 — Historical completeness.
- ISS-017 — Glenigan access and reuse permissions.
- ISS-020 — Outstanding historical security exposure.

Update the existing Issue Register using verified Task 012 evidence.

Do not create new issues unless a genuinely distinct unresolved problem requires tracking.

Do not close methodology, access or licensing issues without the required evidence and owner authorisation.

ISS-020 remains Open and the repository remains private.

## 12. Methodological Restrictions

Task 012 must not:

- Join planning data to other datasets.
- Create model-ready features.
- Standardise data frequencies for modelling.
- Harmonise Local Authority geography.
- Apply Phase 2 missing-value treatments.
- Implement point-in-time modelling joins.
- Impute values.
- Perform correlation analysis.
- Calculate planning-to-stock ratios.
- Train or evaluate models.
- Modify existing Phase 2 decisions or journal entries.

Any such work belongs to separately authorised Phase 2 tasks.

## 13. Efficient Development Workflow

### Stage A — Implementation and validation

Investigate approved sources, implement ingestion, reconcile original observations and complete required tests.

### Stage B — Documentation and Pull Request

Update Phase 1 journal entries, Task 012 evidence, shared documentation and measured execution time.

Review the final Git diff to confirm:

- Phase 1 scope only.
- Phase 2 journal unchanged.
- No unrelated preprocessing or modelling changes.
- Existing validated datasets preserved.
- No unapproved source acquisition.
- Repository remains private.

Commit and open one focused Task 012 Pull Request against `main`.

Do not rerun the full suite solely for documentation and PR preparation when earlier validation remains applicable.

### Stage C — Independent Review

Stop for owner-directed independent review.

Do not merge automatically.

## 14. Acceptance Criteria

Task 012 is ready for review when:

1. The approved MHCLG planning application sources have been ingested for verified historical coverage.
2. Original planning decisions and dwelling-unit concepts remain distinct.
3. Quarterly and geographic coverage are documented.
4. Source revisions and relevant quality indicators are preserved.
5. Independent source reconciliation passes.
6. Automated tests and data-preservation checks pass.
7. The residential dwelling-units investigation has a documented result.
8. Relevant issues are updated without premature closure.
9. All development-journal activity is recorded in the Phase 1 journal.
10. The Phase 2 journal and approved methodology remain unchanged.
11. No preprocessing, feature engineering or model training is introduced.
12. One focused PR is opened without automatic merging.

If PS1/PS2 ingestion succeeds but suitable local dwelling-unit permissions remain unavailable, report **PASS WITH CONDITIONS**, provided the limitation and its consequences are properly documented.

## 15. Final Report

Provide:

- Sources and releases ingested.
- Historical coverage and measures.
- Observation counts.
- Geography and missing-value findings.
- Independent source reconciliation.
- Tests and preservation results.
- Residential dwelling-units investigation.
- Access and licensing checks.
- Issue Register updates.
- Phase 1 journal entry reference.
- Confirmation that the Phase 2 journal was untouched.
- PR, branch and commit details.
- Actual task execution time and measurement limitations.

Classify the outcome as PASS, PASS WITH CONDITIONS, BLOCKED or FAIL.

**Task 012 remains a Phase 1 Data Ingestion task. Phase 2 Data Preparation is outside its implementation and documentation scope, except for factual updates to shared project records.**

## Implementation and validation report - 22 November 2026 (Phase 1)

**PASS WITH CONDITIONS; ready for independent owner review after PR preparation.**
Started from clean main `c242af94b3e2be21889eac4092dd4ffc185ad788` following
merged PR #11 (including the approved Table 123 policy) and PR #12 (Decision A).
Branch: `feature/012-mhclg-planning-ingestion`. Repository private; ISS-020 Open.
This task is Phase 1; Phase 2 documentation/history and approved methodology
are preserved, regardless of the more recent Phase 2 journal creation.

### Source contract and coverage

Implemented `src/ingestion/mhclg_planning.py` and a checksum-pinned JSON
inventory under the existing source-I/O, storage and audit conventions. Eleven
immutable raw bundles retain the official full/recent PS1/PS2 CSVs, district
dictionary, publication/technical/statistical documents, terms and robots.
The prior Task 006.2 evidence was reviewed; its CSV bytes were not present in
the clean checkout, so the current four approved files were acquired once.
Completed acquisition was reused on all subsequent inspections/runs.

- PS1 full: **42,861 authority-quarter rows, 121 quarters, 1996 Q2-2026 Q2**;
  88 count fields plus original metadata.
- PS2 full: **68,583 authority-quarter rows, 189 quarters, 1979 Q2-2026 Q2**;
  329 count fields including residential major/minor granted/refused/decisions,
  totals and time/category breakdowns.
- Recent PS1 and PS2: **1,240 rows each**, 2025 Q3-2026 Q2, retained as separate
  overlapping audit assets; not appended to histories.
- All assets: **113,924 source rows**, **26,852,655 count cells** comprising
  **14,816,586 numeric** and **12,036,069 literal `..` markers**. All original
  region/name/code, quarter and financial-year fields remain available.

Original `*_source` and parsed `*_values` tables remain separate, with native
record/line identity, reporting dates and source checksum/retrieval provenance.
Coverage, geography, schema and documents complete **12** tables per layer.
The CLI uses existing storage TOML and optional inventory/reference arguments.
Original count definitions and all source strings remain unchanged; no
application count is converted to dwelling units or modelling features.

### Source findings and limits

PS1's third preamble record is a PDR definition-change note, so its header is
record four; PS2's header is record three. Original cp1252 text, note typo and
financial-year labels remain literal. Categories/collection change historically;
PS1 end-quarter applications are no longer collected after April 2014. Missing
markers are not zero and numeric values can reflect publisher imputation.

Exact cohort-code matches range **249-294 PS1 / 238-294 PS2**, and **283-294
for both from 2015 Q1**. The recent four quarters have 294 exact codes and numeric
major/minor residential granted counts. All noncohort LPA/development-corporation/
national-park/predecessor observations remain. LPA responsibilities are not
automatically whole-LAD boundaries. The full files include **3,678 PS1 and 9,000
PS2 rows without syntactically valid GSS codes**. Fifteen identical PS1 Shepway
row pairs in 1996 Q2-1999 Q4 are retained/flagged, not deduplicated. PS2 includes
1,905 rows in 83 quarters sharing missing-code marker `-`; original record
identity prevents conflation of distinct observations. No geography mappings.

Release first publication is **24 September 2026**; the **29 October 2026**
change log corrects **Table 3b of the statistical release**, not a verified
PS1/PS2 CSV revision. Original-offset first/public/internal document timestamps
remain separate; source quarters and filenames do not establish original
release dates. Historical source values are retrospective and can be revised/
re-imputed; earlier release versions/complete PIT availability remain unverified.

### Dwelling-unit investigation and dependency outcome

Official PS1/PS2 describe applications/decisions; national Glenigan rolling
units do not provide the required LA total-residential units series. Current
technical notes identify annual LAHS Section I **affordable-housing** units
granted permission as a partial official candidate. Its restricted concept is
not an all-residential substitute; permission-field history, coverage, detailed
definitions/revisions and extract-specific rights are not verified. No LAHS
data or restricted third-party extract was acquired. Separate owner approval
is required before candidate ingestion.

**Proceed with documented limitations:** ISS-003 (native geography retained),
ISS-004 (historical availability), ISS-011 (source quality) and ISS-012 (coverage)
remain Open. ISS-010 (local all-residential units) and ISS-017 (potential Glenigan
local extract rights) remain Open; neither blocks independent PS1/PS2 work.
ISS-020 remains Open; ISS-022 remains ONS-specific and no ONS request occurred.
No new issue or premature closure. Rights/access evidence is in the
[source findings](../reports/data_audits/012/source-findings.json): applicable
GOV.UK paths not disallowed by generic robots rules, Crown/OGL v3.0 attribution/
exceptions checked, no inferred third-party rights or invented contact details.

### Tests, source reconciliation and preservation

**39 focused tests passed in 1.20 seconds; 343 full regression tests passed in
67.23 seconds** at the final technical checkpoint. Coverage includes encoding/
preambles, source definitions/periods, historical row ambiguity, missing/zero/
negative values, immutable revised snapshots, interrupted recovery/offline
reuse, corruption, invalid inventories, bounded HTTP/Retry-After, incomplete
responses, redirects and header safety.

Independent pandas parsing/header discovery reconciles **27,422,275 native
source fields**, all parsed numeric/missing cells, source and reporting-period
identities, flags and **318** quarterly coverage records. The independent audit
initially stopped before source comparison on a BOM-prefixed reference header;
its reader was corrected and regression-tested, preserving the diagnostic
receipt and all source/production/reference bytes. Absent document dates were
normalised to standard JSON nulls in the receipt writer only; comparison results
were unchanged. The successful full audit is not represented by the old failure.

Recent/full assets agree across 2,480 rows and **524,520 non-key fields**,
without assuming unrelated request/provenance metadata equivalence. All **12**
validated/processed tables agree. An offline rerun with a downloader that raises
preserves all **471** data files, including **423 pre-task** files. Before/after
hashes confirm the Phase 2 journal and pinned reference unchanged. Dictionary
Decision A and the approved Table 123 policy also remain unchanged.

Project-source and cleaned-local-history Gitleaks scans pass with zero findings;
11 raw checksums/safe HTTP metadata checks, offline lock, Black, whitespace and
Git integrity checks pass (informational dangling objects only). These do not
certify erasure of retained old remote history/caches/external copies; ISS-020
remains Open. Final staged/documentation review follows without a full-suite or
ingestion repeat solely for PR preparation. No dependencies/infrastructure,
source-data correction, harmonisation, joins, ratios, imputation or modelling.

### Evidence, journal and timing checkpoint

[Source/reproduction index](../reports/data_audits/012/README.md),
[passing audit](../reports/data_audits/012/validation-evidence.json),
[initial BOM diagnostic](../reports/data_audits/012/validation-blocker.json),
[security receipt](../reports/data_audits/012/security-validation.json) and
[pre-task preservation hashes](../reports/data_audits/012/preservation-before.json)
retain the reproducible evidence. Significant development activity is recorded
only in the [Phase 1 journal](development-journal/01-data-ingestion.md). The
Phase 2 journal is untouched; source and preprocessing decisions are unchanged.

UTC clock-tool start **2026-11-22T12:58:38+00:00**. Source implementation, tests
and offline validation checkpoint **2026-11-22T13:14:30+00:00**: **952 seconds /
60 = 15.866667 minutes**. Stage B documentation, final security/scope checks and
PR preparation continues from that measured checkpoint. Test durations are
within wall-clock totals, not added again. Tool/network/access-review waits
are included, not separately measured/subtracted. Final measured total and
independent-review receipt follow; no automatic merge is authorised.
