# Task 010: ONS population, area and migration

**PASS WITH CONDITIONS for the owner-approved offline scope.** Nine retained
official workbooks are ingested; five advertised superseded files remain
unacquired. This report does not claim every historical ONS vintage is present or
that the data is model-ready. See [the task archive and full report](../../../docs/010-ons-population-area-and-migration-ingestion.md).

## Reproduce without ONS requests

From the clean repository root with the retained source bundles:

```powershell
uv run python -m ingestion.ons_population --snapshot-id 2026-11-22-task010
uv run python reports/data_audits/010/inspect_sources.py
uv run python reports/data_audits/010/validate_ingestion.py
uv run pytest
```

The production CLI and investigation replay are offline-only. A missing raw
request fails clearly; neither invents a contact header nor downloads a substitute.
The low-level transport boundary remains tested with synthetic responses and
requires an approved non-personal project contact URL before network access.
No further automated ONS downloads are authorised in this task.

A fresh clone lacks ignored raw/output data. Recover the verified retained bundles
through the project's approved storage process; do not copy old Git history or
sensitive manifests from the pre-remediation checkout. The small JSON reports in
Git are evidence, not replacement source datasets.

## Editions and periods

| Retained edition | Selected sheets | Population | Published area/density | Migration year ending mid-year |
|---|---|---|---|---|
| summary2025 | MYE3/4/5 | 2011-2025 | Area once per source area; density 2011-2025 | 2025 |
| detail2025 | MYEB3 | 2011-2025 | Not in this component table | 2012-2025 |
| summary2024 | MYE3/4/5 | 2011-2024 | Area once; density 2011-2024 | 2024 |
| detail2024 | MYEB3 | 2011-2024 | Not in this component table | 2012-2024 |
| summary2023 | MYE3/4/5 | 2011-2023 | Area once; density 2011-2023 | 2023 |
| detail2023 | MYEB3 | 2011-2023 | Not in this component table | 2012-2023 |
| summary2022_2023 | MYE3/4/5 | 2011-2022 | Area once; density 2011-2022 | 2022 |
| summary2022_2021 | MYE3/4/5 | 2011-2022 | Area once; density 2011-2022 | 2022 |
| detail2022 | MYEB3 (2021 Geography), MYEB3 (2023 Geography) | 2011-2022, each geography separately | Not in these component tables | 2012-2022, each geography separately |

There are **198505** selected source cells: population 44898, published density
23754, area 1801 and 21342 cells for each of the six internal/international
inflow, outflow and net measures. These are edition-specific observations,
including repeated revised values; they are not a single stitched panel.

The latest summary has 357 source geographies including aggregates; detailed
files on 2023 geography have 318 LAs. Older 2021 geography has 373 summary areas
and 331 detailed LAs. Exact approved-cohort matches are 292 on 2023 geography,
288 on 2021 geography. All exact matches have numeric selected values in their
respective periods. Coverage counts are findings, not universal pass thresholds.

The 76 source markers are literal `No data`: 38 aggregate areas each for
internal inflow/outflow in summary2023. They remain markers, not zeros. Net values
are read from published cells; neither net migration nor density is calculated.
Area has no separately labelled reference year: it is retained once per
area/sheet/edition, in square kilometres, without broadcasting it across years.

## Reconciliation and preservation

`validate_ingestion.py` resolves workbook ZIP relationships, shared strings and
original XML cells independently of the production workbook parser/column mapper.
It verifies every selected cell, original code/name/type, period, measure, unit,
value/marker, formula, style ID and manifest provenance. It separately checks raw
request identities/checksums; an observation from another edition or geography
cannot be mistaken for an equivalent cell. All 599 coverage rows reconcile.
Same-vintage population and migration comparisons between each summary and its
2023-geography detailed file cover 24804 cells, with zero differences.

All six validated/processed tables agree. The rerun uses a downloader that raises
if called, and verifies that all 388 data files remain byte-for-byte unchanged,
including 342 pre-existing files. All 16 source bundles are immutable and verified.
The full suite passed 266 tests (38 new focused cases); no expensive test/ingestion
reruns are required for later documentation-only or PR preparation changes.

## Geography, revisions and limits

Barnsley/Sheffield remain source E08000016/E08000019 versus reference
E08000038/E08000039. Their latest-summary MYE4 rows 72/75 each retain all 37
selected numeric cells across the source tables. Names and source geography types
confirm present observations, not missing values. The retained notes do not explain
the code changes; no equivalence/mapping is inferred. Older county names North
Yorkshire/Somerset also coincide with newer unitary names; names do not establish
boundary equivalence. All original levels and codes remain separate.

2025 summary notes refer to April 2024/2024 authorities while its edition label
and the detailed table identify 2023 geography. All raw statements are retained and
observations carry `geography_notes_require_review`. No silent harmonisation or
choice of a preferred geography is made.

Compared only on matching source code/geography/measure/year, detailed 2022-to-2023
shared cells have no changes (24804 comparisons); 2023-to-2024 has 4440 changed
numeric cells, and 2024-to-2025 has 3810. These are revision audit counts, not
features. Source notes retain Census 2021 rebasing and updated international
migration information. Publication claims remain source text, separate from
observation year/retrieval; timezone and complete first-publication availability
are unverified. No model-input vintage or fixed lag is selected.

## Pending acquisition and access

The three retained version-history pages advertise five unavailable local files:
2022 summary on each of 2021/2023 geography, previous v1 and v2; detailed 2022
previous v1. Their exact official URLs and supersession/correction evidence are
in `source-investigation.json`/retained pages. They require a future approved
project contact URL or organisation email before any automated ONS retrieval.
They do not create a missing year in the latest 2012-2025 migration history; they
limit historical vintage/correction coverage. Pre-2011 detail and national/regional
only files were identified but are outside this forecasting-history LA contract.

[ONS terms](https://www.ons.gov.uk/help/terms-conditions) and the retained catalogue
identify Crown copyright/OGL reuse with attribution and exceptions. No restricted
account was used. [ONS fair use](https://www.ons.gov.uk/help/fair-use-policy) and
[bot guidance](https://developer.ons.gov.uk/bots/) require an identifying bot header,
respectful rates/Retry-After and an appropriate contact without personal details.
After reviewing the detailed contact requirement, the acquisition worker was
stopped and the owner explicitly selected offline development. Existing raw
headers are preserved as historical provenance; current code invents no contact.

## Evidence files

- `source-investigation.json`: retained editions, original schemas/notes, official
  document identities, excluded files and pending downloads.
- `validation-evidence.json`: full-cell, per-period, same-vintage and offline
  preservation results, tests and validated code/contract hashes.
- `source-findings.json`: coverage, source-marker and revision counts plus the
  Barnsley/Sheffield investigation (from the validated observations/coverage tables).
- `preservation-before.json`: hashes of the 342 pre-existing data files.
- `security-validation.json`: project-source/clean-history secret scans and HTTP
  metadata/integrity checks; does not resolve retained remote-history ISS-020.

ISS-003/004/011/012/020 remain Open. ISS-022 records the concrete contact approval
needed before the affected future acquisition; it does not block the completed
offline ingestion/reconciliation. No code mapping, imputation, target joins,
features, models, source substitutions or cloud infrastructure were introduced.
