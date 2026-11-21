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
  Dated update, 20 November 2026: investigation completed and findings/evidence
  pushed to feature/007-boe-ingestion for independent review; no PR or merge.
- **Evidence/references:** [Owner instructions and investigation](../007.1-iumzid4-historical-revisions-and-publication-vintages.md),
  [retained source evidence](../../reports/data_audits/007.1/),
  [ISS-004/ISS-005](../issue-register.md#issues),
  [timing record](../task-execution-log.csv).

## Pre-Task 007 discussions - owner methodological decisions (date not established)

- **Event/trigger:** Financing-source policy decisions during methodological
  discussions before Task 007; exact decision dates/times are not supplied.
- **Initiated by:** Human project owner, as explicitly attributed in Task 007.
- **Human actions:** Approved earliest retrievable published IUMZID4 values,
  including provisional first states; accepted the February 2019 transition
  without changing published rates; required preservation of available revisions
  for audit rather than replacement of selected model inputs.
- **Decision 1 and stated rationale:** Forecasts are generated when relevant new
  data becomes available. Existing forecasts will not be regenerated solely
  because the Bank later revises mortgage rates, so historical inputs should
  reflect initially published information rather than retrospective revisions.
- **Decision 2 and stated rationale:** IUMZID4 directly represents BTL financing
  and supplies pre-2019 history not matched by later BTL categories. The owner
  accepts the documented methodology limitation, preferring official unchanged
  observations to an unsupported correction. The Bank's approximately -0.17pp
  estimate is a limited illustrative August-September 2018 comparison, not an
  effect for every historical observation or a universal adjustment factor.
- **Decision 3 and stated rationale:** XML already carries historical revision
  records. Retaining them supports traceability, reproducibility and independent
  validation without a separate permanent download process; audit history does
  not change the first-release input policy.
- **AI actions / attribution:** Task 007.1 previously demonstrated selected XML
  histories and recommended considering that interface. The supplied Task 007
  instructions attribute these decisions and reasons to the owner. Separate
  ChatGPT recommendations or discussion timestamps are not established here.
- **Outcome/status:** Approved ingestion policy; earliest database events must
  still be labelled uncertified when original-publication completeness is unknown.
- **Evidence/references:** [Task 007 original instructions, sections 2 and 9.1](../007-boe-bank-rate-and-iumzid4-ingestion.md),
  [Task 007.1 findings](../007.1-iumzid4-historical-revisions-and-publication-vintages.md#investigation-report---20-november-2026).

## 21 November 2026 - Task 007 financing ingestion implementation

- **Event/trigger:** Owner supplied the production ingestion task and authorised
  committing/pushing to the existing milestone branch, without a PR or merge.
- **Initiated by:** Human.
- **Human actions:** Supplied the source contracts, approved policies and stated
  rationale above; required immutable provenance, tests and independent checks.
- **AI actions (Codex):** Verified clean Task 007.1 branch state, reviewed relevant
  issues/standards/code, archived the prompt, implemented XML revision selection
  and Bank Rate HTML extraction, immutable layer publication, reruns and recovery.
  Retrieved both sources and an audit-only CSV; verified all 178 current mortgage
  observations, ten earlier-record selections and all 259 Bank Rate rows.
- **Significant problems/interventions:** Sandbox network access was refused;
  approved external execution succeeded. Reads of externally written ignored
  files needed approved execution. An initial test decorator syntax error was
  corrected before tests passed. Optional Black executable was absent; no new
  formatting dependency was introduced.
- **Decision and stated rationale:** Codex used the demonstrated full-history XML
  route because it supplied the complete current range and retained history in
  one request. It kept source timestamp strings and explicit uncertified evidence
  rather than inferring public availability. No statistical correction was made.
- **Outcome/status:** Live snapshot contains 178 selected months and 336 retained
  states; Bank Rate contains 259 change events. Offline reruns preserve hashes.
  ISS-004/ISS-005 remain Open with approved ingestion choices distinguished from
  remaining evidence and later feature decisions. Tests and Git handoff are
  reported in the task's final validation record; no implementation of Task 008.
  Dated update, 21 November 2026: all 70 tests passed; implementation commit
  `f73119a05b6eea046c61cac47954f19e9797da48` pushed and matched the remote
  milestone branch; local/remote main unchanged. Task 007 completed for review,
  with no PR or merge. Measured timing is recorded in the shared CSV.
- **Evidence/references:** [Task/report](../007-boe-bank-rate-and-iumzid4-ingestion.md#implementation-report---21-november-2026),
  [source and rerun evidence](../../reports/data_audits/007/validation-evidence.json),
  [issue update](../issue-register.md#task-007-update---21-november-2026),
  [execution timing](../task-execution-log.csv).

## 21 November 2026 - Independent-review HTTP metadata correction (Task 007.2)

- **Event/trigger:** Independent review identified session-cookie response headers
  in committed Task 007 validation evidence; owner requested correction.
- **Initiated by:** Human, through the supplied review finding and task.
- **Human actions:** Authorised safe header handling, current-evidence cleanup,
  tests and a history-remediation assessment. Required preserving immutable data
  and expressly prohibited history rewriting without separate owner approval.
- **AI actions (Codex):** Confirmed two exposed header fields, traced complete
  header capture and legacy export paths, implemented provenance allowlisting at
  capture/publication/read/export boundaries, and regenerated the current JSON.
  Checked Task 007/007.1 artifacts without printing values; added regression tests.
- **Decision and stated rationale:** Codex used an allowlist so unknown session,
  auth or custom headers are excluded by default while keeping source provenance.
  Existing manifests are filtered in memory to preserve immutable on-disk evidence.
- **Outcome/status:** 76 tests passed. All 16 existing snapshot files, including
  six Parquet files, remain byte-for-byte unchanged. Current evidence differs
  only by excluded headers. No equivalent exposure found in Task 007.1 JSON.
  Two pushed historical commits still contain the original fields; ISS-020
  remains Open for an owner risk/remediation decision. Cookie validity/scope
  has not been established; no session replay, PR, merge or history rewrite.
- **Evidence/references:** [Owner prompt and correction report](../007.2-harden-boe-http-metadata-and-validation-evidence.md),
  [verification outcomes](../../reports/data_audits/007.2/validation-evidence.json),
  [ISS-020](../issue-register.md#issues), [timing CSV](../task-execution-log.csv).
  Dated update, 21 November 2026: correction commit
  `f8cb66d1ddcc9a4efc2374af2cf9b0833bd5fe06` pushed and matched the remote
  milestone branch; local/remote main unchanged. Task 007.2 completed for review
  with ISS-020 remaining Open; final timing is in the shared CSV.

### 21 November 2026 update - owner acceptance of ISS-020 residual risk (Task 007.3)

- **Event/trigger:** Owner reviewed the Task 007.2 findings and supplied an
  explicit resolution instruction after the initial correction handoff.
- **Initiated by:** Human.
- **Human actions:** Accepted residual historical session-cookie exposure in
  the private repository with the implemented preventive controls; expressly
  prohibited history rewriting, force pushes and session invalidation.
- **AI actions (Codex):** Archived the instruction verbatim and updated ISS-020
  to Resolved, preserving earlier Open status and findings as dated history.
  The owner subsequently formalised this documentation work as Task 007.3;
  Codex retained the preliminary edits and tracked its measured intervals
  separately from the completed Task 007.2 technical correction.
- **Decision and stated rationale:** Explicit owner risk acceptance based on
  private-repository context and preventive controls. Expiry/access scope have
  not been independently verified and historical values remain accessible.
- **Outcome/status:** Resolved through owner acceptance, not confirmed removal
  or expiry. No code, ingestion data or methodology changes; no invalidation,
  history rewrite, force push, PR or merge.
- **Evidence/references:** [Verbatim owner decision](../007.2-harden-boe-http-metadata-and-validation-evidence.md#owner-resolution-instruction---21-november-2026-verbatim),
  [Task 007.3 instructions and validation](../007.3-record-iss-020-owner-risk-acceptance.md),
  [ISS-020](../issue-register.md#issues), [timing CSV](../task-execution-log.csv).

## 21 November 2026 - Bank of England milestone Draft PR preparation (Task 007.4)

- **Event/trigger:** Owner requested one milestone Draft PR for Tasks 007.1,
  007, 007.2 and 007.3, reporting an independent review result of Pass with
  documented limitations. Reviewer identity and a separate formal GitHub review
  are not established by that instruction.
- **Initiated by:** Human.
- **Human actions:** Authorised Draft PR creation into main if none existed,
  retaining final approval/merge control and prohibiting methodology changes,
  history rewriting, force pushes, merging and Task 008 work.
- **AI actions (Codex):** Verified a clean branch matching remote at
  `bbcda06f4b70948477fc11467a29ed80be0e2d5f`, fetched remote refs and searched
  existing PRs without finding one for the milestone branch. Reviewed evidence
  and issue dispositions; prepared a summary separating approved input policy,
  source-evidence limits and owner-accepted historical cookie exposure.
- **Outcome/status:** PR preparation in progress; publication and available
  check results will be recorded in the Task 007.4 report. ISS-020 is Resolved
  by owner acceptance; ISS-004/ISS-005 remain Open. No implementation changes.
  Dated update, 21 November 2026: [Draft PR #4](https://github.com/chanmlh026/rental-forecasting/pull/4)
  created; GitHub reports a clean, mergeable draft, zero status checks/workflow
  runs and an empty check rollup. No CI workflow is configured; 76 local tests
  passed. Approval/merge remain with the owner; no merge performed.
- **Evidence/references:** [Task 007.4 prompt/report](../007.4-prepare-boe-ingestion-milestone-pull-request.md),
  [issue register](../issue-register.md#issues), [execution timing](../task-execution-log.csv).

## 21 November 2026 - Approved inflation/HPI decisions and implementation (Task 008)

- **Event/trigger:** Owner authorised Task 008 after the Bank of England milestone.
  Codex observed remote main at merge commit `48bae0947f294d59631cb160e73b5a7aeeefc62a`;
  this records the observed baseline, not an inferred merge actor or exact time.
- **Initiated by:** Human.
- **Human actions:** Approved both CPI and CPIH, their annual rates and index
  levels, all-property HPI price/index for the existing 294-LA cohort, and
  preservation of original vintages and available revisions. Required source
  coverage/reconciliation, immutable provenance and no feature/model work.
- **Owner decision 1 and stated rationale:** Retain both CPI and CPIH because
  ingestion collects potentially relevant official predictors without deciding
  usefulness early. Their concepts differ; usefulness, overlap with rent data
  and possible correlation will be evaluated during later preprocessing/modelling.
- **Owner decision 2 and stated rationale:** Retain published inflation rates
  and underlying indices to allow later feature development without prematurely
  fixing final model inputs.
- **Owner decision 3 and stated rationale:** Retain all-property LA HPI measures
  because local property-market conditions may inform rent forecasts; predictive
  usefulness remains unestablished and will be evaluated later.
- **Owner decision 4 and stated rationale:** Keep original snapshots and available
  revision information so future preprocessing/backtests can distinguish reference
  periods from information available at forecast cutoffs. No first-release policy
  for these sources was approved by the IUMZID4 decision.
- **AI actions (Codex):** Archived the task, created the dedicated branch from
  merged main, checked official sources/licences and dependencies, reused existing
  immutable/security primitives, and implemented the two independent source
  contracts. Retained four current/prior ONS pairs and two HPI releases with
  England revision matrices; produced full-source/cohort/coverage Parquet.
- **Significant problems/interventions:** Sandbox access required approved
  retrieval. HPI's visible publication date needed a validated text fallback;
  independent attribute exports had different date/headings from the full file.
  An audit-script syntax error was corrected before final validation. No missing
  source data, values or geographic mappings were invented to bypass failures.
- **Decision and rationale (Codex implementation):** Preserve each release rather
  than select earliest values, matching the authorised vintage policy. Use exact
  official codes for the cohort, with both source/approved names retained.
  The release summary confirms HPI's Jan 2023 base; no re-reference is calculated.
- **Outcome/status:** 117 tests passed. All 1,840 current inflation observations
  and each of 152,730 HPI price/index rows reconciled with independent official
  exports. The Sep HPI cohort has 294 x 381 complete months; 11 name differences
  are flagged. Aug/Sep cohort revisions are retained (3,523 prices/2,843 indices).
  Sixty snapshot files remained unchanged on offline reruns. ISS-003/004/012/013
  were updated and remain Open; ISS-014 remains a future cutoff decision. No
  feature engineering, source substitution or changes to earlier ingestion.
  Dated update, 21 November 2026: Task 008 completed for independent review;
  implementation commit `3865292416bac061bc98348297aafe87f2de84f1` pushed and
  matched the remote development branch. Local/remote main unchanged; no PR,
  merge or Task 009 work. Measured timing is recorded in the shared CSV.
- **Evidence/references:** [Owner prompt and report](../008-ons-inflation-and-uk-hpi-ingestion.md),
  [source/reconciliation evidence](../../reports/data_audits/008/validation-evidence.json),
  [issue register](../issue-register.md#issues), [timing CSV](../task-execution-log.csv).

## 21 November 2026 - Task 008 review and stable-baseline merge (Task 008.1)

- **Event/trigger:** Owner requested review and merge of completed Task 008
  before further ingestion tasks, conditional on passing tests and no material
  review finding or merge conflict.
- **Initiated by:** Human.
- **Human actions:** Authorised PR creation/reuse and conditional merge into
  main. Prohibited methodological changes, history rewriting, force pushes and
  beginning Tasks 009-013; unresolved issues must remain open.
- **AI actions (Codex):** Verified clean matching local/remote feature heads,
  inspected the expected 13-file diff, reviewed new code/tests and evidence,
  refreshed the complete test suite (117 passed), and replayed source audit
  checks (all comparisons pass; 60 snapshot files unchanged). Initial search
  found no PR. No implementation or ingestion data changed.
- **Outcome/status:** Pre-merge review passed with the existing documented
  limitations. PR creation, checks and actual merge result are recorded in
  the task report after the corresponding actions. No issue is closed by merge.
- **Evidence/references:** [Task 008.1 prompt/report](../008.1-merge-task-008-and-establish-stable-baseline.md),
  [Task 008 evidence](../../reports/data_audits/008/validation-evidence.json),
  [issue register](../issue-register.md#issues), [timing CSV](../task-execution-log.csv).
  Dated update, 21 November 2026: [PR #5](https://github.com/chanmlh026/rental-forecasting/pull/5)
  was created after another duplicate check, then merged at 14:35:12 UTC under
  the owner's conditional authorisation. GitHub reported a clean mergeable PR,
  empty check rollup and no review threads/reviews. Local suite/audit passed;
  hosted CI is not configured. Merge SHA
  `a247a292971594ab7fde507b7fbff64b53d0292f` is the Task 008 implementation
  baseline. Fetch and tree/ancestry checks verified the implementation on remote
  main; local main fast-forwarded to it. No unresolved issue was closed. A
  documentation-only completion receipt records actual results/timing on main
  without changing the merged implementation. No Tasks 009-013 work began.

## 21 November 2026 - UMB-first decision and source investigation (Task 009.3)

- **Event/trigger:** Owner authorised a separate UMB source investigation while
  earnings tasks remain unmerged; later explicitly requested resumption after
  usage-limit interruption, preserving all prior work and excluding the wait gap.
- **Initiated by:** Human.
- **Human decision and rationale:** Prefer the ONS model-based published rate for
  economically active residents aged 16+, because local APS samples of unemployed
  people can be small/unreliable. APS is fallback only if UMB proves unsuitable.
  Preserve deferral of cross-dataset geography harmonisation to preprocessing.
- **AI actions (Codex):** Verified stable main and unchanged earnings branches;
  created a separate research branch, retained safe immutable source evidence,
  audited all 87 current-family annual periods, confidence values/flags and two
  archived M01 editions. Did not modify earnings ingestion or derive new ratios.
- **Significant findings/interventions:** Two cohort code mismatches, historical
  rate gaps and 19 latest matched confidence gaps retained. Earlier M01 history
  starts 1996/97 with a different reference-period structure. API placeholders,
  inconsistent revision labels and incomplete vintage evidence documented.
  Automatic approval review could not execute the formatting/test command at a
  usage limit. On owner resumption, inspected scope/output state, preserved all
  downloads and reran that command and offline checks; no Task 013.1 work found.
- **Outcome/status:** 117 stable-baseline tests passed. Full CSV counts/keys and
  independent official HTML/CSV and archived-confidence comparisons validate.
  UMB is recommended for separately authorised source-level ingestion with limits;
  no APS fallback, production ingestion, harmonisation or features implemented.
  ISS-006 resolved for approved source/measure verification; ISS-003/004/011/012
  updated and remain Open. Separate measured sessions and timing limitations are
  retained in the shared CSV. No PR, merge or Task 013.1 started.
- **Evidence/references:** [Prompt/report](../009.3-umb-unemployment-availability-and-quality-investigation.md),
  [audit evidence](../../reports/data_audits/009.3/validation-evidence.json),
  [archive evidence](../../reports/data_audits/009.3/archive-evidence.json),
  [issues](../issue-register.md), [timing](../task-execution-log.csv).
