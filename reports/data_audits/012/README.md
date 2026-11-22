# Task 012: MHCLG planning statistics - Phase 1

**PASS WITH CONDITIONS.** PS1/PS2 source ingestion is validated; no suitable
all-residential LA dwelling-unit-permissions source is established. This is
Phase 1 ingestion, not a model-ready panel or Phase 2 harmonisation.

## Sources, schema and coverage

[Official MHCLG landing page](https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics),
[verified inventory](../../../configs/mhclg_planning_sources.json) and
[source findings/dependencies](source-findings.json) retain URLs, original file
identities/checksums, publication/correction definitions, rights and limitations.
Eleven immutable raw bundles retain four CSV assets and seven source documents,
including the official district dictionary. No third-party local extract or ONS
request was made. GOV.UK terms and publication OGL v3.0 wording were checked;
third-party exceptions do not establish Glenigan local-extract rights.

| Source asset | Original authority-quarter rows | Quarters | Count fields | Verified history |
|---|---:|---:|---:|---|
| PS1 full | 42,861 | 121 | 88 | 1996 Q2-2026 Q2 |
| PS2 full | 68,583 | 189 | 329 | 1979 Q2-2026 Q2 |
| PS1 recent | 1,240 | 4 | 88 | 2025 Q3-2026 Q2 |
| PS2 recent | 1,240 | 4 | 329 | 2025 Q3-2026 Q2 |

All native fields are preserved, including region, original LPA code/name,
quarter, financial-year labels and every count category/time bucket. The full
assets are the historical source tables; recent assets are separate overlapping
audit tables, not appended to the histories. Original strings are in each
`*_source` table; `*_values` contains parsed numeric counts plus unchanged
identifiers and original source-record/provenance fields. There are **113,924**
asset-specific rows, **26,852,655** count cells: **14,816,586** numeric and
**12,036,069** literal `..` markers. Counts are applications/decisions/actions as
labelled, including major/minor residential granted/refused/total decisions;
none is converted to permitted dwelling units.

PS1's extra PDR definition note makes its header the fourth CSV record; PS2's
header is the third. Both are decoded cp1252, preserving original punctuation
and the note's literal date typo. `..` may reflect not collected/not available;
it is not zero. PS1 quarter-end applications ceased collection after April 2014.
PDR/category definitions change; historical comparability is not assumed.
Publisher imputation and rolling revisions are documented, without comprehensive
cell-level flags; a numeric value is not proof of unimputed data.

[Quarterly coverage](quarterly-coverage.json) has 318 asset/quarter rows. Unique
exact cohort-code matches range 249-294 for PS1 and 238-294 for PS2; from 2015 Q1
both range 283-294. Recent quarters have all 294 codes with numeric major/minor
residential granted counts. All source rows remain, including noncohort LPAs,
national parks and development corporations. LPA responsibilities can cover
only part of an LAD. Neither direct code matching nor a current retrospective
file certifies historical boundary equivalence.

The full files contain 3,678 PS1 and 9,000 PS2 rows without a syntactically valid
GSS code. Fifteen identical PS1 Shepway row pairs (1996 Q2-1999 Q4) are retained
and flagged (30 rows). PS2 has 1,905 rows in 83 quarter groups sharing `-`,
including distinct predecessor rows and repeated names with different values.
Source identity is edition plus original record, not code/quarter alone. These
are source-quality facts for ISS-003/011, not permission to deduplicate or map.

## Publication, independent comparison and preservation

The release was first published 24 September 2026; its 29 October update corrects
Table 3b in the statistical release, not a verified PS1/PS2 CSV revision. Document
first/public/internal update timestamps retain original offsets separately. No
historical release date is inferred from a quarter, filename or retrieval. Current
notes describe re-imputation/revision of seven earlier quarters. Earlier release
versions and complete historical publication calendars are not reconstructed.

[Independent audit](validate_ingestion.py) uses pandas CSV parsing/header
discovery independently of the production csv parser. All **27,422,275 native
fields**, parsed counts, source/period identities, financial-year labels, flags
and coverage match their own files. Both 1,240-row recent assets exactly match
full-file counterparts: zero differing fields across 524,520 non-key comparisons.
All **12** validated/processed tables agree. Offline replay preserves all **471**
data files, including **423** pre-task files and the new sources/outputs; the
Phase 2 journal and pinned reference are unchanged.

The [initial audit diagnostic](validation-blocker.json) records a BOM-related
reference-header load failure before source comparison. The independent reader
was corrected to UTF-8 with BOM handling, regression-tested and rerun successfully;
production/source/reference bytes were unchanged. Absent document dates are
standard JSON nulls; that receipt-serialization correction changed no comparisons.
[Passing evidence](validation-evidence.json) records source counts, comparisons,
preservation and validated code/configuration hashes.

## Dwelling-unit permissions and remaining conditions

The reviewed MHCLG planning sources publish application decisions and England
Glenigan housing-unit totals; national rolling values do not establish local
units. The technical notes identify a partial official candidate: annual LAHS
Section I affordable-housing units granted permission. Its affordable-only
scope cannot substitute for all-residential units; permission-field history,
coverage/definitions/revisions and extract-specific rights remain unaudited.
No LAHS dataset was acquired. See [investigation and official references](source-findings.json).
ISS-010 and ISS-017 stay Open; separate owner authorisation is required before
any units-source ingestion. ISS-003/004/011/012/020 stay Open. No ratios, joins,
frequency standardisation, imputation, mapping, model or Phase 2 decision change.

## Reproduce

With the retained ignored raw bundles, from the clean repository root:

```powershell
uv run python -m ingestion.mhclg_planning --snapshot-id 2026-11-22-task012
uv run python reports/data_audits/012/validate_ingestion.py
uv run pytest tests/test_mhclg_planning.py
uv run pytest
```

Same-snapshot ingestion reuses completed requests; the independent audit injects
a downloader that raises on any acquisition attempt. Missing/corrupt bundles fail
clearly. A fresh clone needs verified data recovered through approved storage;
lightweight Git evidence is not a substitute dataset. `inspect_sources.py`
reuses saved documents/assets; it can acquire missing authorised sources and
therefore is not the network-disabled validation entry point. A changed official
source requires reviewed inventory/new snapshot, preserving prior bytes.

**39 focused tests passed in 1.20 seconds; 343 full regression tests passed in
67.23 seconds.** Source-history secret scanning, 11 raw checksums/header checks,
lock, formatting and Git integrity checks passed (informational dangling objects
only). Final source/staged secret and documentation checks are recorded in the
security receipt. No expensive repeats solely for PR preparation. Original prompt
and full report: [Task 012](../../../docs/012-mhclg-planning-applications-ingestion.md).
