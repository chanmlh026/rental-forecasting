# Task 014.3: historical ASHE predecessor median earnings ranges

Research date: **22 November 2026**. Research-only; independent review required.

The observed ranges justify **selective further investigation**, not a uniform
approximation or a methodological approval. Complete published predecessor
coverage shows comparatively narrow spans for BCP (5.43-14.03%) and West Suffolk
(11.17-17.14%), but much wider spans for Cumberland (up to 53.29%), Dorset
(up to 47.36%) and North Yorkshire (42.14-45.22% in its complete editions).
A small partial span is especially unsafe: Cumberland's 2018 provisional span
is 6.05% with Copeland suppressed, whereas complete 2015 coverage spans 49.11%.
No combined median, midpoint, average or weighted reconstruction is calculated.

## Scope, source and calculations

Primary analysis: observation years **2015 through the year before each April
reorganisation**. The reorganisation year is also inspected as a separately
labelled transition supplement, so neither interpretation of "until" is omitted.
Annual pay relates to the tax year ending 5 April, not a calendar-year mean;
a 1 April reorganisation is not evidence that almost all annual earnings were
measured under the successor's organisation or geography.

Use the existing Task 009.2 `2026-11-21-task009-2` processed ASHE snapshot,
`observations.parquet`, with its immutable manifest. Read **17 editions** covering
2015-2023, preserving provisional/revised editions separately. This includes the
sole retained 2015 revised edition. Independently verify the original pay/CV
cells in the existing Task 009.1 immutable ZIPs and the stored workbook hashes.
Source publisher: Office for National Statistics; [Table 8 source URL](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8).
This is a link to the established source, **not a new download**. Existing OGL
attribution/access findings in Tasks 009.1/014.2 apply; no source acquisition,
new Nomis query or automated ONS request occurred. Official legislation and
ministerial source descriptions were checked through web search; no boundary
shapefiles or new statistical source files were acquired.

The unchanged definition is **residence-based Table 8.7a, All, median column D,
gross annual pay, all employee jobs, both sexes, full- and part-time, GBP/year**.
Retain adult-rate/job-tenure eligibility, native notes, paired 8.7b CVs, original
row/code/name, style, suppression marker and publication vintage. Existing
2022 revised/2023 provisional population-note conflicts remain flagged; no
absence rule, numerical adjustment or exclusion policy is invented here.

For each authority/year/**edition**, take only its specified predecessor rows:
`minimum = min(numeric predecessor medians)`; `maximum = max(...)`;
`span GBP = maximum - minimum`; `span % = 100 * span GBP / minimum`.
The denominator is the lowest published median, not a pooled or mean salary.
Unrounded numerical results are retained in JSON; table display rounds to two
decimals. Counts and missing/suppressed identities are retained explicitly.

- **Complete:** every expected district has a numeric published median in that
  edition. This is numeric coverage, not certified historical geographic or
  statistical comparability, representativeness or precision.
- **Partial observed subset:** at least two medians, but one or more expected
  rows absent or non-numeric. Displayed extrema/span describe only observed
  districts and are not a definitive full-area range.
- **Unassessable:** fewer than two numeric medians. A single median can be shown
  as the observed min/max, but span/percentage are left null, rather than a
  misleading zero. With zero numeric medians all extrema are null.
- **Suppressed:** the preserved pay marker `x`; existing ONS notes identify
  unreliable estimates (CV above 20%). This is distinct from a predecessor row
  absent from a later-geography edition. An absent code is not proof that no
  historical estimate was ever published. All observed nonnumeric predecessor
  pay markers in this analysis are `x`; other source markers are not recoded.

## Verified predecessor membership and intermediate history

The research roster is [predecessors.json](predecessors.json), with legal URLs,
provisions, names and exact source codes. It is an audit grouping specification,
**not production mapping logic or an approved harmonisation contract**.
Bournemouth and Poole were already unitary authorities: the term predecessor
here includes them, not just non-metropolitan districts. County totals are
excluded from constituent lists to avoid double counting.

| Successor / code | Effective date | Historical district/unitary constituents | Official evidence |
|---|---|---|---|
| Bournemouth, Christchurch and Poole (`E06000058`) | 2019-04-01 | Bournemouth (`E06000028`); Christchurch (`E07000048`); Poole (`E06000029`) | [Order](https://www.legislation.gov.uk/uksi/2018/648/pdfs/uksi_20180648_en.pdf) |
| Dorset (`E06000059`) | 2019-04-01 | East Dorset (`E07000049`); North Dorset (`E07000050`); Purbeck (`E07000051`); West Dorset (`E07000052`); Weymouth and Portland (`E07000053`) | [Order](https://www.legislation.gov.uk/uksi/2018/648/pdfs/uksi_20180648_en.pdf) |
| Buckinghamshire (`E06000060`) | 2020-04-01 | Aylesbury Vale (`E07000004`); Chiltern (`E07000005`); South Bucks (`E07000006`); Wycombe (`E07000007`) | [Order](https://www.legislation.gov.uk/uksi/2019/957/made) |
| North Northamptonshire (`E06000061`) | 2021-04-01 | Corby (`E07000150`); East Northamptonshire (`E07000152`); Kettering (`E07000153`); Wellingborough (`E07000156`) | [Order](https://www.legislation.gov.uk/uksi/2020/156/pdfs/uksi_20200156_en.pdf) |
| West Northamptonshire (`E06000062`) | 2021-04-01 | Daventry (`E07000151`); Northampton (`E07000154`); South Northamptonshire (`E07000155`) | [Order](https://www.legislation.gov.uk/uksi/2020/156/pdfs/uksi_20200156_en.pdf) |
| Cumberland (`E06000063`) | 2023-04-01 | Allerdale (`E07000026`); Carlisle (`E07000028`); Copeland (`E07000029`) | [Order](https://www.legislation.gov.uk/uksi/2022/331/body/made) |
| Westmorland and Furness (`E06000064`) | 2023-04-01 | Barrow-in-Furness (`E07000027`); Eden (`E07000030`); South Lakeland (`E07000031`) | [Order](https://www.legislation.gov.uk/uksi/2022/331/body/made) |
| North Yorkshire (`E06000065`) | 2023-04-01 | Craven (`E07000163`); Hambleton (`E07000164`); Harrogate (`E07000165`); Richmondshire (`E07000166`); Ryedale (`E07000167`); Scarborough (`E07000168`); Selby (`E07000169`) | [Order](https://www.legislation.gov.uk/uksi/2022/328/made) |
| Somerset (`E06000066`) | 2023-04-01 | 2015-2018: Mendip (`E07000187`); Sedgemoor (`E07000188`); South Somerset (`E07000189`); Taunton Deane (`E07000190`); West Somerset (`E07000191`); from 2019: Mendip (`E07000187`); Sedgemoor (`E07000188`); South Somerset (`E07000189`); Somerset West and Taunton (`E07000246`) | [Order](https://www.legislation.gov.uk/uksi/2022/329/pdfs/uksiem_20220329_en.pdf) |
| East Suffolk (`E07000244`) | 2019-04-01 | Suffolk Coastal (`E07000205`); Waveney (`E07000206`) | [Order](https://www.legislation.gov.uk/uksi/2018/640/made) |
| West Suffolk (`E07000245`) | 2019-04-01 | Forest Heath (`E07000201`); St Edmundsbury (`E07000204`) | [Order](https://www.legislation.gov.uk/uksi/2018/639/made) |

Important geographic distinctions:

- Dorset comprises the five listed districts, **excluding Christchurch**.
  Christchurch belongs to BCP. The former Dorset county included Christchurch
  and cannot serve as the new Dorset comparator. This preserves Task 014.2's
  warning about newer Nomis families carrying old county values.
- Buckinghamshire excludes Milton Keynes; North Yorkshire excludes York;
  Somerset excludes North Somerset and Bath and North East Somerset. Cumbria's
  two successors are disjoint district groups, not the whole old county each.
- [Somerset West and Taunton, SI 2018/649](https://www.legislation.gov.uk/uksi/2018/649/pdfs/uksiem_20180649_en.pdf)
  joins Taunton Deane and West Somerset from **1 April 2019**, on their combined
  footprint. The calendar-date roster therefore uses five districts through
  2018 and four in 2019-2022. The **2018 revised** source already uses the later
  four-district partition. It gets a separate `later_roster_source_vintage_supplement`
  row, rather than silently replacing the missing two old districts or counting
  both old and merged units. Its complete four-part span is 6.65%, compared with
  23.88% for the five-part 2018 provisional partition; different editions and
  aggregation levels preclude interpreting this as earnings convergence.
- Statutory predecessor membership/dates are independently supported by the cited
  Orders. The West Suffolk membership/date is additionally corroborated by the
  [8 February 2018 ministerial statement](https://questions-statements.parliament.uk/written-statements/detail/2018-02-08/hcws462).
  Names/codes are cross-checked against original source rows. Electoral ward
  changes alone are not treated as district perimeter changes. No polygon
  overlay, exhaustive search of every minor external boundary adjustment or
  proof of a constant source geography in every year has been performed.
  That geographic-certification limit remains under ISS-003; no unapproved
  mapping/adjustment is used to bypass it. Decisions A/B1 are unchanged.

## Comparison across all 11 authorities

The **full authority/year/edition table** is [ranges-by-edition.md](ranges-by-edition.md):
minimum, maximum, GBP/percentage span, valid/expected count, coverage class,
explicit suppressed codes/markers and absent codes for all 142 research records.
[Machine-readable evidence](range-evidence.json) provides each original source
value/CV/style, source row, workbook/cell, edition URL/hashes and comparator.
No provisional/revised mixing or selection of the more favourable spread.

Summary below uses complete **calendar-date, pre-reorganisation** editions only.
Ranges in the final two columns are the smallest/largest observed spans across
those complete editions, not confidence intervals, a cross-year pooled sample,
or universal bounds. Edition counts include two publications for many years;
their observations are not statistically independent. A year listed as complete
has at least one complete edition, not necessarily a complete revised edition.

| Authority | Pre-reorganisation years | Complete editions / inspected | Years with any complete edition | No complete edition in any retained vintage | Complete-edition spans GBP | Complete-edition spans % of minimum |
|---|---|---:|---|---|---:|
| Bournemouth, Christchurch and Poole | 2015-2018 | 4/7 | 2015, 2017, 2018 | 2016 | 1,159-2,911 | 5.43-14.03 |
| Dorset | 2015-2018 | 3/7 | 2016, 2018 | 2015, 2017 | 2,249-7,980 | 11.15-47.36 |
| Buckinghamshire | 2015-2019 | 5/9 | 2016, 2018, 2019 | 2015, 2017 | 5,869-6,973 | 21.83-27.93 |
| North Northamptonshire | 2015-2020 | 9/11 | 2015, 2016, 2017, 2018, 2019 | 2020 | 5,053-7,169 | 23.26-37.91 |
| West Northamptonshire | 2015-2020 | 5/11 | 2015, 2017, 2018 | 2016, 2019, 2020 | 3,162-6,931 | 13.78-32.32 |
| Cumberland | 2015-2022 | 5/15 | 2015, 2019, 2021 | 2016, 2017, 2018, 2020, 2022 | 5,031-11,395 | 24.04-53.29 |
| Westmorland and Furness | 2015-2022 | 10/15 | 2015, 2016, 2019, 2020, 2021, 2022 | 2017, 2018 | 2,846-6,631 | 12.99-34.11 |
| North Yorkshire | 2015-2022 | 4/15 | 2017, 2021 | 2015, 2016, 2018, 2019, 2020, 2022 | 7,361-9,055 | 42.14-45.22 |
| Somerset | 2015-2022 | 8/15 | 2018, 2019, 2020, 2021, 2022 | 2015, 2016, 2017 | 1,408-4,115 | 6.54-23.88 |
| East Suffolk | 2015-2018 | 3/7 | 2016, 2018 | 2015, 2017 | 4,043-7,215 | 19.60-39.76 |
| West Suffolk | 2015-2018 | 5/7 | 2016, 2017, 2018 | 2015 | 2,574-3,699 | 11.17-17.14 |

Across **65 authority-years**, 37 have at least one complete retained edition
and **28 have no complete edition**. Across **119 primary edition records**,
61 are complete, 41 partial and 17 unassessable. There are 56 suppressed
predecessor mentions and 42 absent-row mentions across these edition records;
these are repeated publication/authority observations, not unique districts.
The 22 transition-year edition records all have zero predecessor rows under
the original roster in the retained sources. Successor-geography publication
has replaced those rows; this is not evidence that the predecessor employees
or their historical earnings ceased to exist. The extra Somerset 2018
later-roster record brings the total to **142** (62 complete, 41 partial,
39 unassessable including transition supplements).

Interpretation of relative differences, without adopting thresholds:

- BCP and West Suffolk have relatively narrow complete-edition spreads compared
  with most investigated groups. BCP still reaches 14.03% in 2018, and neither
  has complete coverage in every year; narrow does not mean negligible.
- Somerset's four-part 2019-2022 complete spans are 6.54-12.33%, but its complete
  five-part 2018 predecessor roster spans 23.88%. The internal merger can conceal
  heterogeneity, so it must not be used to infer stability of the earlier five units.
- Buckinghamshire (21.83-27.93%), North Northamptonshire (23.26-37.91%),
  West Northamptonshire (13.78-32.32%) and Westmorland and Furness
  (12.99-34.11%) have appreciable complete-edition spreads with substantial
  gaps or variation. No project tolerance for these differences is approved.
- Cumberland, Dorset, North Yorkshire and East Suffolk exhibit particularly
  wide complete spreads. Dorset reaches 47.36% in 2018, East Suffolk roughly
  39.5-39.8% in 2016. North Yorkshire's few complete editions span over 42%.
  These are not good evidence for a blanket assumption of similar predecessor
  earnings. Survey noise may contribute; the analysis does not attribute all
  spread to actual population differences.

Illustrative source checks: Cumberland 2015 medians are Allerdale ?19,534
(CV 9.5%), Carlisle ?19,534 (15.0%) and Copeland ?29,127 (17.0%), yielding
?9,593 / 49.11%. Its 2018 provisional published values are Allerdale ?22,724
and Carlisle ?21,428, with Copeland `x`: the ?1,296 / 6.05% observed subset
cannot establish a narrow full range. North Yorkshire 2017 revised spans
Craven ?17,468 (CV 11.0%) to Selby ?24,829 (9.8%), ?7,361 / 42.14% with all
seven numeric. These CVs remain uncertainty evidence, not automatic exclusions.

## Opportunities to validate a future approximation

No candidate reconstructed median is calculated, so **no approximation error,
bias, accuracy, predictive usefulness or acceptable tolerance is estimated**.
The following are benchmark opportunities, with explicit pairing limits:

| Official comparator | Complete-predecessor overlap found | Potential use / limitation |
|---|---|---|
| Same-edition county median for Buckinghamshire | 2016 provisional/revised, 2018 provisional/revised, 2019 provisional | Stronger same-publication check on the county footprint; new district coterminosity is supported by SI 2019/957. Earlier source vintages/geography still need verification for the eventual target. |
| Same-edition North Yorkshire county median | 2017 provisional/revised; 2021 provisional/revised | Same-population concept and year/edition; SI 2022/328 supports coterminosity. Only two complete years; incomplete years cannot validate full-predecessor approximations. |
| Same-edition Somerset county median | 2018 provisional five-part roster; 2019-2021 provisional/revised; 2022 provisional | SI 2022/329 supports county/new-district coterminosity. Keep the distinct 2018 revised four-part supplementary comparison separate. |
| ONS ad hoc 11165, explicitly April 2019 boundaries | BCP 2015/2017; Dorset 2016; East Suffolk 2016; West Suffolk 2016/2017 | Six authority-years, 11 predecessor-edition pairings; compatible field and verified combined footprint. Different publication/processing vintage means not a clean same-estimator validation experiment. Other special-extract years have incomplete predecessor inputs. |
| New-authority row in another edition of the same observation year | Seven complete-predecessor edition pairs: four 2019 authorities in 2018, Buckinghamshire in 2019, Westmorland and Furness/Somerset in 2022 | Exploratory overlap only. Revisions and geography can change together. No clean within-edition full predecessor/successor pair was found for these new identifiers. North Northamptonshire/Cumberland cases remain partial. |

All 17 complete primary same-edition county pairings and 11 complete special
cross-publication pairings lie inside their observed predecessor interval;
so do the seven complete cross-edition new-authority pairs. The Somerset
later-roster supplement contributes one further same-edition county check.
These counts repeat years/editions and are **not independent validation cases**.
Inside-range is only a coarse consistency observation; it does not identify
where a combined median lies, prove an averaging rule, or validate an
approximation. Same-edition county medians are existing official observations,
not reconstructed outputs. Whenever suitable official combined-area history
exists, owner review should consider that evidence before commissioning
reconstruction. Reusing or selecting it still requires the established
geography/vintage policy; this research does not implement that choice.

## Limitations and conclusion for owner consideration

A combined distribution depends on employee-job population weights and the
**full earnings distributions**, not just component medians. Arithmetic or
job-weighted averaging of medians does not recover its median. Counts in these
workbooks are indicative rounded weighted jobs, not reliable unweighted sample
sizes; no weights or combined statistic are constructed here.

For ideal consistently defined component distributions, their medians can
inform a pooled distribution's broad location, but **published ASHE point
estimates are not guaranteed deterministic bounds** for the independently
estimated combined median. Sampling error, weighting/calibration, imputation,
nonresponse, eligibility and geographic/vintage differences matter. A predecessor
range is neither a confidence interval nor an estimate of approximation error.
Marginal CVs do not give the joint covariance or a combined confidence interval;
no statistical test, confidence-bound construction or significance claim is made.
Even complete data can be noisy (for example the listed Cumberland CVs), while
suppression is unlikely to be an ignorable random subset for this comparison.

The report retains every relevant edition. Comparing revised combined estimates
with provisional predecessors can mix both population assignment and numerical
revision. Current retrieval/publication labels do not establish original
point-in-time availability, and ad hoc 11165's January 2020 publication cannot
be assumed available in 2015. The retained 2020-2022 survey disruption and
population-note flags remain material; do not treat the ranges as a homogeneous
longitudinal series or use them to alter the approved earnings variable.

**Conclusion:** further investigation is justified for a limited, owner-reviewed
question about gaps that official combined-area evidence cannot already cover.
BCP and West Suffolk, and Somerset's later four-part partition, offer comparatively
narrow complete cases and some benchmark opportunities. The larger spreads and
28 incomplete authority-years argue against a single unqualified approximation
for all 11. Before any proposed method could be assessed, it would need a
separately approved definition, geography/vintage-aligned benchmark design and
uncertainty/tolerance criteria. No method, threshold, source vintage, imputation,
feature or reconstructed production median is selected or approved here.

## Reproduction, verification and dependencies

From this worktree, using the existing project environment (no new dependencies):

```powershell
uv run python reports/data_audits/014.3/analyse_ranges.py --source-root PATH_TO_EXISTING_SOURCE_CHECKOUT
uv run python reports/data_audits/014.3/validate_ranges.py --source-root PATH_TO_EXISTING_SOURCE_CHECKOUT
```

The source checkout must already contain Task 009.2's immutable processed
snapshot and Task 009.1's retained raw bundles. This is an offline requirement;
missing files must not trigger acquisition. The first script reads those files
and writes only this audit directory's research evidence/table/validation files.
The second independently recalculates every range from the ingested table with
pandas and checks counts, roster dates, missing identities and original source
fields. On this machine the parent checkout's existing environment is used via
`uv --cache-dir .uv-cache run --no-sync python` with the script path and
`--source-root .`; filesystem-read escalation was needed for protected retained
bundles. No network access is implemented in either research script.

[Validation evidence](validation-evidence.json): 17 immutable ZIP editions and
both annual pay/CV member hashes verified; **1,066 direct raw pay/CV cell checks**
for 533 original source rows. All 142 ranges independently reconciled to the
existing ingestion; marker/CV/style/row identity and comparator pairing checks
pass. All four existing processed snapshot files, including manifest, remain
unchanged. The initial broad uniqueness check encountered expected uncoded
aggregate rows and was narrowed to the selected nonempty source codes without
removing any data; no duplicate selected geography was found. No production
tests are needed/run for this offline research-only change. Final documentation,
security, scope, preservation and Git checks are recorded in the task receipt.

ISS-003/004/011/012: **proceed with documented limitations**, preserving geography,
availability, survey-quality and incomplete-coverage evidence; none needs a new
methodological choice for this descriptive analysis. ISS-022 remains Open and
blocks new automated ONS acquisition, which was not attempted. ISS-020 remains
Open for the separate public-release security checkpoint; repository remains
private. No issue is resolved and no new overlapping issue is required.
Decisions A/B1, production code/configuration/datasets, pinned geography and
previous research evidence are unchanged. Stage journal records the event and
links here; the archive retains the prompt and execution CSV the measured time.
Research branch: `research/014-3-ashe-predecessor-ranges`, based on merged PR #14
main `a8bc21c9a0c95e379f2fc1c61efa39b866985b35`. Independent review before merge.

Final reproducibility check: both offline scripts rerun successfully; the
numerical JSON, full range table and initial validation artifact reproduce
byte for byte. Repository documentation/security/scope checks pass. Final
review URL and measured timing are recorded in the task archive/shared CSV.
