# 007. Ingest Bank of England Bank Rate and Buy-to-Let Mortgage Rate (IUMZID4)

## Objective

Implement a reliable, reproducible, production-ready data ingestion pipeline for two Bank of England financing datasets:

1. **Bank Rate** — the official UK monetary policy interest rate.
2. **IUMZID4** — the monthly quoted two-year fixed buy-to-let (BTL) mortgage rate at 75% loan-to-value (LTV).

This task covers source retrieval, preservation, validation and structured data outputs.

It must follow the project's approved data architecture, engineering standards and human-directed, AI-implemented development approach.

Do not implement feature engineering, statistical analysis, model training or forecasting.

## 1. Review Existing Project Context

Before implementation, review:

- `AGENTS.md`
- `docs/ENGINEERING_STANDARDS.md`
- `docs/data-architecture-and-dictionary.md`
- `docs/issue-register.md`
- `docs/development-journal/01-data-ingestion.md`
- `docs/006-ons-pipr-ingestion.md`
- `docs/007.1-iumzid4-historical-revisions-and-publication-vintages.md`
- Relevant existing ingestion code, tests, configuration and storage conventions.

Treat the current `feature/007-boe-ingestion` branch as the source for Task 007.1 findings.

Follow existing repository conventions wherever applicable. Do not duplicate existing infrastructure unnecessarily.

Review ISS-004, ISS-005 and other relevant dependencies before implementation.

## 2. Approved Methodological Decisions

The following decisions have been explicitly approved by the human project owner.

### 2.1 IUMZID4 — First-Release Value Policy

For every IUMZID4 observation month:

- Use the earliest retrievable published rate as the selected historical observation.
- Include provisional values where they are the earliest recorded published values.
- Do not replace the selected value with subsequent revisions.
- Preserve the complete available revision history separately for auditing and reproducibility.
- Retain the observation month and relevant source update/publication information.
- Do not treat the observation month as the publication date.

The objective is to represent the initial information available to the forecasting system rather than retrospectively revised rates.

An earliest retained database event is not automatically proof of first public availability.

Where original-publication completeness cannot be established, retain the earliest recorded value with an explicit evidence-status indicator. Do not silently claim it is a verified first-release value.

Do not substitute a later revised value without disclosure and project-owner approval.

### 2.2 IUMZID4 — February 2019 Methodology Change

The project owner has approved retaining IUMZID4 across the documented February 2019 methodological transition.

Requirements:

- Preserve the published historical rates without adjustment.
- Do not splice, rescale or harmonise historical values.
- Document the relevant methodological changes and transition date.
- Preserve the July 2018 population-expansion note identified in Task 007.1.
- Retain relevant source notes and metadata.
- Do not introduce a statistical correction based on the Bank's illustrative −0.17 percentage-point estimate.

The statistical implications of the methodology change are outside this ingestion task.

### 2.3 Historical Availability

Retain the distinction between:

- Observation month or effective date.
- Initial recorded publication/update event.
- Subsequent revisions.
- Retrieval timestamp.
- Source snapshot or vintage.

Preserve source timestamps exactly where their timezone has not been verified.

Do not invent timezone offsets or publication timestamps.

The selected first-release values must retain their associated availability evidence so that future feature engineering can prevent look-ahead leakage.

IUMZID4 observations backfilled before the series' October 2016 introduction must not be represented as publicly available at their original observation dates.

### 2.4 Bank Rate

Ingest the official effective-date history without modifying the published interest rates.

Bank Rate is a policy rate, not a calculated quoted-mortgage-rate statistic.

Preserve the original rate-change dates and values.

Do not convert Bank Rate into monthly averages, month-end values or forecast-cutoff values during this task.

These transformations require separate feature-engineering decisions.

## 3. Official Data Sources

### IUMZID4

Use the official Bank of England Interactive Statistical Database XML interface, including its documented historical revision functionality.

The retrieval approach and tested request parameters are documented in Task 007.1.

Relevant source:

https://www.bankofengland.co.uk/boeapps/database/index.asp?EC=IUMZID4&From=Template&G0Xtop.x=1&G0Xtop.y=1&Travel=NIxSUx

Use the XML revision-history functionality demonstrated in Task 007.1.

Do not require a separate permanent CSV ingestion process if the XML provides the necessary current observations and historical records.

A CSV comparison may be used for independent validation.

### Bank Rate

Use the official Bank of England Bank Rate history:

https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp

Identify and verify a reliable official retrieval method.

Preserve the source's original effective-date information and source metadata.

Check official access and reuse terms for both datasets.

Do not use third-party substitute datasets without approval.

## 4. IUMZID4 Ingestion Requirements

Implement repeatable ingestion of the historical monthly IUMZID4 series.

The pipeline must:

1. Retrieve the source XML with available revision information.
2. Preserve the original response bytes and retrieval metadata.
3. Parse the current observations and associated historical revisions.
4. Preserve provisional and final observation statuses where available.
5. Identify the earliest recorded value for each observation month.
6. Retain all available later versions for auditing.
7. Produce structured validated and processed outputs.
8. Preserve the distinction between selected first-release values and revision-history records.
9. Record uncertainty where the earliest recorded value cannot be certified as the original publication.

Verify that the selected XML retrieval method covers the intended historical series.

The previously inspected range was January 2012 to October 2026. Treat this as an investigation reference, not a permanent restriction on future releases.

If a full-history XML request exceeds source limits, implement reliable bounded retrieval without changing the selected methodology.

Avoid unnecessary duplicate downloads or processing.

Do not invent missing historical revision records.

## 5. Bank Rate Ingestion Requirements

Implement repeatable ingestion of official Bank Rate changes.

The pipeline must:

1. Retrieve the official historical rate-change data.
2. Preserve original source responses and metadata.
3. Extract the effective date and corresponding policy rate.
4. Validate date ordering, numeric values and duplicate or conflicting records.
5. Preserve the original event-level granularity.
6. Produce a structured output suitable for future monthly feature construction.
7. Support future source updates and repeatable execution.

Do not interpret an effective date as a precise public announcement timestamp unless verified.

Do not generate monthly Bank Rate features during ingestion.

## 6. Storage, Provenance and Reproducibility

Follow the existing project storage architecture and configuration, particularly `configs/storage.toml`.

Use the established raw, validated and processed data layers as appropriate.

Preserve:

- Original source responses.
- Exact source URLs and request parameters.
- Retrieval timestamps in UTC.
- Source response metadata and relevant headers.
- Checksums.
- Source identifiers.
- Observation dates and rate values.
- Historical revision events and statuses.
- Source update timestamps.
- Relevant methodology and publication notes.
- Transformation and validation metadata.

Store original source snapshots immutably.

New retrievals must not overwrite previously validated source snapshots.

Design for safe retries, idempotent reruns and recovery from interrupted or failed ingestion, following existing engineering conventions.

Do not claim exact point-in-time reconstruction unless supporting evidence is sufficient.

Keep source data outside Git according to existing repository conventions. Commit only appropriate lightweight documentation and validation evidence.

## 7. Structured Outputs

Produce clearly defined structured outputs for downstream processing.

### IUMZID4 Selected Observations

Provide one selected historical rate per observation month, together with:

- Observation month.
- Selected earliest recorded rate.
- Associated source update/publication information.
- First-release evidence status.
- Source and snapshot identifiers.
- Relevant provenance metadata.

Preserve original percentage units.

### IUMZID4 Revision History

Retain the available historical records, including:

- Observation month.
- Recorded value.
- Provisional/final status where available.
- Source update timestamp.
- Event ordering.
- Source and snapshot identifiers.

The revision-history output is retained for auditing and future verification. It does not authorise subsequent revisions to overwrite the selected first-release values.

### Bank Rate

Produce an event-level dataset containing the original effective-date changes and associated policy rates.

Use appropriate data types and preserve provenance.

Codex may determine the exact schemas and file layout, provided they are documented, consistent with the existing architecture, and support all requirements above.

Do not introduce additional data layers or unnecessary abstractions.

## 8. Validation and Testing

Implement appropriate automated tests and independently check selected outputs against official Bank of England data.

### IUMZID4 Validation

Verify:

- XML parsing and schema handling.
- Monthly observation uniqueness.
- Valid dates and numeric values.
- Historical coverage and gaps.
- Earliest-value selection.
- Provisional-value handling.
- Revision ordering and duplicate events.
- Consistency between selected values and retained history.
- Current observations reconciled against the XML source.
- Appropriate treatment of missing revision records.
- Correct preservation of source notes and timestamps.

Use the confirmed Task 007.1 observation examples as regression-test evidence, particularly February 2019 and January 2019.

Include validation of historical backfilled observations.

### Bank Rate Validation

Verify:

- Source extraction correctness.
- Effective-date ordering.
- Numeric rate integrity.
- Duplicate and conflicting records.
- Preservation of rate-change events.
- Reproducibility of repeated ingestion.

### Reliability Testing

Cover normal operation, malformed data, incomplete responses, source-access failures, reruns, conflicting snapshots and recovery scenarios.

Follow existing testing standards.

Do not impose arbitrary statistical usefulness thresholds or reject predictors merely because later modelling may need to account for limitations.

## 9. Documentation and Issue Management

Document:

- Official sources and verified definitions.
- Retrieval methods.
- Output schemas.
- Source snapshots and provenance.
- Validation rules.
- Execution instructions.
- Historical coverage.
- Methodology changes.
- Known limitations.

Update the Data Dictionary with verified source characteristics and implemented outputs.

### 9.1 Project-Owner Decision Rationale

Record the following human-initiated methodological decisions and their stated rationale in:

`docs/development-journal/01-data-ingestion.md`

**Decision 1 — Use first-release IUMZID4 values**

The project owner decided to use the earliest retrievable published IUMZID4 value for each observation month.

**Owner's rationale:**

The intended forecasting workflow generates forecasts when relevant new data becomes available.

Existing forecasts will not be retrospectively regenerated solely because the Bank of England subsequently revises previously published mortgage rates.

Therefore, the historical model-input policy should reflect the initial published information rather than later revised values.

Available historical revisions will be preserved for auditing, but they will not replace the selected first-release observations.

**Decision 2 — Accept the February 2019 methodology change**

The project owner decided to retain IUMZID4 across the February 2019 methodological transition without adjusting the published values.

**Owner's rationale:**

IUMZID4 is directly relevant to BTL financing and provides historical coverage before 2019.

The additional BTL mortgage-rate categories introduced later do not offer equivalent historical coverage for the pre-2019 period.

The Bank of England estimated an overall methodological impact of approximately −0.17 percentage points based on illustrative August–September 2018 comparisons.

The project owner considers this limitation acceptable for the forecasting project and prefers retaining the official observations rather than introducing an unsupported historical correction.

The −0.17 percentage-point estimate must be documented as a limited illustrative comparison, not a universal adjustment factor or evidence that every historical observation experienced the same effect.

**Decision 3 — Preserve historical revisions for audit purposes**

The project owner agreed to preserve the available IUMZID4 historical revision records while retaining the first-release policy for model inputs.

**Owner's rationale:**

The XML source already contains historical revision records.

Retaining these records supports source traceability, reproducibility and independent validation without requiring a separate permanent data-download process.

The stored history is for audit purposes and does not change the approved first-release selection policy.

**Recording requirements**

- Attribute these decisions and their stated rationale to the human project owner.
- Distinguish owner decisions from ChatGPT recommendations and Codex implementation activities.
- Record the decisions as occurring during pre-Task 007 methodological discussions; do not invent an exact decision timestamp.
- Preserve the factual sequence and relevant source references.
- Do not add interpretations, lessons learned or conclusions about AI effectiveness.

### 9.2 Issue Register

Review and update ISS-004 and ISS-005 in:

`docs/issue-register.md`

Record the project owner's approved decisions:

- Use earliest retrievable published IUMZID4 values.
- Include provisional values where they were the earliest recorded version.
- Preserve revision history for auditing.
- Do not use later revisions to replace selected model-input values.
- Accept the 2019 methodology change without correction.
- Defer Bank Rate monthly feature-definition decisions.

Distinguish resolved methodological decisions from remaining source-evidence limitations.

Do not close issues prematurely.

### 9.3 Development Journal

Update:

`docs/development-journal/01-data-ingestion.md`

Record:

- The project owner's decisions and stated reasoning.
- The relevant Task 007.1 investigation findings.
- Codex implementation activities.
- Significant problems, interventions and actual outcomes.

Maintain a factual record of the human–AI development process without evaluating AI effectiveness or drawing lessons learned.

### 9.4 Task Administration

Follow `AGENTS.md` for:

- Verbatim task prompt archiving.
- Execution-time tracking.
- Issue maintenance.
- Engineering standards.
- Documentation and evidence.

Do not modify `AGENTS.md` unless a separate change is required and approved.

## 10. Scope and Constraints

This task authorises Bank of England financing-data ingestion only.

Do not:

- Change the ONS PIPR target ingestion behaviour.
- Implement data joins with Local Authorities.
- Construct monthly financing features.
- Implement statistical correlations or feature selection.
- Train or evaluate ML models.
- Implement forecasting logic.
- Modify the approved 12-month forecast horizon.
- Apply historical mortgage-rate corrections.
- Introduce GCP infrastructure or deployment services.
- Change the approved source variables.
- Make unapproved methodology or architecture changes.

Use existing project dependencies and conventions where practical.

Implementation details, module design and parsing libraries are Codex's responsibility, provided the resulting solution is simple, reliable, maintainable and testable.

## 11. GitHub Workflow

Continue work on:

`feature/007-boe-ingestion`

This branch already contains the completed Task 007.1 investigation.

Before implementation:

- Verify the current branch and working-tree status.
- Confirm Task 007.1 changes are preserved.
- Check the current repository structure and relevant dependencies.
- Do not overwrite or discard existing work.

After Task 007 is complete:

1. Archive the task prompt verbatim.
2. Commit the implementation, tests, documentation and lightweight evidence.
3. Push the completed work to `feature/007-boe-ingestion`.
4. Report the branch name and exact commit SHA.
5. Confirm the remote branch contains the changes.
6. Confirm `main` remains unchanged.

**Do not create a Pull Request.**

**Do not merge into `main`.**

**Do not start Task 008.**

The project owner will decide when the Bank of England ingestion milestone is ready for a Pull Request and eventual merge.

## 12. Acceptance Criteria

Task 007 is complete when:

1. The official Bank Rate ingestion pipeline works.
2. The official IUMZID4 XML ingestion pipeline works.
3. IUMZID4's earliest retrievable recorded values are correctly selected.
4. Provisional values are handled according to the approved policy.
5. Available historical revisions are preserved for auditing.
6. Source availability and evidence limitations are represented accurately.
7. The February 2019 methodology transition is documented without adjusting published values.
8. Source files and relevant provenance are preserved immutably.
9. Both datasets produce validated structured outputs.
10. Relevant tests pass, including failure and rerun scenarios.
11. Selected results are reconciled with official source evidence.
12. Existing PIPR ingestion functionality remains unaffected.
13. The Data Dictionary, issue register and development journal are updated.
14. The project owner's methodological reasoning is recorded factually.
15. Task execution duration is recorded.
16. Changes are committed and pushed to the designated branch.
17. No Pull Request or merge is performed.

If a source limitation prevents reliable implementation, stop the affected component, document the problem and request the necessary decision rather than silently substituting data or weakening validation.

## 13. Final Report

Provide the following information.

### Implementation Summary

- Data sources ingested.
- Retrieval methods.
- Storage layout and output schemas.
- Historical coverage and observation counts.
- First-release selection and revision-history handling.

### Validation Evidence

- Tests executed and results.
- Official-source reconciliation.
- Rerun and failure-handling results.
- Data-quality findings.
- Unresolved limitations.

### Project Governance

- ISS-004 and ISS-005 status updates.
- Development journal updates, including the three owner decisions and their rationale.
- Decisions requiring project-owner approval.
- Task prompt archive path.
- Execution time in minutes.

### GitHub

- Files created or modified.
- Commit SHA.
- Branch name.
- Confirmation of successful push.
- Confirmation that `main` remains unchanged.
- Confirmation that no PR or merge was performed.

Stop after completing Task 007 and reporting the results for independent review.

---

## Implementation report - 21 November 2026

### Scope, decisions and dependencies

Task 007 authorises the two financing sources only. Existing Task 007.1 work
is preserved on `feature/007-boe-ingestion`; its starting HEAD was
`bccc6c47c50da362f371b1c69b97d48e10126097`. No PIPR behavior, features,
forecast horizon, dependencies, infrastructure or AGENTS.md changes.

**Proceed with documented limitations:** ISS-004 and ISS-005 remain Open.
The owner has approved earliest recorded IUMZID4 selection (including provisional
values), audit history preservation and the unadjusted 2019 transition.
Original-publication completeness, timestamp timezone and complete release
calendars remain source-evidence limitations. ISS-014 is a later operational
cutoff decision and does not block retrieval. LA/geography issues, later source
contracts and the Glenigan rights gap are outside this national-source task.
No new data substitution or owner decision is required for these outputs.

### Official source contract and access

- Bank Rate: [official history](https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp),
  HTML `stats-table`, exact headings `Date Changed` and `Rate`. These are
  effective-date events, not verified announcement timestamps. The available
  page begins on 20 January 1975; no earlier history is claimed.
- IUMZID4: [official selection page](https://www.bankofengland.co.uk/boeapps/database/index.asp?EC=IUMZID4&From=Template&G0Xtop.x=1&G0Xtop.y=1&Travel=NIxSUx),
  documented [XML interface](https://www.bankofengland.co.uk/boeapps/database/Help.asp).
  `_iadb-fromshowcolumns.asp`, `CodeVer=new`, `xml.x=yes`,
  `Datefrom=01/Jan/2012`, configurable `Dateto`, `SeriesCodes=IUMZID4`,
  `UsingCodes=Y`, `VPD=Y`, `VFD=Y`, `VUD=A`, `VUDdate=03/Jun/2007`.
  `VUDdate` is an update-history filter baseline, not an as-of date.
  The full-history request succeeded: no source size limit or need for chunking
  was encountered. Future releases extend the end date; October 2026 is not a
  permanent endpoint. Requests fail clearly on size limits or incomplete data.
  No silent fallback to CSV or removal of history is implemented.
- [Legal terms](https://www.bankofengland.co.uk/legal), checked 21 November 2026:
  database numeric data reuse is under the UK Open Government Licence, subject
  to listed third-party exceptions. Neither selected source was listed as an
  exception. This does not license underlying lender/Moneyfacts microdata.
  Attribution: Bank of England Database; copyright Governor and Company of the
  Bank of England; OGL v3.0. Publisher prose/articles are referenced rather than
  redistributed as full documents. Access is unauthenticated, with a browser
  user agent following the Task 007.1 demonstrated request behavior. The Bank
  reserves the right to restrict excessive requests; reruns avoid downloading.

### Execution, storage and reproducibility

```powershell
uv run python -m ingestion.boe --snapshot-id 2026-11-21-task007 --end-date 2026-11-21
uv run pytest -q
uv run python reports/data_audits/007/validate_live.py
```

The last command reproduces the retained Task 007 audit against that local
snapshot, optionally downloading its single official CSV comparison if absent.
It is not a permanent production CSV process. For a new source retrieval use
a new `--snapshot-id` and current `--end-date`; use `--dataset` to operate one
source independently. Storage reads `configs/storage.toml`; only its existing
local backend is implemented. No GCP deployment is added.

Each layer uses
`bank_of_england/{bank_rate|iumzid4}/snapshot={snapshot_id}/`:

| Layer | Files | Purpose |
| --- | --- | --- |
| raw | `response.bin`, `manifest.json` | Original bytes, exact URL/encoded request parameters, UTC retrieval interval, request/response headers, resolved URL, status, checksum and identity |
| validated IUMZID4 | `current.parquet`, `history.parquet`, `manifest.json` | Parsed current observations, ordered distinct retained states and full metadata |
| processed IUMZID4 | `selected.parquet`, `history.parquet`, `manifest.json` | Earliest recorded selections and independently retained audit history |
| validated/processed Bank Rate | `events.parquet`, `manifest.json` | Source text plus typed effective-date events |

Every table carries `source_id`, `source_snapshot_id`, `source_sha256` and
`retrieved_at` (UTC ISO string). Derived manifests link the raw checksum and
retrieval metadata, transformation version `boe-ingestion-v1`, units, attribution,
source metadata, coverage, counts and evidence limitations. Structured metadata
retains all non-observation XML nodes including both dated source notes.
`source_notes_xml` retains each observation subtree without dropping attributes
or observation comments. Exact raw bytes remain the authoritative source.

Directories are staged beside their destination then renamed as a complete
bundle. Existing bundles require matching identities and verified file hashes;
they cannot be overwritten. An existing raw snapshot is verified and reused
without fetching. A parse failure retains raw evidence and publishes no new
validated/processed bundle. A failure after validated publication can resume
from raw and reuse the matching validated bundle. Abandoned `.staging-*`
directories are ignored; they can be inspected and manually removed when no
process is using them. Incomplete named bundles or checksum conflicts stop
execution for investigation; do not delete a previously validated snapshot to
force replacement. No mutable latest pointer is maintained. Each dataset is
independent; failure in one does not invalidate an already completed other one.

Transport errors and transient HTTP 429/5xx failures get at most three attempts
with bounded waits; permanent access failures and malformed source data stop.
Responses have timeout, nonempty, size, declared-length and redirect checks.
Previously retained selections/events are checked against earlier completed
snapshots before promotion. A changed earliest value/status/update event,
missing previously retained month or altered Bank Rate event requires review;
later revised values cannot silently replace a saved selected value. Earlier
snapshots can be rerun after later retrievals without asserting that future
observations should exist in an older source response.

### Table schemas and validation

| Table | Key | Additional fields and types |
| --- | --- | --- |
| IUMZID4 current | `observation_month` string `YYYY-MM` | `source_observation_date` date; `rate_percent` float64; exact `source_value_text`; `observation_status` provisional/final; exact naive `source_updated_at` string; `record_origin`; `source_attributes_json`; `source_notes_xml` |
| IUMZID4 history | `observation_month`, `event_order` int64 | Same value/date/status/update/attribute fields; event origin; all common provenance fields |
| IUMZID4 selected | `observation_month` | Earliest history row and order; `first_release_evidence_status=earliest_recorded_not_certified`; `history_evidence=revision_records` or `current_update_only`; `pre_introduction_backfill` bool; observation XML and provenance |
| Bank Rate events | `effective_date` date | `rate_percent` float64; exact `source_date_text`, `source_value_text` and common provenance fields |

Source percentage values are neither rescaled nor statistically corrected.
The stored numeric representation is float64; exact original decimal strings
are also retained. Date columns round-trip through Parquet as dates. No
`published_at`/`available_at` timestamp is invented.

IUMZID4 gates require one correct series, monthly frequency, percentage units,
month-end source dates, numeric finite rates, unique months, consecutive coverage
from January 2012 and agreement with source FIRST_OBS/LAST_OBS bounds. Revision
events require a single value/status, valid exact source timestamp, unique
ordering and consistency with current state. A revision that repeats the current
state is represented once in history; both representations remain in raw XML
and the current observation subtree. Same-number provisional-to-final changes
remain separate events. Duplicate revisions, conflicting same-time events and
revisions newer than current stop ingestion. Missing revision children yield
`current_update_only`, never a claim that no earlier publication existed.

Bank Rate gates require the complete identified table and exact headings,
valid effective dates, finite numeric rates, unique strictly descending source
dates and the observed 1975 boundary. Ascending processed ordering preserves
every event. Two-digit years use the table's 1975 boundary explicitly rather
than Python's implicit moving pivot; dates at/after 2075 require a source-contract
update. No monthly averages, month-end values or cutoff rates are created.

### Measured outputs and official reconciliation

Snapshot `2026-11-21-task007`, retrieved 21 November 2026:

| Source | Observation coverage | Count |
| --- | --- | ---: |
| IUMZID4 selected/current | January 2012-October 2026, consecutive | 178 each |
| IUMZID4 history | Same observation range, including retained provisional/final states | 336 |
| Bank Rate | 20 January 1975-5 November 2026, effective-date events | 259 |

[Validation evidence](../reports/data_audits/007/validation-evidence.json)
retains exact requests, retrieval metadata, checksums, output counts, ten selected
regressions and rerun outcomes. The separate official CSV matched all **178**
XML current observations. Ten earliest recorded selections match the previously
retained Task 007.1 examples, including January 2019 **2.36 provisional** and
February 2019 **2.17**, while their current values are 2.37 and 2.22 respectively.
An independent regular-expression extraction matched all **259** Bank Rate
source rows; official page examples checked include 20 January 1975 (11.25),
19 March 2020 (0.10) and 5 November 2026 (4.00). Both production snapshots
reran offline with identical file hashes. Original bodies/Parquet are ignored
local data; GitHub contains the lightweight evidence and replay script, not the
full source datasets. Audit comparison bytes reside under
`data/raw/bank_of_england/audit/snapshot=2026-11-21-task007/`.

### Methodology and remaining limitations

The [Task 007.1 verified source findings](007.1-iumzid4-historical-revisions-and-publication-vintages.md#february-2019-methodology-context)
apply. From February 2019 wider lender coverage and monthly averages replaced
the earlier ER-sample/end-month basis. BTL uses quarterly MLAR weights on both
sides of the transition. The July 2018 population expansion is preserved.
Published history is unadjusted. The Bank's **-0.17 percentage-point** estimate
is a limited illustrative August-September 2018 comparison, not a correction
factor for every historical observation. Later BTL categories lack equivalent
pre-2019 coverage; the owner accepts this limitation for the selected series.

IUMZID4 was introduced in October 2016 with backfill to January 2012.
Pre-introduction observations are flagged and must not be treated as available
at their observation dates. All selected values carry uncertified original-
publication status: completeness of earlier provisional events, exact public
availability and source timestamp timezone remain unverified. The database
update-since baseline is not proof of a complete first-release archive.
Current publication cadence must not be extrapolated into a complete historical
calendar. Future feature engineering must respect these availability limits;
exact point-in-time reconstruction is not claimed. Bank Rate effective dates
also do not establish precise public announcement times.

The sandbox prevented network connections and initially denied reads of files
created by approved external runs; approved network/filesystem executions
completed validation. These tool restrictions do not imply source unavailability.
The optional Black formatter was unavailable; no dependency was added solely
for formatting. Final test totals, timing and Git handoff are recorded below.

### Final validation and review handoff

`uv run pytest -q`: **70 passed**, including all pre-existing PIPR/environment
tests and 36 Bank of England tests. The final run completed in 20.21 seconds.
Tests cover parsing, history/status selection, duplicate/conflicting dates and
events, malformed/non-finite/incomplete responses, source access/retry failures,
raw/output corruption, immutable conflicts, reruns, interrupted publication
recovery and changed historical selections/events. Sandbox cache restrictions
required the final suite to run with approved filesystem access; no test was
skipped for that reason.

Live reconciliation and offline reruns passed using
`reports/data_audits/007/validate_live.py`; the audit evidence JSON is committed.
Archive byte-prefix comparison passed against the original attachment (before
this appended report). Python syntax, evidence JSON, exactly seven CSV columns
with unique text task IDs, 100 local Markdown file targets and `git diff --check`
passed. Anchor targets were reviewed for the new report links; the file-target
check does not assert all pre-existing anchors. PIPR code/tests and configuration
are unchanged. Optional Black could not run because its executable is absent.

Ten files comprise this task: README, this archive/report, the dictionary,
issue register, ingestion journal, shared timing CSV, ingestion module, its
tests and the audit replay script/JSON. Raw source bytes, audit CSV and Parquet
outputs remain ignored local data. Task 007.1 evidence is unchanged. No additional
task, source ingestion, PR or merge is authorised or performed.

Remote `main` baseline checked before publication:
`3f8ee0346909f52b3a31fb17eee0c20966c62c9b`; local `main` baseline:
`a28323e4c70b5afa551de619a19d87087ec329ae`.
Publication verification and final measured timing follow after the first push.

Task 007 is **Completed** for independent review. Implementation commit
`f73119a05b6eea046c61cac47954f19e9797da48` was pushed to
`feature/007-boe-ingestion` and matched the remote branch. Remote main remained
`3f8ee0346909f52b3a31fb17eee0c20966c62c9b`; local main remained
`a28323e4c70b5afa551de619a19d87087ec329ae`. No PR or merge was performed;
Task 008 was not started. The final timing/handoff commit follows this cutoff
and will also be pushed; its exact SHA is supplied in the final user report.

Measured start: **2026-11-21T12:49:19+00:00**; end:
**2026-11-21T13:02:08+00:00**; **769 seconds / 60 = 12.816667 minutes**.
Evidence is the UTC clock tool, with whole-second precision. Initial
attachment/standards reading before the first clock reading is excluded.
Tool/network/approval waits within the interval are included and were not
separately measured. Final timing/handoff write, commit, push, verification and
response are outside the cutoff. One measured session; no estimated active
execution time or between-session gaps are included. The shared CSV contains
one row for Task 007 and retains all prior task records.
