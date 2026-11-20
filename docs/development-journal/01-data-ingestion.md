# Data ingestion development journal

This journal records significant events in the current data-ingestion stage.
The ten retrospective entries preceding Task 006.8 were reconstructed on
20 November 2026 from the
linked repository evidence. Dates describe the event or explicitly identified
evidence timestamp, not the date of reconstruction. Where event dates are
unavailable, entries follow documented task order; that order does not establish
exact execution dates. A task request establishes human instructions, not proof
of execution or the identity of the historical implementer. Unknown attribution
is stated explicitly. Detailed findings remain in their source documents.

## Early context - Tasks 001-004.1 (event dates unavailable)

- **Event/trigger:** Local project foundations and source design preceding ingestion.
- **Initiated by:** Human, as recorded in the archived setup/design requests.
- **Human actions:** Requested modular local development with uv, version control,
  configurable storage and future GCP compatibility. Task 004.1 states the owner
  independently verified IUMZID4 and directed correction of the BTL source.
- **AI actions:** Historical executor and any ChatGPT advisory role are not
  established by these prompts. Current files and Git history establish project
  artifacts, not the date or reasoning of earlier conversations.
- **Decision and rationale:** Task 004 is a design proposal, not blanket approval
  of future architecture. The stated BTL correction uses the owner's verified series.
- **Outcome/status:** README and the initial setup commit record local foundations;
  the dictionary retains IUMZID4. No earlier execution dates are inferred.
- **Evidence/references:** [Setup](../001-initial-project-structure-setup.md),
  [environment](../002-python-development-environment-setup.md),
  [Git request](../003-git-and-github-repository-setup.md),
  [design scope](../004-design-rental-forecasting-data-architecture-data-dictionary.md),
  [BTL correction](../004.1-update-data-dictionary-verified-buy-to-let-mortgage-rate-series.md),
  [README](../../README.md),
  [initial setup commit](https://github.com/chanmlh026/rental-forecasting/commit/a835c70).

## Early context — Task 004.2 (event date unavailable)

- **Event:** Confirmation of the forecast horizon and target.
- **Initiated by:** Human.
- **Human actions / attribution:** Human confirmed Option A in the archived instruction;
  executor of the historical documentation update is not established here.
- **Action:** Defined the origin as the latest eligible published rent month and
  the target as monthly GBP rent exactly 12 calendar months later.
- **Outcome/status:** Confirmed decision, retained in the dictionary; operational
  cutoff and evaluation policies remain separate unresolved decisions.
- **Evidence/references:** [Human instruction](../004.2-finalise-forecast-origin-target-horizon-and-publication-cutoff-definitions.md),
  [target specification](../data-architecture-and-dictionary.md#4-target-variable-specification).

## 24 October 2026 — Task 005.1 workbook inspection (retrieval date)

- **Event:** PIPR target coverage and archive comparison documented.
- **Human actions / attribution:** Historical initiator and inspector are not established
  by the audit; it records inspection with Excel COM.
- **Action:** Inspected the October 2026 and March 2024 workbooks against the
  dated English LA reference.
- **Outcome/status:** Audit reports 124,362 valid cells for 294 LAs and three
  bedroom categories in the latest inspected edition. City of London and Isles
  of Scilly are absent; the archive lacks Barnsley and Sheffield. Overlapping
  vintage differences are observed, with causes unestablished. The audit's
  recommendation of a 294-LA cohort was conditional, not itself an approval.
- **Evidence/references:** [Audit and retrieval record](../005.1-ons-pipr-workbook-coverage-audit.md),
  [audit outputs](../../reports/data_audits/005.1/),
  [ISS-003 and ISS-004](../issue-register.md#issues).

## 24 October 2026 — Task 006 initial ingestion (retrieval date)

- **Event:** Initial PIPR release ingestion and reuse recorded.
- **Human actions / attribution:** The guide identifies the cohort as approved;
  the original approval conversation and historical executor are not supplied
  by this evidence. No approval date or implementer is inferred.
- **Action:** Registered immutable workbook bytes and metadata; validated and
  published the approved 294-LA, 1-/2-/3-bedroom rent observations.
- **Outcome/status:** Guide reports 124,362 processed rows, no missing or duplicate
  target cells, passed validation and 25 movements flagged for review. A second
  run reused matching outputs. Retrieval time is not an exact execution interval
  or source publication timestamp. No features or model were produced.
- **Evidence/references:** [Approved scope and initial run results](../006-ons-pipr-ingestion.md),
  [historical timing limits](../task-execution-log.csv).

## Task 006.1 — Reliability hardening (event date unavailable; after Task 006)

- **Event:** Release-reuse validation and interrupted publication recovery.
- **Initiated by:** Human.
- **Human actions / attribution:** Human requested focused hardening in the restored
  prompt; historical executor is not established by the linked guide.
- **AI actions:** Historical executor unestablished.
- **Action:** The guide documents output content checks, a completion marker,
  recovery of a missing layer, and explicit future-release coverage bounds.
- **Outcome/status:** Documented behavior preserves immutable releases and fails
  on corrupt or conflicting outputs. Publication across two directories is not
  atomic. The restored prompt ends at Section 4; the missing remainder is not
  reconstructed from implementation behavior.
- **Evidence/references:** [Restored human instruction](../006.1-harden-ons-pipr-ingestion-reliability-and-release-validation.md),
  [implemented behavior](../006-ons-pipr-ingestion.md#storage-layout-and-versioning),
  [ISS-018](../issue-register.md#issues).

## 8 November 2026 — Task 006.2 predictor exploration

- **Event:** Candidate source availability and limitations investigated.
- **Initiated by:** Human.
- **Human actions / attribution:** Human requested research, excluding production
  ingestion; Codex execution is identified in the timing record. The archived
  task permits independent routine technical investigation; individual research
  choices are not attributed to a separate human instruction without evidence.
- **AI actions (Codex):** Assessed candidate sources and updated the dictionary with measured
  extracts, source limitations and proposed ingestion batches.
- **Outcome/status:** Evidence includes eight successful extract downloads and
  an ASHE ZIP 403. Geography, definitions, coverage and vintage questions remain
  open; proposed Tasks 007–013 are not implementation approval.
- **Evidence/references:** [Task scope](../006.2-predictor-data-availability-and-quality-exploration.md),
  [findings and scope limits](../data-architecture-and-dictionary.md#verification-record-and-scope-limits),
  [extract evidence](../../reports/data_audits/006.2/predictor-exploration-evidence.json),
  [Codex timing evidence](../task-execution-log.csv).

## 8 November 2026 — Tasks 006.3 and 006.4 execution evidence

- **Event:** Manual task timing introduced and historical timing investigated.
- **Initiated by:** Human.
- **Human actions / attribution:** Human requested both activities; Codex execution
  sessions are identified in the CSV.
- **AI actions (Codex):** Added timing instructions and one shared CSV; inspected available
  session records for earlier task intervals.
- **Outcome/status:** Task 006.2 duration was recovered; original Task 001–006.1
  intervals remain unavailable. Git timestamps were not used as execution times.
- **Evidence/references:** [Tracking request](../006.3-task-execution-time-tracking.md),
  [recovery request](../006.4-historical-task-execution-time-recovery.md),
  [recorded outcomes and session evidence](../task-execution-log.csv).

## 8 November 2026 — Tasks 006.5 and 006.6 review preparation and restoration

- **Event:** Completed ingestion-stage work prepared for review; Task 006.1
  instructions restored from Word.
- **Initiated by:** Human.
- **Human actions / attribution:** Human requested review preparation and restoration;
  Codex execution sessions and review outcome are recorded in the CSV.
- **AI actions (Codex):** Prepared Draft PR #1 and restored the available prompt text,
  correcting references to its absence.
- **Outcome/status:** Timing record reports review publication and restoration;
  the Word source ends at Section 4. No missing requirements or historical
  execution times were invented. This entry does not infer later review actions.
- **Evidence/references:** [Review task](../006.5-prepare-completed-tasks-for-github-review.md),
  [restoration task](../006.6-restore-task-006.1-documentation-to-review-branch.md),
  [outcomes and source hash](../task-execution-log.csv),
  [ISS-018](../issue-register.md#issues).

## 8 November 2026 — Task 006.7 issue register and review amendment

- **Event:** Shared issue register introduced; source-rights scope clarified.
- **Initiated by:** Human.
- **Human actions / attribution:** Human requested the register and subsequent review
  corrections; Codex execution sessions are identified in the timing record.
- **AI actions (Codex):** Indexed 18 issues and added dependency checks to AGENTS.md.
  Following review instructions, separated recurring task authorisation from
  the concrete Glenigan extract rights gap in ISS-017.
- **Outcome/status:** All 18 issues remained Open. Clarification did not approve
  new ingestion or resolve source-specific access/licensing concerns.
- **Evidence/references:** [Original and subsequent instructions](../006.7-introduce-project-issue-register-and-dependency-checks.md),
  [dated scope clarification](../issue-register.md#iss-017-scope-clarification---8-november-2026),
  [execution evidence](../task-execution-log.csv).

## 8 November 2026 - Review merges (GitHub event dates)

- **Event/trigger:** Published review branches were merged after their task work.
- **Human actions:** The identity and reasoning of the merger are not established
  by the PR metadata inspected here; no review approval is inferred.
- **AI actions:** Codex had prepared the review work as recorded in the timing CSV.
- **Outcome/status:** GitHub metadata records PR #1 merged at 12:41:41 UTC and
  PR #2 at 14:42:01 UTC. PR #2 metadata returned no formal reviews or comments;
  its corrective instructions are evidenced by the archived owner request,
  without assigning an unsupported reviewer identity.
- **Evidence/references:** [PR #1](https://github.com/chanmlh026/rental-forecasting/pull/1),
  [PR #2](https://github.com/chanmlh026/rental-forecasting/pull/2),
  [correction instructions](../006.7-introduce-project-issue-register-and-dependency-checks.md),
  [execution evidence](../task-execution-log.csv).

## 20 November 2026 - Human requirement for a development journal (Task 006.8)

- **Event/trigger:** Owner identified a need for a factual journal before Task 007.
- **Initiated by:** Human; the original prompt explicitly supplies this evidence.
- **Human actions:** Stated that task logs, issue records and prompt archives did
  not capture the full development process; proposed recording events, decisions,
  human actions, AI actions and outcomes, explicitly including human-initiated
  ideas. Rejected premature interpretation, learning assessments and conclusions
  about AI-assisted development.
- **AI actions (Codex):** Implemented the journal and maintenance instructions;
  no separate ChatGPT advisory contribution is established here.
- **Decision and rationale:** Owner required a factual, event-based journal and
  amended its organisation to one file per stage. The stated record-coverage gap
  is owner-provided evidence; the earlier recognition date is unavailable.
- **Outcome/status:** Current ingestion journal created; future-stage journals
  are to begin only with those stages. Dated update, 20 November 2026:
  combined requirements checked and [Draft PR #3](https://github.com/chanmlh026/rental-forecasting/pull/3)
  published for independent review; no merge performed.
- **Evidence/references:** [Original prompt and amendment](../006.8-stage-specific-development-journals.md),
  [journal rules](../../AGENTS.md#development-process-journal).

## 20 November 2026 - AI identification of missing task evidence (Task 006.8)

- **Event/trigger:** Original Task 006.8 instructions were absent when the amendment
  was first implemented.
- **Initiated by:** AI, identifying the evidence gap during authorised review.
- **Human actions:** Subsequently confirmed only the amendment had previously
  been supplied, provided the original and directed continued work without merging.
- **AI actions (Codex):** Searched available records, requested the missing text,
  recorded ISS-019, preserved the amendment work and reported incomplete status.
- **Decision and rationale:** Codex left full verification pending rather than
  inventing missing instructions; owner supplied the original to continue.
- **Outcome/status:** Initially In Progress. Dated update, 20 November 2026:
  original now archived verbatim before the amendment; evidence gap resolved
  after archive comparison. Prior incomplete status remains in the task report.
- **Evidence/references:** [Instructions and prior report](../006.8-stage-specific-development-journals.md),
  [ISS-019](../issue-register.md#issues), [timing record](../task-execution-log.csv).


## 20 November 2026 - IUMZID4 vintage investigation (Task 007.1)

- **Event/trigger:** Owner requested evidence on IUMZID4 historical revisions
  before finalising the Bank of England ingestion design.
- **Initiated by:** Human, through the Task 007.1 instructions.
- **Human actions:** Retained IUMZID4 without statistical correction, required
  documentation of the February 2019 transition, deferred modelling treatment
  and authorised source investigation only. No Task 007 implementation or PR.
- **AI actions (Codex):** Checked official documentation and tested ten selected
  months through XML, current CSV and HTML/Excel exports. Retained requests,
  response metadata, parent-linked revision extracts and failed-method evidence.
- **Decision and rationale:** Codex recommends considering XML history alongside
  immutable current-source snapshots because actual historical value changes
  were demonstrated; this recommendation is not an approved ingestion design.
- **Outcome/status:** XML returns earlier and revised values, including provisional
  states. HTML previous-value controls were not demonstrated; filter attempts
  returned application errors. Complete first-publication coverage and source
  timestamp timezone remain unverified. ISS-004/ISS-005 remain Open; their evidence
  and remaining actions were updated. No published values were adjusted and no
  production ingestion, feature engineering or modelling was implemented.
- **Evidence/references:** [Owner instructions and investigation](../007.1-iumzid4-historical-revisions-and-publication-vintages.md),
  [retained source evidence](../../reports/data_audits/007.1/),
  [ISS-004/ISS-005](../issue-register.md#issues),
  [timing record](../task-execution-log.csv).
