# 010. ONS Population, Area and Migration Production Ingestion

## Objective

Implement a reproducible, production-ready ingestion pipeline for the approved ONS Local Authority population, land area and migration datasets.

Preserve the original published data, geography, historical editions, source metadata and revisions.

The task covers data acquisition, source investigation where necessary, validation and production ingestion.

It does not include preprocessing, feature engineering, geography harmonisation or modelling.

## 1. Project Baseline

Start from the latest `main` following the successful merge of PR #9.

Before implementation:

- Read `AGENTS.md` and `docs/ENGINEERING_STANDARDS.md`.
- Review the existing Data Architecture and Dictionary.
- Review relevant source research, existing ingestion implementations and tests.
- Review the Issue Register and applicable dependencies.
- Confirm the repository is private and use the clean development checkout.

Reuse existing ingestion architecture, storage conventions, immutable snapshots, validation and recovery mechanisms.

Do not introduce unnecessary dependencies or infrastructure.

Archive this task prompt and maintain the existing task execution log in accordance with repository standards.

## 2. Data Sources

Use official ONS population estimates for England and Wales.

The existing source investigation identifies:

| Dataset | Required source information |
|---|---|
| MYE4 | Annual mid-year population estimates |
| MYE5 | Land area and published population-density information |
| MYE3 | Internal and international migration components |

Source investigation already confirmed:

- MYE4 population estimates for mid-2011 to mid-2025.
- MYE5 area and population-density information for the same inspected period.
- MYE3 migration components for the year to mid-2025.
- 292 direct-code matches against the approved 294-LA cohort in the inspected datasets.
- Unresolved Barnsley and Sheffield code differences.

These are verified research findings, not universal expectations for every historical edition.

Consult the original ONS files and existing repository evidence before finalising the detailed source contract.

## 3. Source Scope and Historical Coverage

### Population

Ingest the available official annual mid-year population observations relevant to the project's historical forecasting period.

Preserve:

- Population reference year.
- Original Local Authority code and name.
- Original geographic definition and source edition.
- Published population values.
- Available revision and publication metadata.

Retain relevant historical source observations outside the exact target-code cohort when needed to document original geography and coverage.

Do not combine incompatible population vintages without documenting their provenance.

### Land Area

Ingest the published land area information associated with MYE5.

Preserve the publisher's units, geographic definitions and reference years.

Retain any published density values as original source information where appropriate.

Do not independently calculate population density during ingestion.

### Migration

Ingest the verified MYE3 internal and international migration components.

Preserve published inflow, outflow and net measures and their reporting periods.

First establish which historical component editions are available, accessible and sufficiently defined.

Older editions should be investigated and ingested where their original source definitions and provenance can be verified without introducing a new methodological decision.

Do not assume that the mid-2025 extract establishes a continuous historical migration series.

If an important historical source or definition cannot be verified, preserve the valid completed work, document the gap and request owner approval where a material decision is necessary.

## 4. Original Geography Preservation

Maintain the project's approved approach:

**Preserve source geography during ingestion; harmonise geography during preprocessing.**

Requirements:

- Retain original source codes, names and geographic vintages.
- Preserve relevant historical geographic changes.
- Compare source codes against the approved 294-LA reference.
- Report exact matches, unmatched codes and name/code discrepancies.
- Explicitly investigate the previously identified Barnsley and Sheffield discrepancies.
- Do not infer missing data solely from a code mismatch.

Do not implement boundary mappings, geographic aggregation or retrospective geography reconstruction.

Document unresolved findings under ISS-003.

## 5. Data Integrity and Provenance

For each source and edition:

- Preserve immutable official raw files.
- Record source URLs, retrieval dates, source identity and checksums.
- Retain publication and revision evidence where available.
- Distinguish observation year, publication date and retrieval date.
- Preserve original workbook content and relevant notes.
- Retain source missingness, suppression indicators and explanatory annotations.
- Detect duplicate records and unexpected schema changes.
- Validate source units and geographic coverage.
- Support safe retries and reproducible offline re-execution.

Confirm applicable access and licensing requirements.

Do not overwrite previously validated data.

Do not make unsupported point-in-time availability claims.

## 6. Validation

Provide reproducible, source-level validation for each dataset.

### Population and Area

- Reconcile ingested values with official MYE4/MYE5 source records.
- Verify reference years, units and original source identifiers.
- Measure historical and Local Authority coverage.
- Compare the inspected historical period with existing repository findings.
- Explain genuine differences between source editions.

### Migration

- Reconcile internal and international migration components.
- Verify year-ending definitions.
- Measure coverage for each available historical edition.
- Document missing periods and geographic differences.
- Identify revisions and definition changes without silently combining incompatible values.

### General

Validate:

- Source identities.
- Data schemas.
- Duplicate keys.
- Missing and non-numeric source values.
- Immutable snapshots.
- Interrupted acquisition and recovery.
- Reproducibility.
- Preservation of previously validated outputs.

Treat observed historical coverage as evidence, not an arbitrary pass/fail threshold.

Do not reject datasets solely because of missing values or geographic differences.

## 7. Automated Tests

Implement appropriate focused tests for each ingestion component, including normal, boundary and failure cases.

Run focused tests during implementation.

Run the complete regression suite and relevant source audits when the implementation is ready for final validation.

**Do not repeatedly execute expensive tests solely for documentation updates or PR creation.**

Reuse validation evidence when the validated code, source data and configuration remain unchanged.

Independent audit evidence should compare equivalent source observations and validate request-specific metadata separately, applying the lesson from ISS-021.

## 8. Scope Restrictions

Do not:

- Calculate population growth or population-density features.
- Calculate new migration ratios or derived indicators.
- Harmonise Local Authority codes or boundaries.
- Impute missing values.
- Join population or migration data to rental targets.
- Analyse statistical correlations or predictive usefulness.
- Select modelling vintages or availability lags.
- Train models.
- Extend the task to unrelated household or student datasets.
- Change repository visibility or rewrite Git history.

Significant changes to methodology or architecture require project-owner approval.

## 9. Issues and Documentation

Review relevant existing issues, particularly:

- ISS-003 — Geography and boundaries.
- ISS-004 — Historical availability and revisions.
- ISS-011 — Source quality and preservation.
- ISS-012 — Historical coverage and completeness.
- ISS-020 — Outstanding security exposure.

Update the Data Architecture and Dictionary with verified findings.

Record significant development events in the existing ingestion journal.

Update the Issue Register only where supported by evidence.

Keep ISS-020 Open. Do not interpret successful ingestion as resolution of point-in-time or geography limitations.

Maintain the existing execution log and prompt archive without adding new administrative files or tracking systems.

## 10. Efficient Development and PR Workflow

Use three stages.

**Stage A — Implementation and validation**

Implement the ingestion pipeline, investigate relevant historical coverage, run necessary tests and complete independent source reconciliation.

**Stage B — Documentation and PR preparation**

After successful validation:

- Complete required documentation and evidence.
- Check the final diff for unintended or sensitive changes.
- Confirm that committed code and data contracts match the validated state.
- Commit and push the feature branch.
- Open one PR against `main`.

Do not repeat the full test suite unless relevant implementation, data or configuration changes invalidate prior results.

**Stage C — Independent review**

Stop for owner review.

Do not merge automatically.

If a correction is documentation-only, validate the changed documentation without unnecessarily rerunning data ingestion.

Record measured execution time and timing limitations using the existing CSV. Where reliably available, distinguish development, testing, documentation and PR preparation time.

## 11. Acceptance Criteria

Task 010 is ready for independent review when:

1. MYE4 population and MYE5 area data are ingested and validated for the approved accessible scope.
2. MYE3 migration data are ingested for verified editions, with historical gaps and unverified definitions explicitly identified.
3. Original source files, geography, periods, annotations and revisions are preserved.
4. Source reconciliation and relevant automated tests pass.
5. Missingness and geography discrepancies are reported without unauthorised harmonisation.
6. Immutable storage, offline recovery and existing-data preservation are validated.
7. Access, licensing and security checks are complete.
8. Documentation and issue statuses reflect actual findings.
9. One PR is prepared for independent review without automatic merging.

If any critical validation fails, preserve the evidence and stop the affected work rather than forcing a PASS.

## 12. Final Report

Provide a concise report covering:

- Data sources and editions ingested.
- Historical coverage by dataset.
- Number of source observations and geographic areas.
- Exact target-code matches and discrepancies.
- Missingness, revisions and definition limitations.
- Source reconciliation results.
- Automated test results.
- Data preservation and recovery results.
- Licensing and security findings.
- Issue Register changes.
- Outstanding owner decisions.
- Branch, commit and PR information.
- Actual measured task execution time and limitations.

Classify the task as **PASS**, **PASS WITH CONDITIONS**, **BLOCKED** or **FAIL**, supported by reproducible evidence.

Do not claim that the resulting data is already model-ready.

## Owner offline-development instruction - 22 November 2026 (verbatim)

Please continue Task 010 using Option C — offline development.
1. Use existing verified ONS source files for investigation, implementation and testing.
2. Do not make further automated ONS downloads until an appropriate project contact URL or organisation email has been approved.
3. Preserve source provenance, original data and existing validation evidence.
4. Clearly document which datasets and historical periods can be validated offline and which still require downloads.
5. Continue unaffected development work without introducing substitute datasets or changing the approved methodology.
6. If additional downloads are essential for completion, report the dependency and stop only the affected work.
Do not invent User-Agent contact information or bypass ONS access requirements.
Keep the repository private and ISS-020 Open.


## Implementation report - 22 November 2026

**PASS WITH CONDITIONS for the owner-approved offline scope.** The nine retained
workbooks are ingested and independently validated. Five advertised older versions
remain unacquired; future automated acquisition is blocked until the owner approves
an appropriate project contact. This is not a claim of exhaustive vintage coverage
or model readiness. The owner explicitly authorised offline continuation above;
no further automated ONS request was made after that instruction.

### Baseline, scope and implementation

GitHub confirmed PR #9 merged as a269f7226a89adf5d968217ca26600abd18dba84 and the
repository private. Clean main was fast-forwarded to that commit before creating
`feature/010-ons-population-ingestion`. The original pre-remediation checkout was
untouched. The attached original prompt is preserved byte-for-byte above; no new
administrative tracking system or dependency was added.

`src/ingestion/ons_population.py` and the pinned
`configs/ons_population_sources.json` reuse the existing storage configuration,
raw-source registration, checksum verification, safe HTTP metadata and atomic
publication boundaries. Production CLI and the investigation replay are offline
only. Missing responses stop clearly; an injected offline downloader is also used
by the independent rerun. The low-level ONS transport has bounded retries,
Retry-After handling, original TLS verification and a required approved non-personal
contact URL; its behaviour is tested with synthetic responses, without contacting
ONS during offline development. No placeholder or personal contact is supplied by
the current implementation.

The source contract contains five MYE3/4/5 summaries (2025, 2024, 2023, 2022 on
2023 geography and 2022 on 2021 geography), plus four detailed MYEB3 workbooks
(2011-to-2025/2024/2023/2022). Detailed 2022 retains both its native 2021 and 2023
geography sheets, separately. Earlier detailed files verify historical component
coverage; no unverified 2025-only continuity assumption or APS/other substitution
was used. National/regional-only series and the pre-2011 archive were identified
but are outside this forecasting-history LA contract. The latest history covers
all of the project's 2015-onward period without extending into feature creation.

Six identically published validated/processed tables are retained under
`ons_population/snapshot=2026-11-22-task010/`:

- `observations`: original edition/sheet/row/column/cell, code/name/level/vintage,
  measure/year/period/unit, parsed numeric value plus exact XML literal, original
  value JSON, formula/cache, marker kind, style array/ID/number format, source
  header, flags, exact-cohort indicator and request/checksum/retrieval provenance.
- `coverage`: source areas, exact target-code matches, numeric/marker counts and
  unmatched/missing identifiers per edition, sheet, measure and reference year.
- `geography_audit`: original source areas and name/code discrepancies, unmatched
  targets, and an explicit `mapping_applied=False`.
- `notes`: original cover, contents, notes, geography guide, related-publication
  and table-footer text with source cell/style identity.
- `schema`: verified titles/headers, geography labels, per-sheet area counts and
  original publication/geography evidence strings. No source timestamp is recast
  as a verified UTC availability time.
- `documents`: original retained catalogue, version-history, bulletin, terms and
  fair-use HTML with URLs/checksums/retrieval times. Raw XLSX files preserve all
  original worksheets, workbook styles, annotations and other content outside
  selected structured fields.

The inventory pins each inspected workbook hash and exact table identity/headers.
Schema, checksum, duplicate-key or period failures prevent publication; source
missingness and geography differences are retained rather than rejected. Original
numeric literals remain available even when a parsed float cannot express their
full precision. Source net fields and published density values are read directly.
Area is a single source cell without a separate year per area/edition with square-kilometre units;
no invented year or repeated annual area observations are introduced. Population
is a mid-year stock; flows are twelve months to mid-year (1 July to 30 June), with
source definitions/labels retained. No density, growth, net flow or ratio is
calculated by ingestion.

### Measured coverage, quality and revisions

[The source audit](../reports/data_audits/010/README.md) lists every retained edition
and period. Population and published density cover 2011-2025 in the latest summary;
detailed migration covers years ending mid-2012 through mid-2025. Historical
editions remain separate, with their own end years and geographic families.

There are **198505** selected source observations across **20** sheets: population
44898; density 23754; area 1801; and 21342 observations for each of internal and
international inflow, outflow and net. These include source aggregates and repeated
vintages; they are not a harmonised model panel. The latest summary contains 357
source areas, including national/regional/county aggregates, and latest detail
318 LAs. The 2021-geography summary/detail contain 373/331 areas respectively.
2023 geography has **292** exact approved-code matches; 2021 geography has **288**.
All matched selected source values are numeric in their respective periods.

**198429** cells are numeric. **76** are literal `No data` markers in summary2023
internal inflow/outflow for aggregate areas (38 each), preserved without coercion
to zero. Notes retain uncertainty/disclosure, rebasing and revision limitations;
styles/formatting are retained, with no arbitrary confidence/outlier/missingness
threshold. Raw workbooks preserve unstructured source uncertainty material; this
task does not construct new uncertainty fields or infer precision from rounding.

Barnsley and Sheffield were explicitly investigated in both raw workbooks and the
pinned reference: source E08000016/E08000019 at latest MYE4 rows 72/75 versus
reference E08000038/E08000039. Each has all 37 selected numeric latest-summary
cells, with matching published names and metropolitan-district source type. These
are present observations with code discrepancies, not absent source data. The
retained notes contain no specific explanation of these code changes; none is
invented. Older North Yorkshire/Somerset county names also match newer unitary
names without establishing boundary equivalence. All levels/codes are preserved;
no mapping or aggregation is implemented. Some 2025 notes refer to April 2024/2024
authorities while edition/detailed table labels identify 2023 geography; both
statements are retained and records carry a geography-note review flag.

Matching code, native geography, measure and reference year across detailed
vintages shows 0 changed cells among 24804 shared 2022-to-2023 observations,
4440 numeric changes for 2023-to-2024, and 3810 for 2024-to-2025. Detailed results
by year/measure are in [source-findings.json](../reports/data_audits/010/source-findings.json).
These audit counts describe published revisions, not derived predictors.
Source notes retain Census 2021 rebasing and updated international migration;
2025 revisions affect earlier years. No model-input vintage, fixed release lag
or complete historical first-publication timeline is selected or claimed.

### Independent reconciliation and automated checks

**38 focused tests passed in 3.47 seconds**; the complete suite passed
**266 tests in 66.56 seconds**. Cases cover native summary/detail sources, original
geography, exact XML precision, missing/marked/error/formula cells, notes/styles,
units/period/header validation, duplicates, interrupted acquisition/publication,
immutable recovery, corrupted outputs, no-network operation, contact gating,
unsafe headers and bounded retry/terminal HTTP behaviour. Synthetic failures
identified read-only style access and a workbook/HTTP-header metadata-key collision;
both were corrected before production publication. The first production attempt
stopped before outputs on a capitalisation-only `International migration Net`
variant in historical 2021-geography MYE3; read-only diagnosis verified the same
approved source field, and a regression test covers the correction. Source bytes
and labels were unchanged. No critical source discrepancy was found or forced to
pass.

The independent audit uses standard-library XLSX ZIP/XML relationships/shared
strings, without reusing the production workbook parser or column mapper. It
reconciles **all 198505 selected source cells**, including value/marker, style ID,
original identifier/label, measure/year/unit and provenance. Observation identity
includes edition/sheet/cell; request identity/checksums are validated separately.
It verifies **599** coverage rows and reproduces Task 006.2's 292 latest-summary
exact/numeric result. **24804 equivalent same-vintage** summary/detail population
and migration observations match exactly across four release families; cross-vintage
revision differences are reported, not treated as equality failures.

All six validated/processed tables agree. Offline rerun with a downloader that
raises on acquisition preserves **all 388 data files**, including **342** pre-task
files and the **16** retained raw request bundles. Raw bytes, existing datasets,
source retrieval provenance and prior evidence were not altered to satisfy tests.
Completed downloads were verified/reused. No previous source implementation,
dependency, storage configuration or approved cohort/horizon was changed.

Gitleaks 8.30.1 (existing official checksum-verified tool) found no secrets in
Git-eligible project files or cleaned local history (39 commits at validation).
Ignored raw bundles were independently checked for checksums and safe HTTP header
retention; no cookies/authentication headers are retained in source manifests.
`uv lock --check`, cached Black 25.1.0 checks, whitespace checks and
`git fsck --strict` passed (only informational dangling objects). Final staged diff
and documentation checks follow without another full suite/source ingestion.
These checks do not certify erasure from old remote PRs/caches/external copies;
ISS-020 remains Open and private visibility is preserved.

### Access, pending files and issue dependencies

Official ONS catalogue/terms identify Crown copyright and OGL reuse with attribution
and exceptions. Retained terms/fair-use documents were reviewed; no paid/restricted
account, session replay or alternate source was used. The initial obsolete licence
path returned terminal 404; the verified official terms URL was retained instead.
An initial request-encoding identity conflict stopped safely, then canonical
encoding reused the already-saved exact request URL rather than overwriting raw
files. These are resolved acquisition bookkeeping events, not a licence bypass.

The bot-contact review revealed the concrete prerequisite in
[ONS technical guidance](https://developer.ons.gov.uk/bots/), alongside
[the retained fair-use policy](https://www.ons.gov.uk/help/fair-use-policy).
Earlier completed requests retain their original headers/provenance; after the
contact requirement was reviewed the acquisition worker was stopped. The owner
explicitly chose offline development and forbade further automated ONS downloads
without an approved project contact URL or organisation email. Current code
invents no contact and defaults to offline operation.

Five exact URLs remain unacquired, recorded in `source-investigation.json`:
previous v1/v2 for each 2022 summary geography, plus detailed 2022 previous v1.
Version-history pages preserve scheduled revision/supersession dates and the 2023
correction notice concerning within-area moves in country/region/county inflows/
outflows. These files must not be treated as present or verified, or substituted
with newer values. Contact approval is required before their acquisition. They
limit historical vintage/correction coverage; they do not create a missing year
in the latest verified migration series. The original pre-2011 and national-only
archives are identified outside the current forecasting-history LA contract.

Dependency outcome: **Proceed with documented limitations** for the approved
offline scope. ISS-003/004/011/012 remain Open with updated geographic, publication,
quality and coverage evidence. New **ISS-022** is Open for the actual contact
prerequisite before the affected further acquisition; this does not block offline
work. **ISS-020 remains Open** and is not resolved by ingestion/security scans.
No other issue is closed; no methodology/architecture decision, substitution or
owner approval is needed for the verified offline inputs. Further acquisition
requires the stated contact approval. The Household Growth and Student Population
Share exclusions are unchanged. One review PR will contain this offline scope,
with the pending files and conditions explicit; no automatic merge is authorised.

### Stage timing checkpoint

Stage A (source investigation/implementation, tests, offline production/audit and
security): **2026-11-22T09:35:31+00:00 to 2026-11-22T09:58:00+00:00**, **1349 seconds /
60 = 22.483333 minutes**, measured by whole-second UTC clock-tool readings.
Stage B documentation/PR preparation starts at that same cutoff. The 66.56-second
full-suite interval overlaps the ongoing source audit and is not added again.
Earlier focused tests and owner-input/tool/network/access-review waits are included
within Stage A, not separately timed or silently subtracted. Stage C independent
review has not begun. Final total/cutoff and actual PR handoff will be appended.


## Independent-review handoff and final timing - 22 November 2026

**PASS WITH CONDITIONS; Completed for the owner-approved offline scope.**
Implementation commit **824c36c9a00a43b684d5d6b19bede98b4da1930d** is pushed on
`feature/010-ons-population-ingestion`. [PR #10](https://github.com/chanmlh026/rental-forecasting/pull/10)
targets unchanged cleaned main **a269f7226a89adf5d968217ca26600abd18dba84**. GitHub
confirms OPEN, unmerged and mergeable, private visibility and auto-merge disabled.
There are 17 authorised files, no committed datasets or unrelated ingestion/
dependency changes. Local test/audit evidence is final for the unchanged code and
contract; no full-suite/ingestion reruns were performed solely for documentation
or PR preparation. The status API reports no commit statuses and no CI workflow
is configured; local validation is not represented as a CI result.

The five previous-version downloads remain unacquired, blocked pending compliant
contact approval under ISS-022. That outstanding acquisition is not counted as
completed work. The approved offline component, documentation and one review PR
are complete. Broader geography/PIT/quality dependencies and ISS-020 remain Open;
no source discrepancy or current material methodology decision was identified.
Stage C is independent owner review; no merge or visibility change occurred.

| Measured stage (UTC) | Recorded interval | Minutes |
|---|---|---:|
| A: investigation/implementation/tests/offline audit/security | 2026-11-22T09:35:31+00:00 to 2026-11-22T09:58:00+00:00 | 22.483333 |
| B: documentation and PR preparation | 2026-11-22T09:58:00+00:00 to 2026-11-22T10:05:48+00:00 | 7.800000 |
| Total measured session | 1817 seconds divided by 60 | 30.283333 |

Whole-second UTC clock-tool precision. The full suite's pytest-reported 66.56
seconds overlap the source audit and are not added again. Earlier focused tests,
owner-input waits and tool/network/access-review waits are included within the
continuous session and were not measured separately or subtracted. No active-CPU
time is inferred. Cutoff follows implementation push, PR creation and metadata/
privacy checks. This final receipt/timing write, documentation-only commit/push,
remote read-back and response are outside the cutoff. Independent review has not
been timed. The single Task 010 CSV row retains this start/end/duration and status.
