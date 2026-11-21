# 008. Ingest ONS CPI/CPIH Inflation and UK House Price Index Data

## Objective

Implement reliable, reproducible, production-ready ingestion for two groups of official UK datasets:

1. ONS Consumer Prices Index (CPI) and Consumer Prices Index including owner occupiers' housing costs (CPIH).
2. HM Land Registry / ONS UK House Price Index (UK HPI).

The task covers source retrieval, historical data, revisions, provenance, data validation and structured outputs.

**Do not implement feature engineering, forecasting, statistical correlation analysis or model training.**

## 1. Project Context

Before starting, review:

- `AGENTS.md` and `docs/ENGINEERING_STANDARDS.md`.
- `docs/data-architecture-and-dictionary.md`.
- `docs/issue-register.md`.
- `docs/development-journal/01-data-ingestion.md`.
- Existing ONS PIPR and Bank of England ingestion implementations.
- Related tests, storage configuration and task execution conventions.

Use the current merged `main` branch as the baseline.

Reuse existing engineering patterns where appropriate. Keep the inflation and HPI source contracts and validation results independently identifiable.

Check relevant issue dependencies and official source access/licensing before implementation.

## 2. Approved Dataset Selection

### 2.1 ONS CPI and CPIH

Ingest the following four official monthly time series:

| Measure | ONS series ID | Units |
|---|---|---|
| CPI all-items annual inflation rate | `D7G7` | % |
| CPI all-items index | `D7BT` | Index |
| CPIH all-items annual inflation rate | `L55O` | % |
| CPIH all-items index | `L522` | Index |

Official sources:

- https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23
- https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23
- https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l55o/mm23
- https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l522/mm23

Requirements:

- Retrieve official monthly observations using a reliable publisher-supported interface or download.
- Verify the series identifiers, units, index bases and reference periods against source metadata.
- Preserve published annual inflation rates rather than unnecessarily recalculating them.
- Preserve index levels and annual inflation rates as distinct measures.
- Preserve the available full historical monthly series, subject to documented source boundaries.
- Preserve source edition or vintage metadata and relevant corrections.
- Distinguish original observation dates from publication dates and retrieval timestamps.

Do not assume the historical observations were publicly available during their reference months.

Do not impose a fixed historical start date without inspecting and documenting the official source.

### 2.2 UK House Price Index

Use the official HM Land Registry / ONS UK HPI.

Approved measures:

- All-property average house price in GBP.
- All-property house price index, preserving the published index base.

Geography:

- English Local Authority level.
- The existing approved forecasting cohort of 294 Local Authorities.
- Preserve official area identifiers and names.

Initial official release reference:

https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-september-2026

Before implementation, verify the available source files, their identifiers, schemas, geographic scope and historical coverage.

Requirements:

- Retrieve the official monthly HPI dataset and relevant revision information.
- Retain raw official source observations rather than silently limiting the source dataset to current Local Authority boundaries.
- Produce an appropriately identified 294-authority cohort output or coverage view using only verified geographic matches.
- Preserve historical area codes, source geography and relevant methodological changes.
- Identify missing months, missing authorities, duplicates and geography changes.
- Do not automatically map or combine historical authorities without a verified, owner-approved methodology.
- Preserve revisions and original source release evidence where available.

Do not infer that historical coverage is complete merely because the dataset has a long published history.

## 3. Project-Owner Decisions and Rationale

Record the following approved methodological decisions and their stated rationale in the Data Ingestion Development Journal.

### Decision 1 — Ingest both CPI and CPIH

The project owner approved retaining both inflation measures.

**Rationale:** The ingestion stage is intended to collect potentially relevant official predictors without prematurely deciding which is statistically useful. CPI and CPIH represent related but different inflation concepts. Their usefulness, overlap with rent data and potential correlation will be examined during later preprocessing or modelling.

### Decision 2 — Retain inflation rates and index levels

The project owner approved preserving both published annual inflation rates and underlying index levels.

**Rationale:** Retaining the original measures provides flexibility for later feature development without requiring premature decisions about the final model inputs.

### Decision 3 — Retain all-property UK HPI measures

The project owner approved collecting all-property average prices and index levels for the English Local Authority cohort.

**Rationale:** Local house prices may provide information about property-market conditions relevant to rental forecasting. Their predictive usefulness is not yet established and should be evaluated later.

### Decision 4 — Preserve source revisions and limitations

The project owner approved retaining original source snapshots and available historical revision information.

**Rationale:** Historical revisions must remain traceable so future preprocessing and backtesting can distinguish what was observed at a given reference period from what was actually available at a forecast cutoff.

### Recording Rules

- Attribute these decisions to the human project owner.
- Distinguish the owner's decisions from ChatGPT recommendations and Codex's implementation activities.
- Record facts and stated reasoning without introducing speculative interpretations.
- Do not draw conclusions about the project's AI-efficiency or AI-enablement hypotheses.

## 4. Data Ingestion Requirements

Implement source-specific ingestion components using existing project conventions.

The pipelines must support:

- Official source retrieval.
- Immutable raw snapshots.
- Validated and processed structured outputs.
- Source version and release identification.
- Source provenance and checksums.
- Repeatable execution.
- Safe retries and recovery.
- Clear logging and failure reporting.

Reuse `configs/storage.toml` and the existing raw, validated and processed storage architecture.

Avoid additional storage frameworks or unnecessary duplication.

The implementation should remain suitable for future GCP deployment without adding cloud infrastructure during this task.

## 5. Historical Revisions and Point-in-Time Integrity

Retain available historical source vintages, revision information and publication evidence.

The exact first-release selection policy approved for IUMZID4 does **not automatically apply to CPI, CPIH or UK HPI**.

For these new datasets:

- Preserve original source values from each retained release.
- Capture documented corrections and revisions when available.
- Distinguish reference month, source edition, release date and retrieval time.
- Do not overwrite historical source snapshots with subsequent releases.
- Do not assume current revised values were historically available.
- Do not invent unavailable publication timestamps.
- Document the limitations of historical vintage availability.

If reconstructing earlier releases is technically impractical or incomplete, document the limitation and preserve what is verifiable.

Do not implement an unapproved first-release selection or historical adjustment policy.

Exact forecast-cutoff treatment remains a later methodological decision under the existing point-in-time governance.

## 6. Data Quality and Validation

### Inflation

Validate:

- Correct ONS series identity.
- Correct measure descriptions and units.
- Monthly observation dates.
- Historical coverage and continuity.
- Duplicate or missing observations.
- Numeric validity.
- Index-base consistency.
- Publication/revision metadata where available.

Independently reconcile selected observations against official ONS tables.

### UK HPI

Validate:

- Correct all-property measures.
- Prices in GBP and published index units.
- Official area codes and names.
- Monthly reference dates.
- Historical coverage by Local Authority.
- Exact matches against the approved 294-authority cohort.
- Missing or unmatched authorities.
- Geographic code changes.
- Duplicate or conflicting observations.
- Source revisions, release editions and metadata.

Produce a reproducible coverage report by observation month and authority.

Do not silently discard unmatched areas or fabricate historical values.

### Reliability

Test normal operation, malformed source data, incomplete downloads, source changes, interrupted runs, immutable snapshot conflicts and recovery.

Follow existing test conventions and provide reproducible evidence.

Do not introduce arbitrary correlation thresholds, statistical significance tests or feature-selection criteria during ingestion.

## 7. Outputs and Documentation

Produce structured datasets suitable for future preprocessing.

Use appropriate Parquet schemas and retain original source precision or textual values where necessary for reconciliation.

Document:

- Official source URLs and retrieval methods.
- Source definitions and units.
- Output schemas.
- Historical coverage and observation counts.
- Geographic coverage and gaps.
- Source publication and revision limitations.
- Validation findings.
- Execution and recovery instructions.
- Outstanding decisions requiring owner approval.

Update:

- Data Architecture and Dictionary.
- Issue Register.
- `docs/development-journal/01-data-ingestion.md`.
- Task execution log.
- Relevant README or ingestion documentation.

Preserve earlier project documentation and factual journal records.

Archive this task prompt verbatim according to `AGENTS.md`.

## 8. Scope Boundaries

Do not:

- Change existing PIPR or Bank of England ingestion methodology.
- Join the new data to the rental forecasting panel.
- Calculate derived house-price growth features.
- Choose lags or rolling windows.
- Perform correlation analysis or feature selection.
- Decide whether CPI or CPIH should be removed.
- Train or evaluate forecasting models.
- Implement GCP deployment or CI/CD infrastructure.
- Introduce new geographic mappings without owner approval.
- Silently substitute unofficial datasets.

Where a material source-definition or methodological choice remains unresolved, report the evidence and obtain approval rather than making the decision independently.

## 9. GitHub Workflow

Start from the latest merged `main` branch.

Create a dedicated Task 008 development branch using existing naming conventions, unless an appropriate branch already exists.

Implement, test and document the approved task.

Commit and push the completed work for independent review.

**Do not create a Pull Request or merge into `main` without explicit project-owner approval.**

Do not begin Task 009.

## 10. Acceptance Criteria

Task 008 is complete when:

1. Official CPI and CPIH source retrieval works.
2. All four approved ONS time series are correctly identified and ingested.
3. Official all-property UK HPI retrieval works.
4. Average prices and index values are preserved with correct units and definitions.
5. Historical coverage and missing data are quantified.
6. Geographic compatibility with the approved 294 Local Authorities is measured and documented.
7. Available source revision and vintage evidence is preserved.
8. Raw source files and provenance are immutable.
9. Validated structured outputs are produced.
10. Relevant automated tests pass.
11. Independent official-source reconciliation evidence is recorded.
12. Existing ingestion functionality remains unaffected.
13. Documentation, issue register, development journal and execution log are updated.
14. Approved owner decisions and rationale are recorded factually.
15. Changes are committed and pushed to the designated branch.
16. No PR, merge or Task 009 work occurs.

If reliable ingestion cannot be completed for an approved dataset, clearly report the blocker, preserve investigation evidence and request the necessary decision. Do not claim full task completion where acceptance criteria remain unmet.

## 11. Final Report

Provide:

**Implementation**
- Official sources and retrieval methods.
- Historical coverage, observation counts and output schemas.
- Geographic coverage results.
- Revision and vintage preservation.

**Validation**
- Tests executed and results.
- Official-source reconciliation.
- Data-quality findings.
- Failure and recovery evidence.

**Project Governance**
- Development Journal updates and owner decision rationale.
- Issue Register changes.
- Outstanding decisions or blockers.
- Task archive location.
- Measured execution time in minutes.

**GitHub**
- Branch name.
- Commit SHA.
- Confirmation of successful push.
- Confirmation that `main` is unchanged.
- Confirmation that no PR or merge occurred.

Stop after Task 008 and report the results for independent review.

---

## Implementation report - 21 November 2026

### Scope, baseline and dependency outcome

Implemented on `feature/008-inflation-hpi-ingestion`, created from latest merged
remote main `48bae0947f294d59631cb160e73b5a7aeeefc62a` (Task 007 milestone
PR #4 was already merged when Task 008 began). Local main remains
`a28323e4c70b5afa551de619a19d87087ec329ae`. This task does not merge or update
main and does not create a PR. Earlier PIPR/Bank of England code and tests,
configuration, dependencies and approved cohort are unchanged.

**Proceed with documented limitations.** ISS-003: exact official codes match
all 294 cohort authorities; no historical mapping is applied. ISS-004:
release-specific observations and available publication metadata are preserved,
without claiming complete original availability. ISS-012: HPI coverage is now
measured for the inspected releases, not inferred for other predictors.
ISS-013: owner approved both all-property price and index; published base and
revision handling are verified below. Feature/vintage-selection decisions
remain future work. ISS-014: forecast-cutoff/timezone decisions do not block
source ingestion. These issues remain Open at their documented checkpoints;
no unresolved prerequisite requires a source substitution. No new issue is
needed for the preserved limitations. Task 008 is explicitly authorised by the
owner's archived instructions, independently of Task 007.

### Official contracts, access and reuse

Inflation uses the official series pages listed in the prompt and their
JSON representation at `{series_page}/data`, the same series payload used by
the ONS website. It validates `cdid`, `datasetId=MM23`, URI, title, unit,
index-base description, monthly records and the latest-value metadata.
Only the `months` array becomes monthly observations; annual and quarterly
values remain in the original response. Each response's advertised `versions`
inventory, correction notices, description and source-update strings are
preserved. The latest advertised previous URI is retrieved separately through
`{previous_version_uri}/data`; no version ID is guessed. Source JSON release
timestamp strings are retained exactly alongside date-only release fields.
The ONS metadata's midnight timestamp is not certified public release time.

Independent comparison uses the publisher's CSV generator linked from the
series pages: `/generator?format=csv&uri={series_path}`. All four current monthly
series reconcile, without recalculating annual inflation rates. CPI and CPIH
are distinct concepts and their rates/levels remain distinct measures.

HPI retrieves the [September 2026 download page](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-september-2026),
published **18 November 2026**, and its official release summary. Links to
`UK-HPI-full-file-2026-09.csv` and `Revisions-England-2026-09.csv` are discovered
on that retained page. Exact linked URLs, including publisher query parameters,
are recorded. The [August 2026 page](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-august-2026)
was separately retrieved to preserve the preceding release. CLI reference months
select official release pages, not an observation-date filter on a current file.

The full HPI file has 54 source columns; `Date`, `RegionName`, `AreaCode`,
`AveragePrice` and `Index` define the selected all-property contract. All columns
and all areas remain in validated source tables and original bytes. Standardised
observations keep the two selected measures for every source row. Other property
breakdowns are not promoted as model predictors.

The [September release summary](https://www.gov.uk/government/statistics/uk-house-price-index-for-september-2026/uk-house-price-index-summary-september-2026)
and [quality/methodology](https://www.gov.uk/government/publications/about-the-uk-house-price-index/quality-and-methodology)
confirm **January 2023 = 100**, following the February 2025 re-reference from
January 2015. The pipeline reads the release summary's base and checks available
base-month index values equal 100. Published average prices are standardised
nominal GBP values, not raw transaction means. The publisher's LA methodology
already includes smoothing; this pipeline applies no additional adjustment.
Later methods changes and release-specific revisions are preserved as source
values, not harmonised across vintages.

Access is unauthenticated through official ONS/GOV.UK/HM Land Registry HTTPS
hosts. [ONS reuse terms](https://www.ons.gov.uk/help/terms-conditions) and
[HPI reuse requirements](https://www.gov.uk/government/publications/about-the-uk-house-price-index/about-the-uk-house-price-index#7-republishing-data)
were checked on 21 November 2026: these statistical outputs are under OGL v3.0;
no selected-dataset exception was identified. ONS attribution is retained.
HPI attribution follows the publisher: contains HM Land Registry data, Crown
copyright and database right 2020, licensed under OGL v3.0. Rights to underlying
third-party property attributes are not inferred or acquired.

### Execution, storage and recovery

```powershell
uv run python -m ingestion.ons_inflation --snapshot-id 2026-11-21-task008
uv run python -m ingestion.uk_hpi --snapshot-id 2026-11-21-task008 --reference-month 2026-09
uv run python -m ingestion.uk_hpi --snapshot-id 2026-11-21-task008-hpi-2026-08 --reference-month 2026-08
uv run pytest -q
uv run python reports/data_audits/008/validate_live.py
```

Use new snapshot IDs for new retrievals; reuse identical arguments for offline
verification/reprocessing. Existing `configs/storage.toml` supplies the local
root. No cloud backend or infrastructure is added. The last command reproduces
the retained audit and downloads audit-only CSV comparisons if not already
present. Full source bytes and Parquet remain ignored by Git.

| Existing layer | Layout and contents |
| --- | --- |
| raw | `{dataset}/snapshot={id}/{source_id}/response.bin` and `manifest.json`; one immutable bundle per response |
| validated inflation | `ons_inflation/snapshot={id}/observations.parquet` plus manifest; monthly source values for every retained series/vintage |
| processed inflation | Same vintage-keyed table and manifest, without input-value selection |
| validated HPI | `uk_hpi/snapshot={id}/source_table.parquet`, `observations.parquet`, `revisions_england.parquet`, manifest |
| processed HPI | `observations`, `cohort`, `cohort_coverage`, `monthly_coverage`, `authority_coverage`, `geography_inventory`, `revisions_england` Parquet files and manifest |

`source_io.py` reuses the existing Bank of England module's immutable publication,
checksum and safe-metadata primitives. It adds an official-host retrieval boundary
and source-bundle orchestration; existing modules are not refactored. Source
metadata includes exact requests, allowlisted request/response headers, resolved
URL, status, UTC retrieval interval, checksum and snapshot identity. Derived
manifests contain source manifests, transformation version, validation reports,
units/base evidence and licence attribution. HPI additionally pins the geography
reference version and SHA-256. Every derived observation has snapshot, source
checksum, retrieval and release provenance. Original decimal strings are retained
beside float64 values; dates remain dates or explicit reference-month strings.

Downloads have a 60-second timeout, 128 MB bound, declared-length checks and up
to three attempts for transport failures/transient HTTP status. Permanent access
errors stop clearly. Unknown HTTP headers are excluded by default. Failed parses
retain the raw response but publish no new validated/processed bundle. Existing
source requests with matching identities/hashes are reused; changed request
identities or damaged bundles fail rather than overwrite. Layer bundles stage
beside their destinations and rename atomically, with recovery from a completed
raw/validated layer. An existing completed source remains intact on any failure.
Abandoned `.staging-*` folders are ignored and can be inspected before manual
cleanup. No mutable latest pointer or first-release override is created.

### Output schemas and gates

- Inflation key: `(series_id, source_version_id, observation_month)` within a
  snapshot. Fields include concept, measure, unit, index base year, float value,
  exact source value/reference strings, source release date/raw timestamp,
  source update string, original observation attributes and common provenance.
  `current` denotes the captured current response in this snapshot, not a global
  mutable series. Prior responses use their advertised `v...` identifiers.
- HPI observations key: `(area_code, observation_month)` within a snapshot.
  Fields include source name/reference date, float average price/index, exact
  source strings, index base month, cohort-membership flag, approved cohort name,
  source-name difference flag and common provenance. `cohort` contains only
  observed rows with exact eligible codes; source names remain unchanged.
- `cohort_coverage` is an explicitly labelled authority/month grid with source
  row/price/index/both-present booleans. Missing rows are coverage facts, never
  fabricated observations. `monthly_coverage` counts expected/matched/complete
  authorities; `authority_coverage` counts expected/observed/complete months.
  `geography_inventory` retains each source code/name and first/last month/counts,
  including source areas outside the cohort. Names are not used to remap codes.
- England revision audit key: `(measure, observation_month,
  source_publication_label)`. It preserves the publisher's matrix sections,
  exact value strings, numeric or missing values and publication-month labels.
  The file contains average price, annual growth and transaction counts; these
  ancillary revision fields remain audit evidence, not new feature calculations.
  These are England aggregates, not LA vintage records. First-of-month labels
  are explicitly not certified exact release dates. Historical price bases may
  differ between publication rows; no comparable-basis adjustment is inferred.

Hard gates reject wrong identities/units/descriptions, invalid dates/numbers,
duplicate/conflicting observations, malformed/incomplete rows, inconsistent
latest-month/source metadata, unknown revision structure and base conflicts.
Inflation rates may be negative; positive index/price semantics do not impose
statistical-usefulness thresholds. Source blanks remain missing values, with
coverage reports rather than imputation. Genuine calendar gaps are quantified;
none are silently dropped or filled. The HPI source endpoint must reach the
requested reference month. Cohort gaps/name differences are reported without
rejecting the source on an arbitrary coverage threshold.

### Measured historical coverage and revisions

| Series / release | Monthly range | Observations |
| --- | --- | ---: |
| D7G7 CPI annual rate, current | January 1989-October 2026 | 454 |
| D7BT CPI index, current | January 1988-October 2026 | 466 |
| L55O CPIH annual rate, current | January 1989-October 2026 | 454 |
| L522 CPIH index, current | January 1988-October 2026 | 466 |
| All current inflation series | Per-series ranges above | 1,840 |
| Prior inflation versions v132/v133/v133/v134 respectively | Same starts, through September 2026 | 1,836 |
| September HPI, all source geographies | April 1968-September 2026, area-specific starts | 152,730 rows, 405 areas |
| September HPI, approved cohort | January 1995-September 2026, 381 months | 112,014 rows, 294 authorities |
| August HPI, all source geographies | April 1968-August 2026 | 152,325 rows, 405 areas |
| August HPI, approved cohort | January 1995-August 2026, 380 months | 111,720 rows, 294 authorities |

All retained inflation series have zero calendar gaps/missing numeric values.
Current/prior overlapping values agree; that is a measured comparison of these
two vintages, not proof that inflation series never change. November 2026 ONS
releases and October 2026 prior releases are kept independently. Index levels
retain their source's 2015 base; annual inflation rates remain percent.

Both HPI cohort snapshots have **294/294 exact-code matches**, zero missing
authority/month rows and zero missing selected values. Eleven code-matched
source names differ from the pinned names (including punctuation, prefixes
and one trailing space); both spellings are retained and flagged. All unmatched
source areas are retained in the full source and geography inventory. No source
code is combined or rewritten. The source-area/name series have no internal
calendar gaps in this inspected file, and no code has multiple source names.
These are retrospective source-table findings, not evidence that the 2025
cohort or historical administrative boundaries existed throughout the range.

Across the 111,720 overlapping cohort rows, **3,523 price records** and **2,843
index records** differ between the August and September vintages. Both versions
remain available; no release is selected as the canonical historical input.
September's England matrix retains 22,599 cells, 12,716 nonmissing; August's
matrix retains 22,080 cells, 12,440 nonmissing. These tables corroborate aggregate
revision availability, not complete LA publication histories.

The source's pre-1995 history is derived national/regional back-series. It does
not extend measured LA coverage before January 1995. The 2025 re-reference and
publisher methodological changes can affect historical levels. Retaining current
and one prior release does not establish a complete historical archive. ONS
advertises additional historical versions; their metadata/correction notices
are retained, but this task does not mass-download or certify every archive.
HPI's routine revisions and occasional changes beyond the routine window are
publisher behavior; snapshots preserve them rather than assuming a hard finality
date. Exact release-time availability and forecast eligibility remain future
owner-governed decisions under ISS-004/ISS-014.

### Validation and limitations

`uv run pytest -q`: **117 passed in 27.27 seconds** (76 existing tests and 41
new inflation/HPI/I/O tests). Tests cover normal/negative-rate/missing-value
inputs, identities/units/bases, duplicates, malformed JSON/CSV, incomplete
downloads, changed source contracts, unofficial redirects, access/retry errors,
raw/output corruption, immutable conflicts, interrupted publication and offline
recovery for both pipelines. Existing PIPR and Bank of England tests pass;
their implementation and methodology are unchanged.

[Live validation evidence](../reports/data_audits/008/validation-evidence.json)
and [replay script](../reports/data_audits/008/validate_live.py) record independent
comparisons: all **1,840** current inflation observations matched official ONS
CSV downloads; all **152,730** HPI source rows matched each separate official
average-price and index export. Attribute exports use ISO dates/underscore
headings, handled explicitly in the audit rather than changing production
data. Selected first/latest inflation values and six LA price/index examples
are retained for review. All **60** existing raw/validated/processed snapshot
files were unchanged on offline reruns. Comparison CSVs are separate ignored
raw audit bundles under `data/raw/task008_audit/`.

Initial sandbox network access was refused; approved retrieval succeeded.
GOV.UK's release page supplied a visible publication date rather than the
initially expected structured date element; parsing now validates that label.
The first audit run had a corrected syntax error and then exposed the separate
attribute-export schema differences; the final audit passed. These are recorded
implementation/validation interventions, not source absence or waived gates.

No exact historical PIT reconstruction, historical geography mapping or source
statistical usefulness is claimed. No predictors are joined to rents; no lags,
growth calculations, correlations, feature selection, model work or deployment
is included. Owner decisions and reasons are recorded separately in the journal.
Final prompt/CSV/link/security/scope checks, Git publication and measured timing
are recorded at handoff below.

### Final repository checks and independent-review handoff

The task archive's original byte prefix matches the attachment verbatim.
All six added Python files parse; the live evidence JSON parses and contains
only allowlisted HTTP header metadata. Prior execution CSV rows and journal
text are preserved, with one new seven-column CSV row for text ID `008`.
Only ISS-003/004/012/013 rows changed, all remain Open; ISS-014 and ISS-020 are
unchanged. No new issue or unresolved ingestion approval is introduced.
One hundred twenty-five local Markdown file links resolve; `git diff --check`
passes. Existing PIPR/Bank of England modules/tests, configuration, pinned
geography, dependencies, lockfile and AGENTS.md are unchanged. New application
tests are limited to the authorised two source contracts and shared I/O boundary.

Thirteen files comprise the change: README, this archive/report, dictionary,
issue register, ingestion journal, shared timing CSV, three production modules,
one test module and three lightweight source-probe/audit/evidence files under
`reports/data_audits/008/`. Source responses, comparison downloads, source-shaped
tables and generated coverage reports remain ignored under the configured data
root. The committed replay script and small JSON provide reviewable validation
evidence; original dataset binaries are not committed. Additional initial
inspection bodies remain in ignored `data/raw/008-inspection/` and are not
required to run the production pipelines or inspect committed reconciliation.

No geography codes were added/removed between the two inspected HPI vintages.
This does not establish historic boundary equivalence for future joins.
Application tests and the final audit passed with the limitations above.
Git publication and measured timing follow after the implementation push.
