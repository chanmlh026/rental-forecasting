# Task 009.1: ASHE earnings source investigation

Investigated 21 November 2026 from main `85dd08723ba60bd0224b97bf5b0c647e89690a80`,
which contains Task 008 merge `a247a292971594ab7fde507b7fbff64b53d0292f`.
Research only: no production ingestion, model-ready panel, mappings, unemployment,
growth calculation, feature selection or predictive assessment.

## Verified field

The approved measure is available in [ONS residence Table 8](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8).
In the latest ZIP, select `PROV - Home Geography Table 8.7a   Annual pay - Gross 2026.xlsx`,
worksheet `All`, column **D: Median**, header row 5. Columns A/B identify source
geography/name and code; C contains indicative weighted jobs in thousands, not
the unweighted sample size. The paired `8.7b` annual gross CV workbook has the same
selected sheet and column. Other sheets explicitly separate male/female and
full-time/part-time; workbook notes confirm that `All` combines those categories.
Units are GBP per year. Every advertised edition contains the annual gross
8.7a/8.7b pair; exact member hashes, sheet titles, headers and notes are in
[field evidence](field-evidence.json).

The native annual population is adult-rate employee jobs held for more than a
year, including pay affected by absence. Do not apply the weekly/hourly absence
restriction to annual pay. Reference period is the tax year ending **5 April of
the observation year**, not the calendar year. This is employee-job earnings,
excluding self-employed income, and is not household income. The owner accepts
that limitation; usefulness remains for later modelling assessment.

Structural differences include XLS/XLSX, leading apostrophes in GSS codes, and a
split first-row title in 2022 revised (year established from the advertised
edition and member filename). Original codes/cells/styles remain in immutable
ZIPs; research normalization removes only surrounding whitespace/apostrophes.

## Access and licensing

All **37 advertised ZIP editions returned HTTP 200**, spanning 25 observation
years, 2002–2026. Ordinary unauthenticated public ONS `/file?uri=/...` links work
with a transparent research User-Agent; no cookies, credentials or browser
impersonation were used. The earlier Task 006.2 HTTP 403 was not reproduced.
Its cause cannot be established because the earlier failure lacks sufficient
request/response evidence; link encoding and User-Agent differences are not
proven explanations. Manual owner access is separately reported in the prompt.

Initial two-request concurrency encountered **27 HTTP 429 responses**, with
`Retry-After: 10`. Original error snapshots are retained. One subsequent retry
per affected URL, after that interval and with 1.5-second serial spacing,
succeeded for all 27. The current script stops fresh requests on 429 and stops
retries on any renewed failure. Production should use cached immutable files,
serial/paced downloads and bounded Retry-After handling; persistent denial
requires stopping and reporting, with an explicitly supplied official-file
path as a possible fallback. Existing immutable local-bundle architecture can
support such a path; none is implemented here.

The dataset pages identify the Open Government Licence; [ONS terms](https://www.ons.gov.uk/help/terms-conditions)
were checked, with no dataset-specific exception observed for these published
aggregate tables. This does not authorise restricted microdata or bypassing
technical restrictions. Safe HTTP header allowlisting is reused; no session
headers are retained. [Access evidence](access-evidence.json) preserves successful
metadata, original 429 attempts, resolved URLs, retrieval times and hashes.

## Historical coverage

The advertised annual gross field is continuous from **2002 to 2026**. Earlier
general ASHE annual-pay history is described by ONS, but pre-2002 residence-LA
Table 8 files were not verified here. No earlier start is certified. All 37
advertised editions were inspected, including both 2006 methodological editions,
both 2011 SOC editions and provisional/revised pairs for 2016–2025.

Counts below distinguish source English LA GSS rows from exact matches to the
approved 294-code cohort and usable numeric medians. `x` is a source marker,
not zero. Missing cohort identities are retained as explicit code lists in
[coverage evidence](coverage-quality-evidence.json); no authority is dropped.
For 2002–2011, old numeric/alphanumeric codes prevent direct GSS classification:
English *coded geographies including counties* are reported instead. Their LA-only
total and correspondence require an approved historical lookup; **zero exact
matches does not mean absent earnings**. No name matching is applied.

| Advertised edition | English LA GSS rows / legacy coded geographies* | Cohort exact | Numeric | x | Unmatched cohort |
|---|---:|---:|---:|---:|---:|
| 2002 | 394* | 0 | 0 | 0 | 294 |
| 2003 | 394* | 0 | 0 | 0 | 294 |
| 2004 | 418* | 0 | 0 | 0 | 294 |
| 2005 | 418* | 0 | 0 | 0 | 294 |
| 2006 (consistent with 2005 methodology) | 418* | 0 | 0 | 0 | 294 |
| 2006 (consistent with 2007 methodology) | 418* | 0 | 0 | 0 | 294 |
| 2007 | 418* | 0 | 0 | 0 | 294 |
| 2008 | 422* | 0 | 0 | 0 | 294 |
| 2009 | 422* | 0 | 0 | 0 | 294 |
| 2010 (revised) | 422* | 0 | 0 | 0 | 294 |
| 2011 provisional, based on SOC 2000 | 422* | 0 | 0 | 0 | 294 |
| 2011 (revised, based on SOC 2010) | 383* | 0 | 0 | 0 | 294 |
| 2012 (revised) | 326 | 281 | 273 | 8 | 13 |
| 2013 (revised) | 326 | 281 | 277 | 4 | 13 |
| 2014 (revised) | 326 | 281 | 272 | 9 | 13 |
| 2015 revised | 326 | 281 | 263 | 18 | 13 |
| 2016 provisional | 326 | 281 | 269 | 12 | 13 |
| 2016 revised | 326 | 281 | 271 | 10 | 13 |
| 2017 provisional | 326 | 281 | 271 | 10 | 13 |
| 2017 revised | 326 | 281 | 272 | 9 | 13 |
| 2018 provisional | 326 | 281 | 268 | 13 | 13 |
| 2018 revised | 317 | 285 | 272 | 13 | 9 |
| 2019 provisional | 317 | 285 | 270 | 15 | 9 |
| 2019 revised | 314 | 286 | 271 | 15 | 8 |
| 2020 provisional | 314 | 286 | 269 | 17 | 8 |
| 2020 revised | 309 | 288 | 276 | 12 | 6 |
| 2021 provisional | 309 | 288 | 282 | 6 | 6 |
| 2021 revised | 309 | 288 | 281 | 7 | 6 |
| 2022 provisional | 309 | 288 | 267 | 21 | 6 |
| 2022 revised | 296 | 292 | 270 | 22 | 2 |
| 2023 provisional | 296 | 292 | 253 | 39 | 2 |
| 2023 revised | 296 | 292 | 257 | 35 | 2 |
| 2024 provisional | 296 | 292 | 292 | 0 | 2 |
| 2024 revised | 296 | 294 | 294 | 0 | 0 |
| 2025 provisional | 296 | 294 | 294 | 0 | 0 |
| 2025 revised | 296 | 294 | 294 | 0 | 0 |
| 2026 provisional | 296 | 294 | 293 | 1 | 0 |

Modern source GSS LA counts decline with reorganisations; changing exact cohort
counts do not establish historical boundary equivalence. Barnsley/Sheffield
source-code changes and predecessor areas require effective-dated policy under
ISS-003. Latest 2026 matches all 294 cohort codes; South Staffordshire
`E07000196`, source row 131, has `x` in both median pay and CV. The 2025 revised
and 2024 revised editions have 294 numeric medians, whereas 2023 provisional has
39 `x` values among 292 matched authorities. No exclusions or imputation.

Legacy source codes **68/69 collide** between Inner/Outer London aggregates and
City of London/Barking and Dagenham in ten editions (2004 through both 2011
editions). Original rows remain distinct by source row/name. No duplicate
code/name identities or modern GSS duplicates were found. A production parser
must never deduplicate legacy tables by code alone. Source row totals include
counties and aggregates and must not be labelled LA totals.

## Quality, publication and revisions

[ONS QMI](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/methodologies/annualsurveyofhoursandearningslowpayandannualsurveyofhoursandearningspensionresultsqmi)
describes the approximately 1% PAYE employee-job sample, sampling/non-sampling
uncertainty and item imputation. Published medians are not raw household records.
Retain source notes, fills/styles and paired numeric CVs; numeric values alone
do not express all quality information. Counts of jobs are rounded estimates,
so they cannot establish sample sizes. No confidence interval is calculated.

Publisher markers include `x` (unreliable, CV above 20%), `..` (disclosive),
`:` (not applicable), `-` (nil/negligible), and CV `.` (unavailable); empty cells
also occur outside the matched cohort. Observed matched non-numeric median cells
are all `x`. For 2025 revised, numeric matched CV bands are 63 at <=5%, 210 at
>5–10%, and 21 at >10–20%. For 2026 provisional they are 68, 198 and 27,
respectively. Some older numeric pay estimates lack a numeric CV: retain that
state. Band counts use published CV numbers, which may be rounded; original
quality styling is preserved separately. These are descriptive source bands,
not project acceptance thresholds.

The [2026 release](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/2026)
was published 22 October 2026, providing 2026 provisional and 2025 revised
estimates. Annual pay ends on 5 April; the current release lag is therefore
roughly six and a half months, not contemporaneous availability. Current
publication is in October; older QMI publication descriptions cannot certify
every historical release date. Revised 2026 estimates are expected with the
2027 release; this is a schedule, not observed availability.

Current edition subpages, including 2015 and 2025 provisional, display
22 October 2026 as the dataset release label. They do **not** establish those
editions' original publication dates. The 2015 page advertises a previous-v1
ZIP as well as the current file, demonstrating versioned downloads; that prior
file was not downloaded or compared. No complete historical correction ledger,
first-publication archive, release-delay series or exact historical availability
is certified. A generic `correction_mentioned` text-search result in
[publication evidence](publication-evidence.json) is a discovery hint, not proof
of a specific correction. Retrieval timestamps and ZIP dates are not release dates.

[Revision comparisons](revision-evidence.json) compare paired 2016–2025
provisional/revised source-code rows without selecting either as model inputs.
For 2025, 392 of 393 numeric pairs (395 common source-coded geographies) have changed medians;
these include aggregates/counties and are not cohort-only counts. Geography sets
and suppression status also change in some pairs; details are retained.
The 2006 and 2011 dual editions are distinct methodological regimes, not a
homogeneous revision series.

ONS documents breaks in 2004/2006/2011, SOC 2020 use from 2021 revised,
2020–2022 collection uncertainty, a 2023-onward comparability warning,
2024 higher-earner validation and 2026 digital collection. Preserve their dated
notes; no adjustment or cross-regime equivalence is approved here. See the
[interpretation guide](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/methodologies/guidetointerpretingannualsurveyofhoursandearningsasheestimates)
and current bulletin. Full point-in-time joins remain a later owner decision.

## Reproduction, validation and recommendation

Run from the repository root. Raw HTTP/ZIP snapshots are ignored under
`data/raw/ashe-009-1-investigation/`; their manifests and member hashes support
local replay. Row-level research extracts stay there, not in Git or model data.
Committed evidence contains metadata/aggregates and a few source examples.

```powershell
.venv/Scripts/python.exe reports/data_audits/009.1/investigate_ashe.py
# On a rate-limit stop, wait as instructed by ONS, then:
.venv/Scripts/python.exe reports/data_audits/009.1/investigate_ashe.py --retry-rate-limited
.venv/Scripts/python.exe reports/data_audits/009.1/investigate_ashe.py --publication
uv --system-certs run --with openpyxl==3.1.5 --with xlrd==2.0.2 python reports/data_audits/009.1/analyse_workbooks.py
.venv/Scripts/python.exe reports/data_audits/009.1/validate_audit.py
```

For completed downloads, replay the last two commands rather than reacquiring
links. A clean rerun may observe later publisher changes; compare hashes and
retain a separate snapshot rather than overwriting the original. Temporary
pinned Excel readers do not change project dependencies; system certificate
trust was used after uv's default trust rejected the TLS chain. Certificate
verification was not disabled. Sandbox filesystem/network denials required
approved execution outside the sandbox.

Offline audit passes for 37 pay/CV pairs: identical source row identities,
all cohort/CV counts reconcile, 73 immutable raw bundles verify and header
allowlisting passes. Initial validation exposed the documented legacy code
collisions; the check was corrected to verify row identity without dropping rows.
No production code/tests/data changed. Full application tests were not required
or run for this research-only change; repository/static/replay checks are recorded
with the task handoff. Python/JSON syntax, original prompt byte comparison,
seven-column/unique-task timing CSV, unchanged ISS-004/005/020 rows and
`git diff --check` pass. Optional `uv run black` could not run because Black is
not installed; no formatter dependency was added. See [validation evidence](validation-evidence.json).

The field and access contract are sufficiently established to propose a separately
authorised **earnings-only Task 009.2**: immutable official ZIPs, XLS/XLSX schema
checks, original row identity/codes, annual pay plus CV/markers/styles, explicit
release/retrieval/edition metadata and full coverage reporting. No unemployment
scope is implied. ISS-001 is resolved by owner approval plus field verification;
ISS-002 is resolved for demonstrated access and measured coverage, with earlier
403 causation unproven. ISS-003/004/011/012 remain Open. Owner approval is still
needed for historical geography mappings and later vintage/cutoff/preprocessing
policy; a harmonised historical panel cannot be certified before those decisions.
Do not inherit IUMZID4's vintage policy or infer predictive usefulness.
