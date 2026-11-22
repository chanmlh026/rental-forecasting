# Task 014.2: historical ASHE availability on current authority boundaries

Investigated **22 November 2026**. Research only; owner review pending.

Nomis supplies the approved earnings field, but **does not establish a complete,
verified comparable historical series for all 11 authorities**. The ONS April
2019 extract supplies independently defined historical geography for the four
2019 authorities. Several gaps can therefore be reduced without calculating a
combined median; no source or modelling vintage is selected here.

## Sources, access and reproducibility

| Official source | Identifier / scope | Evidence retained |
|---|---|---|
| [Nomis resident ASHE](https://www.nomisweb.co.uk/datasets/asher) | `ASHER`, numeric API dataset `NM_30_1`; annual series 2002-2025 advertised at access | Structure, codes, native geography families, date revisions, focused CSV responses |
| [ONS Table 8](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8) | Existing Task 009.1/009.2 immutable source editions; 22 editions for 2015-2026 inspected read-only | Original ZIP/member hashes, exact source rows/cells, original codes and notes |
| [ONS ad hoc 11165](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/adhocs/11165annualsurveyofhoursandearningsasheestimatesofannualandweeklyearningsbylocalauthorityusingapril2019localauthorityboundariesforplaceofworkandresidence2003to2017) | Published 23 January 2020; residence `k54bresidence1.zip`; advertised 2003-2017, April 2019 boundaries | Only residence ZIP acquired, 14,294,759 bytes; annual pay/CV worksheets for 2015-2017 inspected |

Source: Office for National Statistics. [Nomis copyright](https://www.nomisweb.co.uk/home/copyright.asp)
permits ONS aggregate reuse under OGL with attribution; third-party exceptions
remain separate. The special-release page identifies OGL v3.0. No restricted
microdata, authentication, cookie replay or access-control workaround was used.
[Nomis API guidance](https://www.nomisweb.co.uk/api/v01/help) requests few concurrent
requests and limits CSV downloads to 25,000 values. Queries here were serial,
paced one second apart; largest earnings query contains 121 observations.
No HTTP 429/403 arose in retained successful network queries.

**Access limitation discovered during work:** the initial checkout predates
ISS-022 and the cleaned-history migration. One ONS residence ZIP was downloaded
with a descriptive research User-Agent before remote-main review revealed the
owner's existing ban on further automated ONS downloads pending an approved
non-personal contact. No further automated ONS requests followed discovery.
The helper now refuses fresh non-Nomis URLs, including the ONS download.
This download does not satisfy or override ISS-022; further ONS acquisition
remains blocked by that prerequisite. Offline inspection continued. The initial
sandbox network refusal was an execution restriction, not evidence of publisher
denial or nonexistence. The authorised network retry used the same official host.

Some API discovery attempts returned HTML help with HTTP 200, not metadata:
`ASHER/def.sdmx.json`, `NM_30_1/overview.json` and `NM_30_1/def.meta.json`.
Correct identifiers/routes were obtained from official query/help pages;
`NM_30_1/def.sdmx.json` and `NM_30_1.overview.json` returned valid metadata.
`pay/7.metadata.json` returned `notfound`; geography metadata had null entries.
These are evidence gaps, not data-absence findings. Web-tool fetch failures are
also not evidence that data do not exist. No alternate host or identity was used.

[Access evidence](access-evidence.json) records exact URLs/parameters, retrieval
UTC timestamps, HTTP status, content type, size, SHA-256 and safe headers;
no session headers are retained. [Coverage evidence](coverage-evidence.json)
retains every queried authority/year/family/value/status, special-table pay/CV
cells, source identities and comparison differences. Raw bodies are ignored
under `data/raw/ashe-014-2-investigation/`, separate from production snapshots.

## Definition verification

Nomis `sex=7` **Total** combines male/female and full-/part-time categories;
`pay=7` **Annual pay - gross**, `item=2` **Median**, `measures=20100` **Value**.
`NM_30_1` is the **resident** analysis, distinct from workplace products. Its
code lists and official source description identify the required concept.
The 258 same-code edition comparisons below further corroborate field identity.
Generic dataset unit metadata also lists weekly pounds/hours; that is not the
unit for this selected annual-pay item. This field is GBP per year.

The reference is ONS 8.7a, `All!D` (Median); special K54b residence `.7a`,
`All!D` has the same annual gross all-employee title, sex/working-pattern sheets
and median header; `.7b` gives the paired CV percent. Special `Notes` rows
32/34 distinguish weekly/hourly absence rules from annual estimates: adult-rate
employee jobs held for more than a year, tax year ending 5 April of the labelled
year. Do not annualise weekly pay or interpret the label as calendar-year income.
Nomis's generic survey-date metadata is not a replacement annual reference period.
Native eligibility/absence wording is not fully restated by Nomis's pay-specific
metadata, which returned notfound; existing ONS annual guidance supplies that
context. Task 009.2's 2022 revised/2023 provisional population-note conflict is
preserved; no reinterpretation, filter or claim of perfect cross-year population
comparability is made. Employee-job earnings are not household/self-employed income.

## Questions 1 and 2: initial authorities and historical geography

All three current GSS codes are recognised. Exact query parameters are retained
in `initial.csv`'s access record: geography `E06000060,E06000061,E06000065`,
`date=2015,2016,2017,2018,2019`, and the four selected dimension codes above;
`ExcludeMissingValues=false`. Initial GSS requests resolved to TYPE423
(county/unitary, April 2023). Explicit TYPE424 (district/unitary, April 2023)
native-code queries reproduce their values/statuses, eliminating family ambiguity
for these cells without assuming geographical comparability.

| Authority | 2015 | 2016 | 2017 | 2018 | 2019 | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| Buckinghamshire E06000060 | 25500 | 26000 | 26995 | 28090 | 29302 | Numeric A in every year; historical assignment unverified |
| North Northamptonshire E06000061 | M | M | M | M | M | Q missing in every year, including older TYPE432 |
| North Yorkshire E06000065 | 20866 | 21227 | 21873 | 22937 | 23852 | Numeric A in every year; historical assignment unverified |

The Buckinghamshire and North Yorkshire values exactly match the existing ONS
county rows in these years. This is evidence of published official county
estimates, **not evidence of new retrospective recalculation** by Nomis.
Independent statutory evidence supports footprint continuity:
[SI 2019/957 article 3](https://www.legislation.gov.uk/uksi/2019/957/made)
constitutes Buckinghamshire coterminous with the county, and
[SI 2022/328 article 3](https://www.legislation.gov.uk/uksi/2022/328/made)
constitutes the North Yorkshire district coterminous with the county.
Likewise [SI 2022/329 article 3](https://www.legislation.gov.uk/uksi/2022/329/article/3/made)
supports Somerset's county/district continuity. These facts make the county
observations promising candidates for owner consideration without combining
predecessor medians. They do not independently establish how Nomis assigned
each older observation, every intervening boundary vintage, or whether a
retrospective recalculation occurred. **Historical Nomis values remain geography
unverified**; no claim of a fully verified current-boundary backcast is made.

The requested GSS identifiers remain consistent in query outputs, but native
Nomis identifiers/families differ. TYPE423 for a unitary and TYPE424 for its
district counterpart are separate selectable records. TYPE424 alone does not
prove a comparable statistical population in older years.

## Questions 3 and 5: all-authority coverage, 2015-2026

The following table reports the **April 2023 district/unitary family TYPE424**,
11 authorities x 11 published years = 121 observations: **76 numeric A, 45 Q**.
Bare current GSS queries gave the same values and statuses, including the nine
unitaries resolved to TYPE423. All published numeric observations are kept as
**U**, including later years, because this task has not independently certified
the complete geography-vintage basis of the Nomis series. This conservative
classification does not assert that later-period geography is wrong.

- **U:** published numeric value; geography unverified for a comparable historical series.
- **M:** explicit Q / missing observation, not a numeric zero or confirmed suppression.
- **N:** 2026 is not in this Nomis dataset's returned time codelist; unavailable in the inspected current dataset at access, not a permanent absence claim.
- **S:** explicit suppression (none observed in these queried Nomis cells).
- **C19:** confirmed published April 2019 geography, used in the special-extract table below; does not certify all sources on April 2025 boundaries.
- **E:** unresolved access/evidence gap; no authority/year classified unavailable solely from a failed query. Geographic methodology gaps are represented by U.

| Authority (GSS code) | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bournemouth, Christchurch and Poole (`E06000058`) | M | M | M | U | U | U | U | U | U | U | U | N |
| Dorset (`E06000059`) | U | U | U | U | U | U | U | U | U | U | U | N |
| Buckinghamshire (`E06000060`) | U | U | U | U | U | U | U | U | U | U | U | N |
| North Northamptonshire (`E06000061`) | M | M | M | M | M | M | M | U | U | U | U | N |
| West Northamptonshire (`E06000062`) | M | M | M | M | M | M | M | U | U | U | U | N |
| Cumberland (`E06000063`) | M | M | M | M | M | M | M | U | U | U | U | N |
| Westmorland and Furness (`E06000064`) | M | M | M | M | M | M | M | U | U | U | U | N |
| North Yorkshire (`E06000065`) | U | U | U | U | U | U | U | U | U | U | U | N |
| Somerset (`E06000066`) | U | U | U | U | U | U | U | U | U | U | U | N |
| East Suffolk (`E07000244`) | M | M | M | M | M | M | M | U | U | U | U | N |
| West Suffolk (`E07000245`) | M | M | M | M | M | M | M | U | U | U | U | N |

The extended assessment was feasible through small queries even though the
initial three did not establish a uniformly suitable series. **Family-specific
missingness is not source-wide absence:**

| Additional official family | Additional numeric cells absent from TYPE424 | Result |
|---|---|---|
| TYPE432: April 2021 district/unitary | North/West Northamptonshire, 2020-2021 (4); East/West Suffolk, 2018-2021 (8) | All numeric, still U; 121 cells across TYPE432/434 checked in total |
| TYPE434: April 2019 district/unitary | East/West Suffolk, 2018-2021 (same cells as TYPE432) | Corroborates availability; not independent extra coverage |
| TYPE434 versus TYPE432/424, Dorset | TYPE434 gives Q in 2015-2017 where newer families return numeric values | Different historical content despite the same GSS code |

Nomis's best observed family coverage therefore begins in 2018 for BCP and
East/West Suffolk, 2020 for North/West Northamptonshire, and 2022 for Cumberland
and Westmorland and Furness. Buckinghamshire, North Yorkshire and Somerset have
numeric 2015-2025 observations; Dorset has newer-family numerics throughout but
its early geography is specifically unsafe to assume. These are coverage
observations, not source/vintage selection or reconstructed authority series.

For all 11, existing ONS **2026 provisional** has numeric medians; Nomis's lack
of 2026 is therefore not general ASHE unavailability. Existing ONS exact current
GSS-code numeric rows begin in 2018 revised for the four 2019 authorities,
2019 revised for Buckinghamshire, 2020 revised for both Northamptonshire
unitaries, and 2022 revised for the four 2023 authorities, continuing through
2026 in the inspected editions. Earlier county rows exist for Buckinghamshire,
North Yorkshire and Somerset (and old Dorset); exact-code absence is not
absence of those underlying source statistics. Every edition/row/value is
retained separately in coverage evidence. No suppressed pay cells occurred
among these selected current-code ONS rows or the 12 special-extract pay cells;
this does not remove other cohort-wide suppressions documented in Task 009.2.

## Question 4: the April 2019 historical extract

**Yes, for the examined 2015-2017 years and required earnings definition.**
The official release description expressly specifies April 2019 LA boundaries,
and the residence worksheets' `Notes` rows 8/10 repeat that geographical basis.
The selected annual tables explicitly cover all employee jobs and provide the
four new GSS codes. This is independent geographical evidence beyond names/codes.
It establishes retrospectively produced estimates on those stated boundaries;
the precise recoding/estimation algorithm and microdata treatment are not
documented in the inspected material. The advertised 2003-2014 observations
were not quantified here; no complete earlier-history claim is made. Workbook
Notes mention 1997-2017/GB, whereas the release and ZIP inventory delimit the
advertised 2003-2017 scope and distinguish pre-2012 England/Wales coverage.
Preserve that wording inconsistency; it does not change the checked 2015-2017 cells.

| Authority / code | 2015 GBP (CV %) | 2016 GBP (CV %) | 2017 GBP (CV %) | Geography / cells |
|---|---:|---:|---:|---|
| BCP / E06000058 | 22106 (6.4) | 22292 (5.8) | 22451 (5.3) | C19; annual pay and CV All!D60 |
| Dorset / E06000059 | 20722 (5.8) | 20889 (5.7) | 21356 (7.6) | C19; All!D61 |
| East Suffolk / E07000244 | 20822 (13.0) | 21640 (9.8) | 21478 (13.0) | C19; All!D251 |
| West Suffolk / E07000245 | 20919 (9.2) | 22032 (9.4) | 24160 (6.7) | C19; All!D252 |

The CVs above are published percentages, not project acceptance thresholds.
Numeric pay does not remove sampling uncertainty; keep CVs, styles and notes.
The ad hoc Notes warn about suitability and possible revisions. This is a
January 2020 publication of earlier observations, not proof those values were
available in their observation years. It cannot fill pre-2020 PIT information
sets without a separately approved availability policy.

## Comparison and geography risk

| Limited comparison | Observation | Interpretation |
|---|---|---|
| Nomis TYPE424/432 Dorset versus old ONS county E10000009, 2015-2017 | 20803 / 21018 / 21363 match the original county medians exactly | Strong warning of carried historical geography; not verified recalculation to the new area |
| Same Nomis values versus special April 2019 Dorset | Special 20722 / 20889 / 21356; Nomis minus special = 81 / 129 / 7 GBP | Incompatible as interchangeable same-geography estimates without clarification; vintage and geography can both matter |
| ONS county versus new Dorset boundary | [SI 2018/648 articles 3/7](https://www.legislation.gov.uk/uksi/2018/648/pdfs/uksi_20180648_en.pdf) and [official ministerial statement](https://questions-statements.parliament.uk/written-statements/detail/2018-02-26/HCWS486) identify Christchurch moving into BCP and the rest of the old county forming Dorset | Independent evidence the old county is not the new Dorset footprint; no source-code mapping applied |
| Nomis 2018, four 2019 authorities | 22739 / 21526 / 22649 / 24585, in BCP / Dorset / East Suffolk / West Suffolk order | Exactly equals ONS 2018 revised same-code rows; special extract ends 2017, so no same-year overlap to compare with it |
| Nomis 2025 versus ONS 2025 provisional | All 11 same-code medians agree | Definition and edition corroboration, not complete boundary proof |
| Nomis 2025 versus ONS 2025 revised | All 11 differ; e.g. Buckinghamshire 35937 versus 35898; North Yorkshire 30683 versus 30456.2 | Nomis last update 3 Nov 2025 versus existing ONS 2026 publication of revised 2025; revisions are not necessarily errors |

Across the explicit TYPE424/432/434 requests, 258 same-code numeric edition
comparisons yielded 142 equal and 116 different values. These counts include
repeated observations across families and comparisons to multiple editions;
they are not 258 independent observations or a discrepancy rate. No comparison
silently pairs predecessor districts with a new authority. No comparable
same-year overlap exists between the special extract and exact-current-code
rows of the ordinary ONS series for the four 2019 authorities in 2015-2017.

Nomis metadata gives dataset LastUpdated/LastRevised `2025-11-03 17:30:00`.
Its official 2025 release article identifies provisional 2025/revised 2024.
Selected time metadata retains historical revision releases, including 2015
current revision 7 Nov 2016, 2019 current revision 5 Nov 2020, and 2022 current
revision 7 Dec 2023. Timezone and a complete historical availability ledger are
not established. Dates are metadata, not proof of when each new-geography
backfill first became available. No preferred publication edition is chosen.

No official Nomis documentation inspected here establishes its exact historical
geography assignment or retrospective recalculation for these reorganisations.
The current-family label is insufficient, as the Dorset and family-missingness
evidence demonstrates. Unrelated claimant-count geography documentation was
not applied to ASHE. No publisher contact was made.

## Question 6 and owner options

There is **enough verified official evidence to reduce some reconstruction
needs, but insufficient verified coverage to eliminate all historical gaps**.
The four 2019 authorities have C19 values in the special extract for 2015-2017;
ordinary source/older Nomis families publish 2018 onward values. County-level
observations plus statutory coterminosity make Buckinghamshire, North Yorkshire
and Somerset strong candidates for further verification. Nomis did not return
2015-2019 values for either Northamptonshire unitary or either new Cumbria
unitary in the inspected applicable families. This is not proof no other
official extract exists. No universal comparable-history solution is established.

Options for owner consideration, **not implemented or approved here**:

1. Review the explicitly defined 2019 historical extract alongside later editions,
   retaining publication dates, CVs and all geography/vintage qualifications.
2. Seek ONS/Nomis clarification of county continuity, Dorset's historical
   assignment and geography-family backfills; request an official current-boundary
   extract for remaining gaps if available. Any fresh automated ONS acquisition
   first requires resolving ISS-022. No contact has been sent.
3. Retain explicit missingness and consider a shorter earnings-history window
   or separately approved model treatment where comparable official data remain
   unavailable. Predictive usefulness is untested; availability is not evidence
   for inclusion, exclusion or imputation.
4. If official estimates cannot fill required gaps, commission a separate
   methodology investigation with owner approval. Averaging or job-weighting
   predecessor medians does not recover a combined median; it is prohibited here.

## Repository continuity, dependencies and validation

Starting checkout `review/009-5-merge-validation` contained legitimate dirty
Task 009.5 files and stale pre-migration history. They were preserved. GitHub
connector confirmed PR #12 merged at `2026-11-22T12:54:45Z`, head
`da24b805945153dba0578a694dfcab5a4cd66304`, merge
`c242af94b3e2be21889eac4092dd4ffc185ad788`.
CLI remote inspection/fetch failed with name-resolution/TLS errors; certificate
checks were not disabled. The clean checkout already contained that merged
commit. A local read-only fetch supplied it and an isolated worktree was created
at `data/.staging/task0142-review`, branch `research/014-2-historical-ashe`.
Only Task 014.2 files/timing row were moved there; no dirty Task 009.5 work was
stashed, overwritten, discarded or included. This safely incorporates the
complete merged Task 014.1 baseline rather than copying selected stale documents.
Task 014.1's archive/journal and Decision A were reviewed and preserved.

The owner-confirmed B1 approval is recorded once in the existing dictionary,
linked from the journal/register, with the verbatim confirmation in the task
archive. Implementation remains deferred; it is separate from this ASHE research.
ISS-003/004/011/012: proceed with documented geography, vintage and quality
limitations. ISS-020: remains Open for public-release security; clean ancestry
is used and no public publication is performed. ISS-022: remains Open and blocks
further automated ONS acquisition. No issue closed, new overlapping issue or
methodology decision. Decisions A and B1 retain their approved scope.

Changed files: task archive, dictionary, ISS-003/register note, Phase 2 journal,
shared timing CSV, this report, two audit-only Python helpers and three JSON
evidence files. No production source, tests, configuration, pinned geography,
dependencies, production datasets or prior evidence changed.

Offline reproduction from this worktree with the existing project environment:

```powershell
uv run python reports/data_audits/014.2/analyse_evidence.py
```

Original source verification additionally accepts `--original-root PATH` pointing
to the checkout holding Task 009.1 immutable raw bundles; it verifies original
ZIP/member hashes and exact cells against the prior audit without redownloading.
The small resulting ignored `existing-ons-evidence.json` supports subsequent
offline replay. On this machine the existing environment was invoked from the
original repository using `uv --cache-dir .uv-cache run --no-sync python` plus
the worktree script path; no dependencies were installed. The first default uv
cache attempt failed due to sandbox access; the workspace cache resolved it.

[Validation evidence](validation-evidence.json): 30 raw responses verified by
hash/size; initial 15 cells and 121 TYPE424 cells checked; 121 older-family cells
checked; explicit measure/population codes, unique authority/year identities,
status/value consistency and initial/native-family reconciliation passed.
12 special pay and 12 CV cells checked; all 22 existing ONS ZIP/member hashes
and selected source cells verified read-only; 258 same-code comparisons retained.
JSON/syntax, prompt preservation, seven-column unique timing rows, local
Markdown links/anchors, unchanged Decision A/other issue rows/Phase 1 journal,
production-file scope and Git whitespace/integrity checks are recorded in the
final task handoff. Full production tests are not required or run for this
research-only change. No formatter or new test/dependency framework introduced.

Review status: submitted as local research deliverables for owner consideration;
no PR, push, merge, mapping or harmonisation implementation. Git commit and
measured timing receipt are appended to the task archive/shared CSV at cutoff.

### Owner-authorised submission update - 22 November 2026

The owner subsequently requested pushing this existing branch and opening a PR
against main for independent review; the earlier local-only status above is
historical. All 11 research files were committed at `66513e8`, and all 30 retained
response hashes plus documentation, header/security and Git checks were rechecked
without source acquisition. ISS-003 remains Open and Decisions A/B1 are preserved.
Main has advanced through Task 012 to `0d24e70be44781d8d102b4a8d4b6fdc1664474b6`.
A merge-tree preview reports conflicts in the dictionary and issue register;
no index, working-tree or branch merge was performed. These documentation
conflicts require reconciliation before any later merge, independently of the
unresolved geography/methodology review. This submission preserves the original
research commit, original dirty checkout and clean-history ancestry. No production
code/data, source acquisition, mappings or merge is included in this handoff.

### Owner-authorised conflict reconciliation - 22 November 2026

The owner subsequently authorised updating the research branch from latest main
and resolving the two documentation conflicts. Both complete task sections,
all 22 main issue records, dated ISS-003 additions and evidence links are now
preserved; Decisions A/B1 and original research evidence are unchanged. Main's
Task 012 implementation enters unchanged through the baseline update. The
previous conflict status above is historical. Preservation, 30 raw response
hashes, documentation/syntax/security-pattern and Git checks passed; no new
production changes, data acquisition, mapping or methodological decisions.
PR #14 remains for independent review; it is not merged by this update.
