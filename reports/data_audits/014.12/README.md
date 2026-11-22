# Task 014.12 — Historical publication evidence consolidation

**PASS WITH CONDITIONS — evidence consolidation only.** All initial-model sources
are represented in the [matrix](publication-evidence-matrix.json). This does not
authorise temporal alignment or establish a complete PIT training history.
Baseline: merged PR #18, main `b66211dae66170ec53f257d06aa86f3f7afec741`.

## Reading the results

The [reconciled count table](source-summary.md) counts **76 evidence units**:
27 A (exact edition dates), 1 B (edition month), 0 C (supported windows),
48 D (unresolved timing), 0 N/A. Units are editions, grouped histories or
explicitly labelled IUMZID4 test periods; they overlap and are not historical
month counts. They must not be interpreted as percentages of PIT coverage.
No supported windows or genuinely inapplicable releases were identified.

An A classification concerns the named edition. It does not date the original
release of every historical observation inside that edition. Dates do not
establish intraday availability. Retrieval dates, effective-rate dates and
source-update timestamps have not been substituted for publication timestamps.
The matrix's separate original-observation timing field prevents that inference.

Numerical vintage is assessed relative to original observation publication.
Identifiable provisional ASHE editions are original provisional vintages, even
where their publication dates remain unresolved. Revised editions are later
vintages. Mixed histories retain some identifiable editions without a complete
first-release archive; no claim of complete reconstruction follows. The matrix
contains no source statistical values or transformed predictors.

## Source scope and main limitations

| Source | Existing historical span and retained evidence | Outstanding limitation / availability assumption |
|---|---|---|
| PIPR | 2015-01–2026-09 in October 2026 edition; March 2024 archive ends 2024-02 | Backcasts do not establish 2015 availability. Archive differs in 81.91–84.08% of compared cells and lacks two reference codes. Full original target vintages and label policy unresolved. |
| CPI/CPIH | Rate series from 1989-01; index series from 1988-01; two editions per series ending September/October 2026 | Exact dates 20 October/18 November 2026; no changes in this overlap pair does not establish unchanged earlier history. Earlier release/vintage history unproven. |
| UKHPI | LA price/index history 1995-01–August/September 2026; releases 21 October/18 November 2026 | Retained pair supports those editions, not every original LA release. National aggregate revision matrices cannot establish original LA values. |
| Bank Rate | 259 effective events, 20 January 1975–5 November 2026 | Effective history is retained; announcement timestamps and intraday eligibility not established. Approved announced-and-effective rule remains; no monthly lag. |
| IUMZID4 | 178 months, January 2012–October 2026; 336 history records; 12 selected test periods | Earliest update is not certified original availability; source timezone unknown. Prior cadence changes preclude applying the current fifth-working-day schedule to all history. Approved earliest-recorded/provisional policy unchanged. |
| ASHE | 37 annual editions, 2002–2026, plus separately labelled 2020 ad hoc publication inspecting 2015–2017 values | Only latest provisional/revised editions have verified ordinary-edition dates; 35 older edition timings unresolved. Ad hoc April 2019 geography is not a substituted production series. |
| Nomis UMB | 87 overlapping annual periods ending December 2004–June 2026; two M01 archive comparators with early 1996/97 history | Primary update metadata does not establish every original release. Archives dated 12 April/16 August 2022 retain later history; both claim final edition. Old windows, geography and definitions need compatibility checks before any use. |
| Population/density/migration | Nine editions through 2022–2025; population histories from 2011, detailed migration from 2012; summary migration latest-year only | Covers date the editions, not all original historical observations. The retained 2022 tables explicitly replace 23 November 2023 tables on 15 July 2024; this resolves edition timing, not original numerical retention. Five advertised prior files remain unacquired. Boundary sheets differ; no polygon validation claimed. |
| MHCLG stock | Table 125, stock 2001–2025; publication 21 May 2026 | Backcasts/revisions and source flags retained; no complete original edition archive. A later landing-page update is not the workbook publication date. |
| MHCLG supply | Table 123, financial years 2012-13–2024-25; publication 20 November 2025 | New-build and net-additions share edition; historical revisions/quality flags remain relevant. Identical URL aliases count once. Table 122 is audit-only. |

Every source has some unresolved historical availability or vintage scope; known
edition dates need no assumed monthly lag. Annual/quarterly carry-forward until
a newer eligible release remains approved. The ordinary monthly lag patterns
remain descriptive, not substitutes for known historical dates.

## Coverage is separate from timing and vintage

The matrix preserves Task 014.10's eight ASHE incomplete retained-input LA-years:
West Northamptonshire (E06000062): 2016, 2019; Cumberland (E06000063): 2016,
2017, 2018, 2020; Westmorland and Furness (E06000064): 2017, 2018.
These are eight **coverage cases**, not eight extra missing publication dates.
They remain within the 24 predecessor-only LA-years (16 with complete retained
edition evidence). No arithmetic means were calculated here. Absence of complete
retained evidence does not prove absence from all official sources.

Five advertised population prior files are separately preserved under
`coverage_gaps`, not counted as five retained editions or five date gaps.
ISS-022 prohibits affected further automated ONS downloads until its access
prerequisite is resolved. No such download, external research or ingestion
reprocessing occurred. Planning counts are excluded and units remain deferred.

## Outstanding owner decisions

These seven decision groups are **Proposed – Not Approved** recommendations,
not new approved methodology. No specific fallback month, maximum age or
historical timestamp is recommended where evidence cannot support one.

| Decision / affected scope | Available evidence; unknown | Implication and existing-evidence options | Trade-off and recommendation — Proposed – Not Approved |
|---|---|---|---|
| T1 — Historical evidence admission (ISS-004); all earlier spans above | D records and incomplete original-release histories; dated later editions are identifiable | Choose which source/period combinations may enter exact versus explicitly approximate evaluation; alternatives are restrict claims to verified edition availability or permit disclosed retrospective approximations | Restriction reduces training history and may differ from production coverage; backdating later information risks leakage. Prefer a documented evidence-qualified sample contract; insufficient evidence to prescribe dates for D records. |
| T2 — Numerical vintage/target truth (ISS-004/013/016); PIPR, HPI and revised histories | Retained dated releases, PIPR differences and HPI revisions; full original LA vintages absent | Choose target-label truth and treatment of later predictor vintages: retain named as-of editions where eligible, or explicitly separate retrospective experiments | Settled labels and later predictors can alter evaluation and leak revisions. Prefer distinct documented label and predictor-vintage policies, reporting limits; no canonical label vintage selected here. Existing IUMZID4 policy is excluded from reconsideration. |
| T3 — Bank Rate cutoff eligibility (ISS-004/014); historical effective events | Effective dates known; announcement time history not established | Choose how date-only events interact with the operational timezone/intraday cutoff; use evidenced events without manufacturing announcement times, or limit exact intraday claims | Day-level assumptions may include an announcement too early; excessive exclusion changes production parity. Prefer explicit cutoff granularity and documented ambiguity handling. No artificial monthly lag or specific intraday fallback recommended. |
| T4 — IUMZID4 timestamp eligibility (ISS-004/005/014); 2012–2026 history | Retained update strings/provisional history and selected tests; unknown original availability/timezone and changing cadence | Preserve approved earliest-recorded value treatment; choose permissible exact/approximate availability claims and handling of unverified update times | Treating updates as original publication risks leakage; excluding all history sacrifices retained information. Prefer explicit uncertified eligibility flags and restricted exact claims; no specific historical fallback date can be recommended. |
| T5 — ASHE temporal and input eligibility (ISS-004/012); 35 undated editions, separately eight input LA-years | Identifiable provisional/revised editions; latest release dates; incomplete retained predecessor inputs | Decide temporal eligibility for older editions separately from whether incomplete input years may enter a later authorised preprocessing sample. Approved complete-input arithmetic-mean scope remains unchanged | Backdating revised medians leaks later information; incomplete ranges cannot supply approved complete-input means. Prefer separate timing/vintage and coverage gates; no substitution or new approximation recommended. |
| T6 — Annual-source history admission (ISS-004/009/011/012); demographic and MHCLG earlier periods | Nine demographic and two housing editions with dates, but later backcasts; five population versions unacquired | Use compatible dated retained editions after release, or permit labelled retrospective histories; older first releases cannot be invented from latest summer/autumn patterns | Carrying known eligible editions is approved; applying future backcasts to earlier cutoffs risks leakage and differs from production. Prefer date-based edition eligibility and explicit unresolved earlier spans; insufficient evidence for a fixed historical annual month. |
| T7 — UMB history/cutoff and common-run completeness (ISS-004/012/014/015); retained rolling periods and operational forecast runs | Primary update metadata, dated M01 comparators, missing cells; no full original Nomis vintages or approved detailed run cutoff/completeness policy | Choose admissible UMB historical vintages and common-run handling for genuinely delayed/missing inputs, respecting the approved adaptive schedule and regional same-quarter baseline | Later revisions can leak; excluding periods changes sample/cohort and production parity. Prefer evidence-qualified retained vintages and explicit common-run rules before implementation. No automatic archive substitution, new donor fallback or fixed lag approved. |

Before temporal alignment/preprocessing, the owner must authorise the historical
evidence/sample and vintage policies (T1/T2), resolve operational timestamp and
completeness handling (T3/T4/T7), and specify treatment of the source-specific
unsupported spans/inputs (T5/T6/T7). New acquisition would additionally require
ISS-022 resolution and separate authorisation. There is no evidence-based
universal fixed fallback month to approve from this consolidation.

## Reproduction and validation

Run from the repository root, without network access or dependencies:

```powershell
python -X utf8 reports/data_audits/014.12/consolidate.py
python -X utf8 reports/data_audits/014.12/validate.py
git diff --check
```

The builder reads only existing tracked reports/documentation, records SHA-256
inputs, and produces the JSON matrix and count table. It opens no datasets or
URLs. The [execution receipt](validation-receipt.json) records checks actually
executed. Production tests are not applicable to this metadata/documentation
change; no independent statistical/source-data validation is claimed.
