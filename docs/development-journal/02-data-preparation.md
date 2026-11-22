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
