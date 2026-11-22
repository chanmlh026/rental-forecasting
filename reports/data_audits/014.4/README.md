# Task 014.4: cross-dataset historical geography

Research dated 22 November 2026; independent review required. No source selection,
geography mapping, statistical reconstruction or preprocessing policy is approved.

The retained official population and migration backcasts provide the clearest
opportunity to avoid reconstruction. Numerical histories also exist for all 11
authorities in HPI and the three PIPR bedroom targets, but the evidence reviewed
does not establish their historical footprints. These are verification priorities,
not evidence that approximation is necessary. Dwelling-unit permissions remain
an unresolved source gap. ASHE and UMB require source-family-specific treatment.

## Scope and interpretation

The exact 11 authorities and dated predecessor rosters come from the
[pinned Task 014.3 evidence](https://github.com/chanmlh026/rental-forecasting/blob/7d2ddf2b2efe1af27e4182348e41e150aae3b683/reports/data_audits/014.3/predecessors.json).
PR #15 remains unmerged at this task's final source review. Its research roster
is reused as evidence, not adopted as an approved production mapping. Somerset's
2019 intermediate merger is retained; Christchurch is excluded from successor
Dorset. Old Dorset county is not a compatible successor-Dorset footprint.
April 2025 reference geography, Decisions A/B1 and the approved cohort are preserved.
Household Growth, Student Population Share and national predictors are outside scope.

The assessment covers 2015–2026, including partial 2026 coverage where published.
There are 27 audited fields: earnings; UMB rate and confidence margin; population;
density; six migration components; stock; six housing-flow components; three
planning application fields and an explicit dwelling-unit gap; HPI price/index;
and the three bedroom rent targets. These are not 27 independent model features.

**C Confirmed:** official geography evidence supports the documented successor
footprint within these 11 authorities' structural history. This does not certify
polygon equality, every minor external boundary change, historical availability
or an approved model-input vintage. **U Unverified:** direct numeric observations
or an explicitly identified old-county candidate exist, but compatibility is not
established. **P Predecessor-only:** numeric former-authority observations exist,
possibly with partial predecessor coverage, without a suitable direct candidate.
**M Missing:** no suitable observation in the investigated source records/year.
**E Evidence gap:** suitable source availability or definition is unresolved.
Missing does not establish absence from every official publication.

A yearly classification means at least one qualifying numeric period/version;
it does not mean a complete year or that every retained vintage agrees. Fiscal
years use ending year; UMB uses the end year of overlapping rolling windows.
The detailed JSON retains native periods, numeric periods, original codes, source
markers, flags, publication dates, locators and source hashes. No vintages are
merged into a preferred series. The matrix is an evidence index, not an approved
training panel.

## Coverage comparison

The following compact table is generated from the evidence matrix. Years are
two-digit calendar/ending years. Migration here shows internal net; all six
components have the same yearly classifications. Supply shows net additions;
other components remain separate in the full matrix. Planning shows major
dwelling applications granted, not units. UMB confidence is separately audited.
See [all 27 authority-variable-year tables](coverage-by-year.md) and
[version-level evidence](coverage-evidence.json) for complete detail.

| Authority | ASHE | UMB | Population | Density | Migration | Stock | Supply | Planning apps | HPI | PIPR |
|---|---|---|---|---|---|---|---|---|---|---|
| Bournemouth, Christchurch and Poole | C15?17; U18?26 | U15?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?19; C20?25; M26 | P15?19; C20?25; M26 | P15?18; U19?26 | U15?26 | U15?26 |
| Dorset | C15?17; U18?26 | U15?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?19; C20?25; M26 | P15?19; C20?25; M26 | P15?18; U19?26 | U15?26 | U15?26 |
| Buckinghamshire | U15?26 | P15; U16?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | U15?20; C21?25; M26 | U15?20; C21?25; M26 | P15?19; U20?26 | U15?26 | U15?26 |
| North Northamptonshire | P15?19; U20?26 | P15?19; U20; P21; U22?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?21; C22?25; M26 | P15?21; C22?25; M26 | P15?20; U21?26 | U15?26 | U15?26 |
| West Northamptonshire | P15?19; U20?26 | P15?19; U20?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?21; C22?25; M26 | P15?21; C22?25; M26 | P15?20; U21?26 | U15?26 | U15?26 |
| Cumberland | P15?21; U22?26 | P15?21; U22?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?23; U24?25; M26 | P15?23; C24?25; M26 | P15?22; U23?26 | U15?26 | U15?26 |
| Westmorland and Furness | P15?21; U22?26 | P15?21; U22?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?23; U24?25; M26 | P15?23; C24?25; M26 | P15?22; U23?26 | U15?26 | U15?26 |
| North Yorkshire | U15?26 | P15?21; U22?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | U15?25; M26 | U15?23; C24?25; M26 | P15?22; U23?26 | U15?26 | U15?26 |
| Somerset | U15?26 | P15?21; U22?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | U15?25; M26 | U15?23; C24?25; M26 | P15?22; U23?26 | U15?26 | U15?26 |
| East Suffolk | C15?17; U18?26 | U15?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?19; C20?25; M26 | P15?19; C20?25; M26 | P15?18; U19?26 | U15?26 | U15?26 |
| West Suffolk | C15?17; U18?26 | U15?26 | C15?25; M26 | C15?25; M26 | C15?25; M26 | P15?19; C20?25; M26 | P15?19; C20?25; M26 | P15?18; U19?26 | U15?26 | U15?26 |

## Official-source findings

### Population, density and migration

The retained detail2025 schema explicitly describes April 2023 boundaries and
provides population history from 2011 and all six migration components from
2012 through 2025. All 11 authorities have numeric 2015–2025 observations on that
declared basis. The summary2025 density notes refer to April 2024 geography,
including the April 2023 reorganisations, with January 2025 Standard Area
Measurements. Edition-title/notes references to 2023/2024 are retained rather
than normalised. This supports the successor footprints at issue here, without
certifying unrelated boundary changes or a time-varying area denominator.
The [official population methods guide](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/populationestimatesforenglandandwalesqualityandmethodsguide)
describes revised historical series. The source's Barnsley/Sheffield year wording
does not replace Decision A's approved statutory reference.

Alternative retained 2022 detail files use 2021 and 2023 geographies; the older
version lacks the four 2023 unitary codes. They remain separate versions. The
declared later-geography history offers a route to official values without
adding predecessor counts. It does not establish availability at earlier forecast
origins. Latest population publications are 29 July 2026; older 2024/2023 editions
have 30 July 2025/15 July 2024 publication evidence. Ambiguous 2022 publication
references are retained as text with no invented single date. Five superseded
Task 010 files remain unacquired under ISS-022.

### ASHE and UMB

ASHE retains the approved residence, All employees, Table 8.7a median gross annual
pay definition. Task 014.2's special extract explicitly uses April 2019 boundaries:
12 pay observations for the four 2019 reorganised authorities in 2015–2017
therefore qualify as C in this structural-footprint assessment. Other numeric
current-code histories and Buckinghamshire/North Yorkshire/Somerset old-county
candidates remain U. This adds no new decision about those candidates or about
Task 014.3's median ranges. Suppressed values and CV evidence remain separate.
See the [existing ASHE investigation](../014.2/README.md); its source conclusions
and access incident are preserved rather than repeated or revised.

UMB retains item 2 rate (20100) and confidence margin (20701), not counts or a
different unemployment definition. Existing TYPE424 history and alternative
432/434/464 families were investigated. Three focused public Nomis requests
returned 1,248 rows: December windows 2015–2025 and June 2026, two measures.
They are samples of annual windows, not exhaustive alternative-family quarterly
histories. TYPE432 supplies North Northamptonshire rates of 3.4% (December 2020),
2.6% (December 2022) and 3.6% (December 2023), where the retained primary family
has gaps. December 2021 remains Q-missing in this sampled family. No whole-year
absence is inferred from one December window. Geography remains U; a new native
family ID does not establish a revised historical footprint. TYPE464 provides
predecessor evidence, not an approved combined rate.

The [Nomis reweighting notice](https://www.nomisweb.co.uk/articles/1433.aspx)
also requires retaining release/revision context. ONS local-statistics calendar
year indicators, archived M01 and APS estimates differ in cadence, definition or
estimation and are not silent replacements. Query URLs, timestamps, safe headers,
HTTP status and hashes are in [access evidence](nomis-access-evidence.json).

### Dwelling stock and housing supply

Retained Table 123/122 cover notes name the 2019, 2020, 2021 and 2023
reorganisations and say previous-geography reporting is no longer collected.
Direct successor flow observations begin in fiscal years ending 2020, 2021,
2022 and 2024 respectively. These post-reorganisation periods qualify as C;
Table 123 remains the approved modelling flow source, while Table 122 is audit-only.
Predecessors and old-county candidates remain visible for earlier years.

Table 125 stock notes explicitly cover 2019–2021 reorganisations but do not
provide equivalent explicit 2023 evidence in the retained notes. The four 2023
successors' numeric 2024/2025 stock observations remain U. A matching new code
alone is insufficient. Old Buckinghamshire, North Yorkshire and Somerset county
rows are historical candidates, not adopted mappings. Old Dorset county includes
Christchurch and must not be substituted. Imputation, provisional/revision flags,
rounding and cross-table differences remain source facts; no reconciliation or
denominator timing is chosen. See [Task 011](../011/README.md) and
[official technical notes](https://www.gov.uk/government/statistics/housing-supply-net-additional-dwellings-england-2023-to-2024/housing-supply-net-additional-dwellings-england-2023-to-2024-technical-notes).

Other MHCLG stock tables and VOA council-tax stock warrant definition checks if
needed; council-tax units are a different statistical universe. No numerical
coverage or approved replacement is claimed for these alternatives.

### Planning

PS1 received applications and PS2 major/minor dwelling applications granted are
application/decision counts. Successor rows begin at reorganisation Q2. LPA
responsibilities can exclude national parks or involve development corporations;
whole-LAD compatibility is unverified even after reorganisation. These rows are U,
with predecessor evidence earlier. A quarter containing a reorganisation requires
its own period check. Full native histories/fields remain in [Task 012](../012/README.md).

All-residential LA dwelling units granted remain E for all 11 authorities and years.
Annual LAHS Section I affordable permissions are an official partial candidate,
but differ in scope; history, definitions, completeness and extract rights remain
unaudited. National Glenigan aggregates do not establish an accessible local
extract or its redistribution rights. ISS-010/017 remain Open. PS2 applications
cannot fill the units numerator and no planning intensity is calculated.

### HPI and PIPR targets

Both retained August/September 2026 HPI vintages contain all 11 current codes
through their release endpoints, with numeric historical prices and indices
from 1995. Within this assessment all 2015–2026 years have numeric observations.
The [February 2023 release notice](https://www.gov.uk/government/news/uk-house-price-index-for-february-2023)
documents the 2023 geography update; the
[HPI quality and methodology](https://www.gov.uk/government/publications/about-the-uk-house-price-index/quality-and-methodology)
describes postcode/NSPL assignment. Neither reviewed statement expressly
certifies the footprint of every retrospective month for these 11 authorities.
Price and index therefore remain U, not missing. The retained index reference
is January 2023=100; neither index aggregation nor transaction-price averaging
is an approved substitute. Price Paid Data have different scope/adjustment and
are not an interchangeable HPI history.

The retained October 2026 PIPR source has numeric 1-, 2- and 3-bedroom targets for
every authority from January 2015 through September 2026: 2026 is nine months,
not a complete year. Current-code/cohort consistency is verified. Per-year
boundary vintage remains unverified in the retained workbook and reviewed
[PIPR QMI](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/methodologies/priceindexofprivaterentsqmi)
and [detailed methodology](https://www.ons.gov.uk/economy/inflationandpriceindices/methodologies/priceindexofprivaterentsdetailedmethodology).
These targets remain U, a priority for verification before preprocessing.
Earlier IPHRP regional trends cannot establish LA-bedroom observations before
2015; PRMS has a different definition. Neither is selected as a substitute.

## Availability and possible aggregation

Observation period, geography date, source publication and retrieval are distinct.
Each source version records available publication evidence. The JSON labels
versions published after observation-year end as unavailable by that year end;
this is a diagnostic, not an approved historical forecast cutoff. Otherwise
availability is explicitly unverified. No actual forecast origins were supplied,
and complete first-publication archives are absent. Later backcasts must not be
treated as available earlier. ISS-004 remains Open.

Compatible, disjoint same-period population, stock and housing-flow counts might
be additive if no suitable official combined history exists. Definition,
geography, imputation and publication compatibility must first be checked.
Gross internal migration inflows/outflows cannot simply be added: movements
between predecessors become internal to the combined area. Net cancellation
also requires compatible accounting. Density is not additive; any population/area
derivation requires a compatible area basis and later approval. Planning counts
need LPA territorial checks. ASHE medians, UMB modelled rates/confidence, HPI
and PIPR are non-additive; averaging or weighting does not establish a valid
combined statistic. No reconstructed values are calculated here.

## Priorities for owner review

1. Verify PIPR target and HPI retrospective boundaries with explicit publisher
   documentation or an authorised clarification. Routine evidence gathering is
   technical work; any residual comparability assumption requires owner approval.
2. Review the documented population/migration/density backcasts as official-source
   candidates. The owner must select geographic/vintage and historical-availability
   policies before Codex can implement preprocessing.
3. Seek explicit old-county and 2023-stock boundary evidence before considering
   count aggregation. Approve any mapping, denominator timing or source substitution
   separately; retain Table 123/Table 122 roles.
4. Resolve UMB family geography and uncovered periods, and ASHE official combined
   candidates, before deciding whether further approximation research is needed.
   Non-additive estimation/uncertainty/tolerance decisions belong to the owner.
5. Resolve units-source availability and rights (ISS-010/017); do not replace units
   with applications or affordable-only counts. Obtain the approved ONS bot contact
   before any affected download (ISS-022). No contact or approval is inferred.

After those decisions, Codex can implement approved mappings, explicit vintage
selection and coverage checks in a separately authorised task. This PR approves none.

## Reproduction, access and validation

Run from an existing project environment; no dependencies or network are needed
for replay. Supply roots containing the named immutable snapshots and a checkout
of the pinned Task 014.3 membership evidence. Focused Nomis response bodies are
retained locally under `data/raw/geography-014-4/`, ignored by Git. Their hashes
and exact public URLs are recorded; replay deliberately fails if a required body
or snapshot is missing. No source values are silently regenerated by downloading.

```powershell
uv run python reports/data_audits/014.4/assess_coverage.py --source-root <retained-root> --source-root <other-retained-root> --membership-root <task0143-checkout>
uv run python reports/data_audits/014.4/validate_coverage.py --source-root <retained-root> --source-root <other-retained-root>
```

[Validation evidence](validation-evidence.json) records 3,564 unique classifications,
69 source versions, 6,927 version-level records, 26,857 native rows inspected and
22 unchanged hashed input files. The independent validator reconciles 11,682
native period records directly with source parquets and checks source references,
classification invariants, safe query metadata and manifests. Coverage counts
are not new statistical estimates. Full production tests are not required/run:
production logic, configurations and datasets are unchanged.

No automated ONS-host download was made in this task. Existing ONS files and
notes were inspected offline; indexed official documentation was consulted.
The three public Nomis requests used the existing approved dataset and statistical
definition, no credentials/cookies or access bypass, and returned HTTP 200.
Existing OGL/source-specific context is retained; this does not establish rights
for third-party planning microdata. ISS-020 private-context limitations remain.

Dependency outcome: proceed with documented limitations for research only.
ISS-003/004/009/010/011/012/017/020/022 remain Open; no new overlapping issue or
closure is warranted. ISS-022 blocks affected acquisition, not this offline audit.
Decisions A/B1 are unchanged. Task 014.3, all earlier evidence and unrelated dirty
Task 009.5 work are preserved. Submission is for independent review, not merge.
