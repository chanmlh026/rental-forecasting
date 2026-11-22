# Data preparation development journal

This journal records significant events in Phase 2 data preparation. Decision
approval and documentation do not imply preprocessing implementation. Detailed
methodology/evidence remain in the dictionary; original instructions, outstanding
dependencies and measured timing remain in their existing shared records.

## 22 November 2026 - Decision A and Phase 2 journal initialisation (Task 014.1)

- **Event/trigger:** Owner approved the Barnsley/Sheffield historical-boundary
  approximation and requested a documentation-only record and Phase 2 journal;
  resumed the same task after initial-review and usage-limit interruptions.
- **Initiated by:** Human.
- **Human actions:** Approved the two-authority policy, preserving source values,
  codes and vintages; supplied the rationale and candidate quantitative evidence.
  Required verification/qualifications, ISS-003 Open and no mapping implementation
  or automatic merge.
- **AI actions (Codex):** Preserved the existing branch, both archived prompts
  and single timing row; appended resumption instructions. Reviewed official
  boundary documents and independently inspected retained, checksum-matching
  ONS/MHCLG workbooks read-only. Recorded policy, calculations, limitations and
  future validation requirements in the existing dictionary decision convention.
  Created this Phase 2 journal without changing the Phase 1 journal.
- **Decision and stated rationale:** Owner accepts a small potential aggregate
  effect relative to authority area, stock and population to retain representative
  history and avoid unnecessary adjustments/engineering complexity. This is an
  accepted approximation, not demonstrated zero impact. Prior ChatGPT analytical
  contributions and the provenance of earlier approximate denominators are not
  independently established by the available prompts; owner judgement and
  Codex verification/documentation are attributed separately.
- **Outcome/status:** Methodology approved; implementation and validation pending
  Task 014. Exact retained population/stock figures verified; official wording
  conflicts on whether 284 dwellings is total or additional remain qualified for
  owner review. No realised transfer impact inferred. ISS-003 stays Open; Issues
  B-E remain unreviewed/unapproved in Phase 2. No processing, mapping, source
  acquisition, data changes or modelling; documentation submitted for owner review.
- **Evidence/references:** [Decision A, complete evidence and future requirements](../data-architecture-and-dictionary.md#decision-a-barnsley-and-sheffield-historical-boundary-harmonisation),
  [original/revised/resumption instructions](../014.1-barnsley-sheffield-geography-decision-a.md),
  [ISS-003](../issue-register.md), [shared execution timing](../task-execution-log.csv).

## 22 November 2026 - Historical ASHE availability and B1 confirmation (Task 014.2)

- **Event/trigger:** Owner requested research into earnings before 11 authorities'
  creation, preserving the annual gross median All residence definition and
  prohibiting harmonisation or source selection.
- **Initiated by:** Human.
- **Human actions:** Supplied test authorities and source/coverage requirements;
  identified merged PR #12 and confirmed prior B1 approval, its four code changes,
  rationale and deferred implementation. Earlier ChatGPT discussion is not available;
  the owner's confirmation establishes the recorded approval.
- **AI actions (Codex):** Read official Nomis metadata and focused observations;
  inspected the residence historical extract and retained ONS editions offline.
  Current-main review through the GitHub connector exposed the stale checkout
  and ISS-022 after one ONS ZIP acquisition. Stopped further automated ONS downloads.
  Preserved original dirty Task 009.5 work and moved only new Task 014.2 work
  to an isolated branch at merged PR #12, using the clean checkout's local commit.
  Recorded B1 in the existing dictionary and source findings in one audit report.
- **Decision and stated rationale:** B1 retains unadjusted history for the four
  minor 2013 changes because the owner considers affected property/elector counts
  very small. No new ASHE source, vintage or reconstruction treatment selected.
- **Outcome/status:** Research delivered with explicit geography/evidence gaps;
  12 special-extract 2015-2017 pay/CV pairs verified on April 2019 boundaries.
  Nomis family-specific missingness and Dorset's old-county values prevent a
  blanket comparable-history conclusion. Decisions A/B1 preserved, implementation
  deferred; ISS-003 and related issues remain Open. Owner review pending.
- **Evidence/references:** [Task instructions and owner confirmation](../014.2-investigate-historical-ashe-current-boundaries.md),
  [research and reproducible coverage](../../reports/data_audits/014.2/README.md),
  [B1 decision record](../data-architecture-and-dictionary.md#decision-b1-minor-2013-boundary-changes),
  [issue register](../issue-register.md), [shared timing](../task-execution-log.csv).

### Submission update - 22 November 2026 (Task 014.2)

- **Event/trigger and human action:** Owner requested pushing the completed
  research branch and creating a PR against main for independent review.
- **AI actions (Codex):** Verified committed scope, 30 retained response hashes,
  documentation, safe evidence headers, credential patterns and Git integrity;
  preserved A/B1, ISS-003 Open and unrelated dirty work. No source acquisition.
- **Outcome/status:** Submission authorised; main's Task 012 advance introduces
  two shared-document merge-preview conflicts, recorded for independent review.
  No merge or harmonisation authorised; final PR receipt is in the
  [Task 014.2 archive](../014.2-investigate-historical-ashe-current-boundaries.md).

- **Dated outcome update, 22 November 2026:** [PR #14](https://github.com/chanmlh026/rental-forecasting/pull/14)
  created open/non-draft against main for independent review. Research and
  submission-check commits pushed; final timing/PR receipt recorded in the same
  task archive and CSV row. Dictionary/register merge conflicts remain disclosed;
  no merge, production change, acquisition or methodological implementation.

### Conflict-resolution update - 22 November 2026 (Task 014.2)

- **Event/trigger and human action:** Owner authorised the latest-main update
  and reconciliation of PR #14's two documentation conflicts, retaining both
  tasks and all approved decisions; PR merge remains unauthorised.
- **AI actions (Codex):** Combined both dictionary sections and dated ISS-003
  additions; verified all 22 issue records, existing timing rows and original
  research evidence. Preservation checks caught and corrected adjacent ISS-004
  omission before commit. All 30 research response hashes and final doc/Git
  checks passed. Task 012 implementation/config/tests/evidence match main.
- **Outcome/status:** Conflicts reconciled locally; ISS-003 Open, A/B1 unchanged;
  source acquisition, production edits and mapping absent. Remote confirmation
  and timing receipt are recorded in the [same task archive](../014.2-investigate-historical-ashe-current-boundaries.md).

- **Dated outcome update, 22 November 2026:** Main update and both doc conflicts
  committed/pushed as `1859d94`; GitHub confirms PR #14 mergeable, open and
  unmerged. PR description updated to retain evidence gaps/access incident and
  record the resolution. ISS-003 Open, Decisions A/B1 unchanged; no implementation
  or acquisition. Final measured intervals retained in the same execution row.

## 22 November 2026 - Predecessor median earnings range research (Task 014.3)

- **Event/trigger:** Owner requested numerical historical earnings-range evidence
  for the 11 reorganised authorities, retaining the approved ASHE definition and
  forbidding production reconstruction, methodology decisions and new ONS downloads.
- **Initiated by:** Human.
- **Human actions:** Specified yearly min/max/GBP/percentage spans, numeric and
  missing/suppressed counts, dated predecessor history, uncertainty limitations,
  official comparator assessment and independent review before merge.
- **AI actions (Codex):** Created a separate branch from merged Task 014.2 main;
  checked statutory membership and Somerset's intermediate merger. Read retained
  ingestion and verified raw pay/CV cells offline; preserved all editions and
  supplied complete/partial/unassessable ranges plus comparator qualifications.
  Independently reconciled every range to source observations and confirmed
  existing processed snapshot files unchanged. No statistical source acquisition.
- **Outcome/status:** Across 65 pre-reorganisation authority-years, 37 have a
  complete retained edition and 28 do not. Complete ranges differ substantially;
  partial narrow ranges cannot establish similar full-area earnings. Official
  comparator overlaps offer qualified future research opportunities; no candidate
  combined median or approximation accuracy calculated. Research supports only
  selective further investigation, with owner decision/independent review pending.
  Decisions A/B1 preserved, ISS-003 and related source limitations remain Open;
  no production implementation or geography harmonisation.
- **Evidence/references:** [Research, roster and numerical evidence](../../reports/data_audits/014.3/README.md),
  [original task prompt and handoff](../014.3-ashe-predecessor-median-earnings-ranges.md),
  [shared timing](../task-execution-log.csv), [ISS-003](../issue-register.md).

- **Dated review update, 22 November 2026:** Research commit `cce7f2c` pushed;
  [PR #15](https://github.com/chanmlh026/rental-forecasting/pull/15) opened for
  independent review against merged Task 014.2 main and confirmed mergeable,
  open and unmerged. Final timing and review receipt recorded in the same task
  archive/CSV row. No model or methodology approval inferred from submission.

### Cross-dataset official historical geography investigation - 22 November 2026 (Task 014.4)

- **Event/trigger:** Owner requested official historical geography research for the
  exact 11 reorganised authorities across current LA predictors and PIPR targets.
- **Initiated by:** Human.
- **Human actions:** Specified research-only scope, source priority, five evidence
  classifications, preservation of A/B1 and ISS-003 Open, and the ISS-022 acquisition hold.
- **AI actions (Codex):** Checked current main and unmerged Task 014.3; used an isolated
  main-based worktree to preserve unrelated dirty work and PR #15. Inspected retained
  source parquets, manifests and geography notes; consulted official documentation;
  retained three focused public Nomis responses. Created an offline coverage audit
  and independent source-period checks; no automated ONS download or reconstruction.
- **Outcome/status:** 11 authorities, 27 audited fields and 2015?2026 assessed. Official
  population/migration backcasts identified; HPI/PIPR historical footprint verification,
  non-additive series and planning units remain review priorities. No methodology
  selected; A/B1 and all issue statuses preserved. Independent review pending.
- **Evidence/references:** [Prompt](../014.4-cross-dataset-historical-geography-and-official-sources.md),
  [findings and validation](../../reports/data_audits/014.4/README.md),
  [dictionary](../data-architecture-and-dictionary.md#task-0144-cross-dataset-historical-geography-research---22-november-2026),
  [register](../issue-register.md), [measured timing](../task-execution-log.csv).

- **Submission update, 22 November 2026:** [PR #16](https://github.com/chanmlh026/rental-forecasting/pull/16)
  is open/non-draft/mergeable and unmerged; independent review pending. The same
  task archive and execution row retain measured cutoff and submission evidence.

### Research integration and approved geography policy - 22 November 2026 (Task 014.5)

- **Event/trigger:** Owner authorised merging the unchanged reviewed PR #15,
  updating PR #16 against main and leaving PR #16 open for final independent review.
- **Initiated by:** Human.
- **Human actions:** Approved the overarching policy: ONS PIPR is the geographical
  reference for the approved 294 Local Authorities; all historical LA predictors
  must use the same reference boundaries regardless of observation year. Official
  retrospective estimates are preferred; compatible additive counts may be
  reconstructed when necessary subject to verification; non-additive approximations
  need separate owner approval. Reaffirmed Issue E: join HPI by verified LA code,
  retain original source names and use reference names in modelling outputs.
- **AI actions (Codex):** Verified exact reviewed heads, reran PR #15's offline
  independent range validator and merged #15 with an expected-head guard. Fetched
  updated main and reconciled three append conflicts in the dictionary, this
  journal and timing CSV, preserving both tasks in order. Recorded the approved
  policy separately from implementation and source verification.
- **Decision/status:** The policy approval does not verify historical PIPR
  boundary compatibility or approve a particular source/vintage/transformation.
  Task 014.4 classifications and original research conclusions remain unchanged.
  A/B1 and Issue E preserved; ISS-003 stays Open, ISS-004/022 restrictions retained.
  No acquisition, production changes or approximation approval; PR #16 must remain open.
- **Evidence/references:** [Task 014.5 and integration receipt](../014.5-integrate-geography-research-and-approved-methodology.md),
  [approved policy](../data-architecture-and-dictionary.md#approved-overarching-geographical-policy-and-issue-e---22-november-2026),
  [Task 014.3 research](../../reports/data_audits/014.3/README.md),
  [Task 014.4 research](../../reports/data_audits/014.4/README.md),
  [issues](../issue-register.md), [timing](../task-execution-log.csv).

- **Integration outcome update:** PR #15 merged at `8d97df3`; PR #16 updated
  at `079bb3e` and confirmed open/mergeable/unmerged. Both offline validators
  and preservation checks pass. Final receipt/timing in the same Task 014.5
  archive and CSV; independent review of PR #16 remains pending.


### Planning authority geography and source allocation research - 22 November 2026 (Task 014.6)

- **Event/trigger:** Owner requested a 294-LA planning geography assessment,
  2015 Q1-2026 Q2 classifications and investigation of Task 012's 271 code gaps.
- **Initiated by:** Human.
- **Human actions:** Required research-only work and retention of all policy,
  source definitions and Open issues. Confirmed no local LPA/LAD lookup exists;
  authorised completing as much as possible with retained records and permitted
  official documentation while preserving ISS-022 and reporting unresolved cases.
- **AI actions (Codex):** Preserved the dirty checkout and PR #16; created a
  dedicated dependent branch. Inspected existing planning snapshots, official
  metadata and authority documents. Classified 54096 measure-level records;
  retained original reporting identities and all-field availability. Independently
  reconciled original CSV tokens and input hashes. No download or count reconstruction.
- **Outcome/status:** Documentary evidence identifies 49 non-coterminous cases,
  with 245 current relationships unresolved. Per measure: 41 additive opportunities,
  420 allocation cases and 13063 Unverified LA-quarters. All 271 code gaps have
  complete numeric predecessor candidates, without confirmed whole-LA coverage.
  Coterminous total/historical geography certification remains an evidence gap;
  no Direct observations certified from code matching. A/B1, Issue E and the
  overarching PIPR policy preserved; ISS-003/004/010/017/022 remain Open.
- **Evidence/references:** [Task prompt and owner continuation](../014.6-verify-planning-authority-geography-and-la-allocation.md),
  [research and independent source checks](../../reports/data_audits/014.6/README.md),
  [dictionary](../data-architecture-and-dictionary.md#task-0146-planning-authority-geography-research---22-november-2026),
  [register](../issue-register.md), [shared timing](../task-execution-log.csv).

- **Submission update:** [PR #17](https://github.com/chanmlh026/rental-forecasting/pull/17)
  is open/non-draft/mergeable/unmerged against PR #16's research branch.
  Bounded investigation submitted; full geography certification remains incomplete.
  Measured timing and validation receipt are in the same Task 014.6 archive/CSV row.


### Approved planning-variable decisions and PR finalisation - 22 November 2026 (Task 014.7)

- **Event/trigger:** Owner requested documentation-only finalisation of Task 014.6
  and PR #17, with no further investigation, acquisition or implementation.
- **Initiated by:** Human.
- **Human actions:** Explicitly approved excluding residential planning application
  counts because they measure activity rather than homes permitted; deferring
  all-residential dwelling units granted permission until a future phase because
  compatible 294-LA history and verified intended-use rights are not established;
  and retaining new-build completions/net additional dwellings in scope unchanged.
  Prohibited further initial-phase planning geography/units-source investigation
  and application-count or affordable-only substitution; required data preservation.
- **AI actions (Codex):** Verified PR #15 merged, #16 open against main and #17
  open against #16's branch; applied the decisions only to PR #17's branch.
  Updated current dictionary statuses and dated decision records; moved ISS-010/017
  to Deferred with future reauthorisation checkpoints and unresolved evidence intact.
  Preserved Task 014.6 findings and distinguished completed bounded research from
  incomplete geographical certification. Updated PR review/dependency descriptions.
- **Decision/outcome:** Planning scope decisions approved; no particular source,
  approximation, rights or geography compatibility approved. No further LPA/LAD
  work for excluded predictors in initial modelling. Geography A/B1, Issue E and
  PIPR policy preserved; ISS-003/004/022 remain Open. All research/data unchanged;
  independent review of documentation remains required; no PR merge.
- **Evidence/references:** [Verbatim prompt and receipt](../014.7-finalise-planning-variable-decisions-and-pr17-documentation.md),
  [planning decisions](../data-architecture-and-dictionary.md#task-0147-approved-planning-variable-decisions---22-november-2026),
  [retained Task 014.6 audit](../../reports/data_audits/014.6/README.md),
  [issue register](../issue-register.md), [shared timing](../task-execution-log.csv).

- **Finalisation update:** Documentation/preservation checks passed, including
  140 unchanged prior audit/archive blobs. PR #17 description requests independent
  review; PR #16 description cross-references the later scope decisions. Review
  order is #16, then retarget/recheck #17 against main under separate merge
  authorisation. No PR merged; measured receipt is in the Task 014.7 archive/CSV.


### Approved methodological baseline consolidation - 22 November 2026 (Task 014.10)

- **Event/trigger:** Owner requested documentation-only consolidation after merged
  PR #16/#17, establishing the baseline for future temporal alignment/dataset construction.
- **Initiated by:** Human.
- **Human actions:** Confirmed PIPR reference/294 LAs, modern statistical-code
  compatibility assumption with contrary-evidence exceptions and existing A/B1/
  Issue E; approved variable-specific ASHE mean, baseline regional UMB imputation,
  official-first population/density/migration and compatible stock/supply count
  treatment. Retained planning exclusions/deferral and prohibited implementation.
  Explicitly replaced Option A with Option B and approved monthly adaptive
  execution/latest-eligible information principles, preserving timing/vintage limits
  and excluding predictor-age features. No fallback months or maximum ages selected.
- **Decision and stated rationale:** Option B targets the same calendar month in
  the next year from execution so publication delays do not shift the target.
  Code compatibility is a modelling assumption, not proof of historical geography;
  predecessor ASHE means are flagged estimates, not exact combined medians.
- **AI actions (Codex):** Based a focused branch on merged main `85e60e4`;
  updated current dictionary target/alignment descriptions and cross-references,
  README/AGENTS horizon pointers, PIPR ingestion-guide context, a dated historical
  note on the prior audit, issue actions/checkpoints and this journal. Preserved
  earlier dated decisions/research and original audit figures as history. Checked the retained
  Task 014.3 evidence for the approved 24-year scope: eight lack a complete
  retained edition, recorded as an input-validation limitation without new source
  investigation or estimates. No code/configuration/data/test changes.
- **Outcome/status:** Approved policy documented; preprocessing/validation remains
  future work. Option A's original approval is retained under an explicit
  superseded heading and in historical archives/journals. Monthly reporting lags
  are expectations, not fixed selection rules. Specific operating/PIT assumptions
  remain unresolved. ISS-003/004/009/011/012/013/014/015/016/022 Open;
  planning ISS-010/017 Deferred unchanged. No source or model outputs changed.
- **Evidence/references:** [Verbatim prompt and receipt](../014.10-consolidate-approved-methodology-and-forecasting-decisions.md),
  [current baseline](../data-architecture-and-dictionary.md#task-01410-approved-methodological-baseline---22-november-2026),
  [issue register](../issue-register.md), [shared timing](../task-execution-log.csv).

- **Submission update:** [PR #18](https://github.com/chanmlh026/rental-forecasting/pull/18)
  is open/non-draft/mergeable/unmerged against merged main `85e60e4`. Requested
  documentation checks pass; eight existing ASHE completeness gaps and detailed
  operating/PIT choices remain explicit. Final receipt and measured cutoff are
  retained in Task 014.10 archive/CSV; independent review pending, no implementation.

### 22 November 2026 ? Task 014.12: historical publication evidence consolidation

- **Event/trigger:** Owner requested existing-evidence consolidation after merged
  PR #18/Task 014.10, without source acquisition, reprocessing or new methods.
- **Initiated by:** Human. **Human action:** Supplied scope, classification and
  review requirements. **AI action:** Codex consolidated retained audit metadata
  into a reproducible matrix and source summary, separating edition timing,
  numerical vintages and coverage; documented seven outstanding decision groups.
- **Decision/rationale:** Existing owner approvals preserved. Recommendations are
  Proposed ? Not Approved. Retained 2022 population notes distinguish July 2024
  replacement tables from November 2023 originals; no new research was needed.
- **Outcome/status:** PASS WITH CONDITIONS for consolidation; 27 exact edition
  dates, one verified month, 48 unresolved timing evidence units. Eight ASHE input
  cases and five unacquired population versions remain separate coverage gaps.
  Historical PIT sample/vintage/cutoff decisions remain outstanding. Review PR
  requested; no merge authorised. No production or dataset changes.
- **Evidence:** [Audit and decision register](../../reports/data_audits/014.12/README.md),
  [validation receipt](../../reports/data_audits/014.12/validation-receipt.json),
  [prompt archive](../014.12-consolidate-historical-publication-evidence-and-temporal-gaps.md),
  shared execution CSV. ISS-003/004/022 preserved; no issue closed.

- **Same-session submission update:** [PR #19](https://github.com/chanmlh026/rental-forecasting/pull/19)
  opened for independent review, unmerged. Offline artifact checks executed and
  passed; no independent source-data validation claimed. Final measured timing
  cutoff and reporting exclusions are recorded in the shared CSV/task receipt.


### 22 November 2026 - Task 014.13: owner temporal and ASHE policy approval

- **Event/trigger:** After merged PR #19 (Task 014.12), owner supplied T1-T7
  decisions for documentation only. Available attachment ends mid-list in
  Section 7; remaining text requested, not invented or represented as received.
- **Initiated by:** Human. **Human actions:** Approved original-first/earliest-
  retained/flagged-retrospective hierarchy and PIPR primary target preference;
  monthly post-MPC Bank Rate, cadence-aware IUMZID4/annual ASHE and annual-source
  eligibility, cutoff-safe UMB and delayed monthly release carry-forward policy.
  Explicitly superseded complete-input ASHE restriction with available-numeric
  predecessor estimates, including the eight incomplete cases in the same scope.
- **AI actions:** Codex verified merged PR #19/current main, preserved dirty outer
  checkout via isolated documentation worktree, archived supplied prompt verbatim,
  updated canonical Section 6 and current ASHE guidance, annotated superseded
  restrictions and updated existing issue dependencies without closing evidence gaps.
- **Decision and stated rationale:** Reproduce historical production conditions as
  closely as available evidence permits. Distinguish genuinely historical values
  from retrospective proxies; no silent backdating. Partial ASHE values are
  estimates, not exact combined-area medians; source missing markers remain.
- **Outcome/status:** Policies documented for future implementation; no preprocessing,
  model features, training, scheduling, geography transforms or source acquisition.
  Remaining operational exceptions, essential-input/staleness rules and evidence
  validation stay explicit. Decisions A/B1, Issue E, Option B and other baseline
  geography/variable approvals preserved. ISS-003/004/022 remain Open.
- **Evidence:** [Owner prompt](../014.13-consolidate-temporal-alignment-and-ashe-decisions.md),
  [canonical decisions](../data-architecture-and-dictionary.md#task-01413-approved-temporal-alignment-and-ashe-decisions---22-november-2026),
  [issue register](../issue-register.md), shared task execution CSV. Original
  Task 014.12 matrix, reports and research evidence remain unchanged.

- **Session stop:** Complete supplied T1-T7 documentation and offline preservation
  checks passed. Full Task 014.13 remains In Progress pending the missing Section 7
  continuation; no unprovided delivery requirements inferred. Changes retained on
  isolated local branch; no push/PR/merge. Measured session and exclusions recorded
  in shared CSV and task archive; [validation receipt](../../reports/data_audits/014.13/consolidation-validation.json).

- **Same-date resumption:** Owner supplied the Section 7-9 continuation and
  explicitly instructed resumption from `78461dd`, focused PR creation after
  validation and no automatic merge. The initial local attachment's truncation
  is now resolved as a prompt-availability limitation; prior session facts and
  timing retained. Codex appended the continuation verbatim, confirmed latest
  main still `09c92ec` (merged PR #19), reviewed existing changes against all eight
  acceptance criteria and added a subsequent-approval note to the Task 014.12
  summary without altering its matrix, counts or original research evidence.

- **Final submission update:** Full Task 014.13 acceptance checks passed; prompt
  continuation resolved the initial local availability limitation. [PR #20](https://github.com/chanmlh026/rental-forecasting/pull/20)
  opened/non-draft for independent review, not merged. Original research matrix,
  code and datasets unchanged; all prior decisions retained except explicitly
  superseded complete-input ASHE policy. Remaining operational/evidence work is
  recorded without invented decisions. Completed row sums two measured sessions
  and excludes the gap/final reporting cutoff; see shared CSV and task receipt.
