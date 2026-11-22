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
