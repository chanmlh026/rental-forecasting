# Project Issue Register

This is the single index of material unresolved project decisions, known data
limitations and implementation dependencies. Detailed measurements stay in the
linked dictionary, audits and evidence reports. Initial review: 8 November 2026,
Task 006.7. Entries below are supported by repository evidence; proposed remedies
and ingestion batches are not approved decisions.

## How to use the register

Before a development task, scan the affected areas and required checkpoints.
For relevant unresolved entries, record one of these outcomes in the task's
normal report; no separate checklist file or automated system is required:

| Outcome | When it applies | Action |
|---|---|---|
| Proceed | No unresolved prerequisite affects correct execution of this task. | Continue within the authorised scope. |
| Proceed with documented limitations | The issue can be investigated or its limitation preserved safely within scope. | Record issue IDs, limitations and follow-up checkpoint; do not silently select a new methodology or substitute data. |
| Blocked - Approval Required | A material decision, unapproved substitution or necessary prerequisite prevents the affected work. | Stop that component; report issue ID, reason, required action/approval and viable alternatives. Continue independent, unaffected work when safe. |

An **Open** issue is not automatically a blocker. **Required Before** identifies
the earliest affected action, not a blanket prohibition on earlier research or
raw-source inspection. A blocked prerequisite cannot be bypassed by labelling it
Deferred. Any approval requirement belongs to the affected decision, not to
unrelated tasks. Task numbers 007-013 below refer to the dictionary's proposed
batches, which still require project-owner authorisation.

Preserve the approved 294-LA cohort, 1-/2-/3-bedroom rent-level target and Option A
12-calendar-month horizon. The existence of this register does not reopen those
decisions or establish acceptance thresholds. Current PIPR hard-failure/warning
rules remain unchanged.

## Issues

Issue descriptions identify a **Decision**, **Evidence gap**, or **Known
limitation** so an unresolved choice is not mistaken for an established defect.
Rows can combine these when they share one required action. Initial entries are
Open because no new resolution or approval was established by creating this
register.

| Issue ID | Issue | Category | Affected Area | Required Before | Status | Required Action / Decision | Evidence Reference |
|---|---|---|---|---|---|---|---|
| ISS-001 | Decision: median earnings measure and population definition | Methodology | ASHE median earnings / earnings growth | Task 009 selected-field contract, before implementing that measure | Open | Obtain project-owner approval for residence-based pay period, working pattern and sex breakdown. Keep employee earnings distinct from household income/GDHI; derive growth only from comparable definitions. | [Dictionary: E1 and GDHI context](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-002 | Evidence gap: ASHE file access and field-level coverage | Data Availability | ASHE source acquisition | Task 009 ASHE parsing/publication | Open | Resolve the recorded ZIP 403 through an accessible official extract; verify chosen fields and cohort/history. A changed variable or proxy needs owner approval; do not infer completeness from a landing page. | [Dictionary: E1 access limitation](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence), [retrieval evidence](../reports/data_audits/006.2/predictor-exploration-evidence.json) |
| ISS-003 | Decision and known limitation: source codes and boundary vintages differ | Geography | LA predictors, historical geography, PIPR archives | First affected LA ingestion/join (proposed 008 onward), before applying mappings | Open | Verify effective-dated code/boundary compatibility, including Barnsley, Sheffield and predecessor authorities. Owner approval required for geography policy/mappings; preserve source codes and distinguish code mismatch from absent observations. Unaffected national sources can proceed when authorised. | [Dictionary: geography findings](data-architecture-and-dictionary.md#quantitative-exploration-and-geography-limitations), [PIPR archive findings](005.1-ons-pipr-workbook-coverage-audit.md#k-historical-vintage-findings) |
| ISS-004 | Known limitation and decision: historical release times/vintages are incomplete | Data Availability | All sources, PIT joins and backtesting | Each source onboarding (007 onward): capture available provenance; before exact PIT claims: verify historical availability | Open | Record observation, availability, retrieval and vintage separately. Retain snapshots and disclose missing history; owner approval required for material lag/vintage assumptions. Research or ingestion with explicit limitations need not wait for full historical reconstruction. | [Dictionary: PIT interpretation](data-architecture-and-dictionary.md#point-in-time-interpretation), [PIPR limitations](006-ons-pipr-ingestion.md#revisions-publication-timing-and-geography-limitations) |
| ISS-005 | Known limitation and decisions: financing measurement regimes and release cadence | Methodology | IUMZID4 and Bank Rate | Task 007 source contract; approve derived rate semantics before feature construction | Open | Verify IUMZID4 backfill, 2019 measurement change and conflicting cadence descriptions against actual releases. Preserve regimes; do not silently splice them. Owner must approve cutoff/monthly Bank Rate summary and any material transformation; raw exports alone do not decide these. | [Dictionary: B1/B2 and BTL history](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-006 | Decision: survey-based versus modelled unemployment | Methodology | APS / UMB unemployment | Task 009 unemployment contract | Open | Obtain owner approval for survey or explicitly labelled model-based rate, denominator/age and rolling-period semantics. Preserve uncertainty and revisions; claimant count is not an interchangeable unemployment rate. | [Dictionary: U1](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-007 | Decision and known limitation: household growth source/concept | Methodology | Household demand predictors | Task 013 source selection, before implementing household measure | Open | Owner must choose estimates versus released projections and relevant scenario. Investigate comparable history; retain admin-based development restrictions and uncertainty. Do not silently combine survey estimates, admin-based counts and projections. | [Dictionary: H1/H2](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-008 | Decision: student-share population universe and residence | Methodology | Student population share | Task 013 student-table selection and subsequent feature definition | Open | Obtain owner approval for ages, numerator, denominator and residence concept. TS068 includes schoolchildren, not only university students; verify Census boundary comparability and dated availability. Do not substitute provider enrolments or invent an annual panel. | [Dictionary: S1](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-009 | Decision: housing-flow and dwelling-stock denominator compatibility | Methodology | Standardised supply predictors; Tables 122/123/125 | Task 011 compatibility contract; approve ratio definition before feature implementation | Open | Verify periods, all-dwelling definitions, boundaries and revisions. Owner must approve start-year/end-year/other denominator timing. Raw inputs can be retained without constructing ratios; ratio availability cannot precede either input's release. | [Dictionary: supply standardisation](data-architecture-and-dictionary.md#dwelling-stock-denominators-and-supply-standardisation) |
| ISS-010 | Evidence gap: accessible LA approved-dwelling-units numerator | Data Availability | Planning units per 1,000 dwellings | Task 012 units-source component, before approving its ingestion | Open | Establish a suitable local units-granted source, geography and rights. PS2 application decisions cannot substitute for units; England rolling totals cannot establish an LA series. Owner approval required for any alternative. Independent authorised PS1/PS2 work can continue. | [Dictionary: planning units limitation](data-architecture-and-dictionary.md#dwelling-stock-denominators-and-supply-standardisation), [inspected extracts](../reports/data_audits/006.2/predictor-exploration-evidence.json) |
| ISS-011 | Known limitation: source quality flags, imputation and notes need preservation | Data Quality | Survey uncertainty; annual housing source flags/styles | Source-specific contracts (009/011 in particular), before derived outputs lose these signals | Open | Retain uncertainty, suppression and publisher-imputation indicators; investigate Table 123 style-dependent flags and inconsistent note-year labels. Numeric cells are not necessarily unadjusted observations. Do not turn flags into automatic exclusions or invent thresholds. | [Dictionary: source quality and notes](data-architecture-and-dictionary.md#quantitative-exploration-and-geography-limitations), [source characteristics](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-012 | Evidence gap: selected predictor histories and cohort completeness unmeasured | Data Quality | ASHE, unemployment, households, Census, HPI and older migration components | Respective onboarding tasks 008-013, before claiming full historical/cohort coverage | Open | Measure selected fields after resolving relevant definitions and ISS-003 geography. Keep raw missing/suppressed values and distinguish samples from full panels. Missingness itself is not a rejection decision; owner approval required for material preprocessing/substitution policies. | [Dictionary: measured coverage limits](data-architecture-and-dictionary.md#quantitative-exploration-and-geography-limitations), [remaining research](data-architecture-and-dictionary.md#decisions-and-research-still-required) |
| ISS-013 | Decision: HPI measure/base and release-specific revision treatment | Methodology | Average house price / index / annual growth | Task 008 HPI contract before standardising selected series | Open | Confirm all-property price versus index, series base, revision policy and available releases. Owner approval required for feature-definition or material vintage-policy choices. Do not infer a complete fixed-boundary panel from national series history. | [Dictionary: M1](data-architecture-and-dictionary.md#underlying-source-characteristics-and-evidence) |
| ISS-014 | Decision: operational forecast timezone and cutoff schedule | Methodology | Forecast generation and PIT feature assembly | Before implementing operational forecast/cutoff rules; not a prerequisite for recording source retrievals | Open | Obtain owner approval for issue/cutoff schedule and timezone. Retain precise timezone-aware cutoffs and distinguish them from origin month; do not infer availability at midnight from an edition date. | [Dictionary: target specification](data-architecture-and-dictionary.md#4-target-variable-specification), [time fields](data-architecture-and-dictionary.md#required-time-fields) |
| ISS-015 | Decision: common-origin handling of delayed/missing target series | Methodology | Forecast cohort completeness and cross-area comparison | Before operational origin selection and comparable model evaluation | Open | Retain the approved cohort and no target imputation. Obtain owner approval for the common-origin completeness rule and missing-series behavior; do not silently choose thresholds or mix per-series horizons. Existing ingestion gates remain unchanged. | [Dictionary: origin and completeness rules](data-architecture-and-dictionary.md#4-target-variable-specification), [current ingestion validation](006-ons-pipr-ingestion.md#validation-behavior) |
| ISS-016 | Decision: canonical target-label vintage for evaluation | Methodology | Training-label eligibility and evaluation truth | Before label construction / backtesting evaluation policy | Open | Owner must choose first-released versus settled/revised evaluation truth and document its distinction from information available at training cutoff. Preserve versions; current retrospective values cannot establish historical availability. | [Dictionary: historical forecast reconstruction](data-architecture-and-dictionary.md#4-target-variable-specification), [PIPR vintage differences](005.1-ons-pipr-workbook-coverage-audit.md#k-historical-vintage-findings) |
| ISS-017 | Evidence gap and approval dependency: source rights and ingestion scope | Data Availability | Proposed Tasks 007-013; third-party permissions data | Before each production source onboarding or redistribution | Open | Obtain owner authorisation for the relevant proposed batch and confirm source-specific licence/access notices. Government aggregate availability does not establish microdata rights. No task approval is inferred from the roadmap or successful download. | [Dictionary: proposed batches](data-architecture-and-dictionary.md#7-proposed-production-ingestion-batches), [access/licences](data-architecture-and-dictionary.md#access-licences-and-reproducible-evidence) |
| ISS-018 | Known limitation: restored Task 006.1 instructions stop at Section 4 | Other | Historical task documentation | Before representing the archive as the complete original specification | Open | Recover the remainder if available; otherwise preserve and disclose the truncation. No historical execution times can be inferred from prompt restoration or Git dates. This does not reopen the implemented reliability work or block unrelated ingestion. | [Restored prompt](006.1-harden-ons-pipr-ingestion-reliability-and-release-validation.md), [documented limitation](data-architecture-and-dictionary.md#decisions-and-research-still-required) |

## Lifecycle and decision record

- **Open:** identified but unresolved.
- **In Progress:** investigation or resolution is underway within an authorised task.
- **Resolved:** required action and validation are complete, including owner
  approval wherever required. Record the outcome, evidence and approval reference.
- **Deferred:** intentionally postponed, with an explicit future checkpoint in
  Required Before and the reason in Required Action / Decision. Never use
  deferral to bypass a current prerequisite.

Keep IDs stable and never delete or reuse resolved entries. Update the existing
row rather than creating overlapping issues. On resolution, add a short dated
resolution/approval note in the action cell (or a short note below this table if
needed) and link the detailed evidence. A proposal or attempted implementation
alone is not resolution. Routine engineering actions may be resolved within
authorised scope; material methodology, architecture, feature-definition and
data-substitution decisions require project-owner approval.

## Task 006.7 dependency review

**Proceed with documented limitations.** The register indexes ISS-001-ISS-018;
none requires a methodological choice to create this documentation. No issue
has been resolved or deferred by this task. In particular, potential Task 007
dependencies ISS-004, ISS-005 and ISS-017 require source-contract review and
owner task authorisation, not prior resolution of unrelated LA/household issues.
This task does not start Task 007 or approve any ingestion batch.
