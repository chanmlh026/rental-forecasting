# Task 011: MHCLG housing supply and dwelling stock

**PASS WITH CONDITIONS for source-level ingestion.** No housing ratios,
denominator timing, geographic harmonisation or modelling is implemented.
See [the task archive/report](../../../docs/011-mhclg-housing-supply-and-dwelling-stock-ingestion.md).

## Reproduce

Run from the clean repository root:

```powershell
uv run python -m ingestion.mhclg_housing --snapshot-id 2026-11-22-task011
uv run python reports/data_audits/011/validate_ingestion.py
uv run pytest
```

The pinned source inventory is `configs/mhclg_housing_sources.json`.
Same-argument production reruns verify/reuse saved requests without acquisition;
the audit injects a downloader that raises if used. A new snapshot downloads only
missing official requests and requires bytes matching the inspected inventory.
A changed publication/file requires explicit inventory review and a new snapshot,
not overwriting saved raw or validated data. Current raw/processed datasets remain
ignored; a fresh Git clone needs the retained official files to replay live audits.

## Sources and coverage

| Source | Periods | Structured observations | Source area coverage |
|---|---|---:|---|
| Table 122, LT_122 | Financial years 2001-02 to 2024-25 | 10104 | 421 rows, including 417 GSS codes and uncoded published aggregates |
| Table 123, 13 year sheets | Financial years 2012-13 to 2024-25 | 70546 | 377 distinct GSS codes across history; native rows vary by sheet |
| Table 125, rounded and unrounded | 31 March 2001 through 2025 | 21350 | 427 coded areas per sheet, including predecessors/aggregates |

There are 102000 selected source cells: 98366 numeric and 3634 source markers.
Table 123 retains all published components and PDR subcomponents, including
`New build` and Census adjustments. Rounded stock is separately identified for
audit; only the original unrounded sheet is labelled as the future denominator
candidate, without choosing a denominator date. Units remain dwellings.

Latest exact cohort matches are 292. Historical numeric target-code coverage for
Tables 122/125 ranges from 272 to 292; Table 123 new build starts at 277 in
2012-13 and reaches 292. All per-period counts reproduce Task 006.2. `[x]` markers,
negative net additions, earlier codes/names and uncoded aggregate rows are retained.
No name-based mapping, imputation or quality/outlier cutoff is applied.

The approved publication pages advertise different asset URLs for Tables 122/123;
each pair is byte-identical. All five attachment bundles are preserved, with two
explicit alias identities. Only three distinct workbooks are parsed, avoiding
duplicate observations. Flow covers state 20 November 2025; stock cover states
21 May 2026. The stock landing page's 25 June 2026 update is not substituted for
the Table 125 publication date. A complete historic vintage archive is not claimed.

## Publisher quality

The ODS parser preserves exact stored XML numbers, displayed text, formulas,
current/former/DCLG identifiers, source row/column, inherited styles/property
maps, source style XML, notes and original raw workbooks. Repeated empty grids
are handled sparsely; explicit ODS spaces/tabs/line breaks remain intact.

Table 123 explicitly identifies red-filled cells as imputed and uses `[note 1]`
for affected authority/year rows. There are 451 red-fill cells and 584 cells with
imputation row notes; their union contains 584 cells. These signals are retained
separately. The combined imputation flag is True when explicitly indicated and
null otherwise; absence of a signal does not certify an unimputed value.
Table 122 narrative historical imputation lists remain linked through period
notes; they are not applied indiscriminately to every authority in that year.
The publisher's warning about using imputed authority values is retained.

Known note inconsistencies remain explicit: Table 123's provisional/revision note
years lag later sheets (7216/7544 flagged observations respectively). Table 125's
unrounded sheet repeats rounded wording (10675 flagged observations); source
unrounded numeric literals remain unmodified. Two older component headers say
only `Of which under PDR`; they are stored under a literal auxiliary label without
assigning an unverified subtype. Census-related adjustments/revisions remain
source evidence; stock changes are not forced to equal net additions.

## Independent checks and cross-publication precision

The audit independently parses ODS XML, values, logical repeated cells and style
inheritance without reusing production parsing/field/style helpers. It reconciles
all 102000 cells, 589 note cells and 276 coverage rows, plus original periods,
units, flags, identifiers and request/checksum provenance. All seven validated/
processed tables agree. Offline rerun preserved all 423 data files, including
388 pre-task files and nine immutable raw request bundles.

An initial cross-table equality assertion stopped the audit. Read-only diagnosis
confirmed a comparison-design error: Table 122 stores integer totals while Table
123 explicitly retains unrounded fractional values. Of 4530 comparable numeric
pairs, 2925 differ in stored value, with observed maximum absolute difference 0.5;
98 displayed values differ too. The latter facts do not establish a universal
rounding rule or tolerance. The corrected assessment reports all differences and
preserves both sources. No rounding, tolerance, substitution, preferred value or
stock-difference equality is used to obtain a PASS. Mandatory exact reconciliation
against each table's own original XML still fails on any actual ingestion mismatch.
Future feature/source compatibility decisions remain under ISS-009/011.

302 full regression tests passed (including 36 focused MHCLG cases), and two
additional focused audit regression cases passed after the comparison correction.
The production code, configuration and input data were unchanged by that correction;
the full suite was not needlessly repeated. Source/history/staged secret scans,
HTTP metadata, lock, formatting and Git integrity checks are recorded separately.

## Evidence

- `source-investigation.json`: preliminary official attachment/schema/notes inventory.
- `inspection-spacing-correction.json`: preserved preliminary gates, verified ODS
  spacing corrections and standalone PDR label evidence; exact final schemas are
  pinned in configuration. No source hashes or values were changed.
- `validation-blocker.json`: historical stopped equality-gate receipt and read-only
  diagnosis; points to a checksum-preserved full failure artifact under ignored
  `data/validation_reports/`. It is retained as history, not a current blocker.
- `validation-evidence.json`: successful per-source validation, compatibility
  findings, offline preservation, tests and validated code/configuration hashes.
- `source-findings.json`: coverage/quality/publication and raw/display precision
  findings from the validated source tables, with reproduction instructions.
- `preservation-before.json`: hashes of all 388 earlier data files.
- `security-validation.json`: scanner, safe HTTP metadata and integrity evidence.

## Access and dependencies

[Approved supply page](https://www.gov.uk/government/statistical-data-sets/live-tables-on-net-supply-of-housing),
[stock page](https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants),
[GOV.UK terms](https://www.gov.uk/help/terms-conditions) and retained robots rules
were reviewed. Official content is Crown copyright/OGL with attribution/exceptions;
no restricted account, credential, session replay or external contact was used.
GOV.UK's checked generic robots rules do not disallow these paths; no evidence
extends ONS-specific ISS-022 contact restrictions to these MHCLG/GOV.UK sources.
No ONS requests occurred and ISS-022 remains Open for its original scope.

ISS-003/004/009/011/012 remain Open for geography, historical availability,
compatibility/denominator timing, publisher quality and broader coverage. ISS-020
remains Open; private visibility and old remote-history limitations are unchanged.
No source-level ingestion result is a model-ready or ratio-ready dataset.
