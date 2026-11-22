# Task 014.6: planning geography and retained-data allocation

Research dated 22 November 2026. **Partial geography verification; source audit
complete for the stated measures and period.** The owner confirmed that no
lookup is retained and authorised completing the investigation with available
evidence while preserving ISS-022. No ONS lookup, mirrored data endpoint or
additional dataset was acquired. No planning counts were added, allocated or
imputed. Independent review is required.

## Result and interpretation

The 271 modern-code gaps in Task 012 are exactly the 11 successors' quarters
before their creation. Every gap has a full statutory predecessor roster with
numeric values for each of the four measures inspected. This establishes
**271 numerical recovery candidates**, not 271 geographically verified recoveries.
National parks and development corporations make several council returns partial
LA totals. Their shared totals cannot simply be added to each affected LA.

Official documents identify **49 current non-coterminous cases**: three LAs split
between a council and a body wholly within that LA, and 46 LAs with a cross-LA
planning body. The other **245 relationships remain Unresolved**. This is a
documented subset, not an exhaustive certified lookup. **Zero Direct cases are
certified by the evidence available here**; that does not mean that zero LAs are
actually coterminous. The exact coterminous total cannot be established under
the present evidence restriction. National Park/borough membership documents
establish relationships, not surveyed polygon equality with the PIPR reference.

For each of 13,524 LA-quarters (294 × 46), the four selected measures have the
same classification totals:

| Classification | LA-quarters per measure | LA-quarter-measure rows, four measures |
|---|---:|---:|
| Direct, verified coterminous | 0 certified | 0 |
| Additive, documented partition and numeric inputs | 41 | 164 |
| Allocation required, documented cross-LA total | 420 | 1,680 |
| Missing, no required observation identified | 0 | 0 |
| Unverified, insufficient geography/history | 13,063 | 52,252 |
| Total | 13,524 | 54,096 |

Thus **41 LA-quarters have a verified numerical addition opportunity** within
the documentary scope below; **13,483 remain unresolved for whole-LA use**
(420 allocation cases plus 13,063 unverified). None of the 271 successor-code
gaps is claimed recovered through verified addition. Zero Missing applies only
to the four selected measures/candidate records, not every field or territory.
No source is approved for production by this assessment.

## Sources and boundary verification

The [ONS April 2025 lookup catalogue](https://www.data.gov.uk/dataset/b07e6300-d9a5-43d6-a3d8-666496eb6991/local-planning-authority-to-local-authority-district-april-2025-lookup-in-the-uk)
describes the 1 April 2025 reference and fields `LAD25CD`, `LAD25NM`, `LAD25NMW`,
`Coterm`, `LPA25CD`, `LPA25NM`, `LPA25NMW`. Its catalogue dates and available
formats establish existence, not row contents, Coterm coding semantics or
historical compatibility. The lookup itself was not requested, including through
ArcGIS, a preview or a mirror. No local version was found; the owner confirmed
none is available. Obtaining the verified lookup remains a prerequisite for
certifying the remaining relationships. Even that current lookup would not
establish every historical quarter's responsibilities or original ID crosswalk.

The retained planning files use council GSS codes and E26/E51 special-body IDs.
These are not silently equated with the lookup's LPA25CD or planning.data.gov.uk
E600 identifiers. Documentary associations use explicit official names/areas,
linked to unchanged source identities. The PIPR cohort is the pinned April 2025
reference's 294 eligible rows; City of London and Isles of Scilly remain excluded.
Decisions A/B1 and Issue E are preserved. B1 remains the owner-approved minor
boundary treatment, not evidence that source returns have already been transformed.

[MHCLG PS1/PS2 guidance](https://www.gov.uk/government/publications/district-planning-matters-return-ps1-and-ps2/ps1-and-ps2-district-planning-matters-return-guidance-notes)
distinguishes council, park and corporation returns and excludes park/corporation
handled applications from council returns. Administrative delegation on behalf
of a park does not create a second independent set of applications. County matters,
prior approvals and other categories have separate definitions. This assessment
does not turn district application/decision counts into dwelling-unit permissions.

## Documented non-coterminous relationships

The complete 294-row index is [latest-la-relationships.csv](latest-la-relationships.csv.gz).
All 49 documented cases and native associated reporting codes follow. Each row
also includes the council's own code. This is a current documentary relationship
assessment, not a claim that the unavailable April 2025 lookup has been verified.
Official evidence URLs, scope and qualified historical intervals are in
[official-relationships.json](official-relationships.json).

| LA | LA code | Relationship | Associated native LPA reporting codes |
|---|---|---|---|
| Hartlepool | E06000001 | Split within one LA | E06000001;E51000007 |
| Middlesbrough | E06000002 | Split within one LA | E06000002;E51000006 |
| Redcar and Cleveland | E06000003 | Shared | E06000003;E26000005 |
| Brighton and Hove | E06000043 | Shared | E06000043;E26000010 |
| Cheshire East | E06000049 | Shared | E06000049;E26000006 |
| Wiltshire | E06000054 | Shared | E06000054;E26000009 |
| Northumberland | E06000057 | Split within one LA | E06000057;E26000004 |
| Cumberland | E06000063 | Shared | E06000063;E26000011 |
| Westmorland and Furness | E06000064 | Shared | E06000064;E26000011;E26000012 |
| North Yorkshire | E06000065 | Shared | E06000065;E26000005;E26000012 |
| Somerset | E06000066 | Shared | E06000066;E26000002 |
| Derbyshire Dales | E07000035 | Shared | E07000035;E26000006 |
| High Peak | E07000037 | Shared | E07000037;E26000006 |
| North East Derbyshire | E07000038 | Shared | E07000038;E26000006 |
| Mid Devon | E07000042 | Shared | E07000042;E26000001 |
| North Devon | E07000043 | Shared | E07000043;E26000002 |
| South Hams | E07000044 | Shared | E07000044;E26000001 |
| Teignbridge | E07000045 | Shared | E07000045;E26000001 |
| West Devon | E07000047 | Shared | E07000047;E26000001 |
| Eastbourne | E07000061 | Shared | E07000061;E26000010 |
| Lewes | E07000063 | Shared | E07000063;E26000010 |
| Wealden | E07000065 | Shared | E07000065;E26000010 |
| East Hampshire | E07000085 | Shared | E07000085;E26000010 |
| New Forest | E07000091 | Shared | E07000091;E26000009 |
| Test Valley | E07000093 | Shared | E07000093;E26000009 |
| Winchester | E07000094 | Shared | E07000094;E26000010 |
| Dartford | E07000107 | Shared | E07000107;E51000003 |
| Gravesham | E07000109 | Shared | E07000109;E51000003 |
| Lancaster | E07000121 | Shared | E07000121;E26000012 |
| Broadland | E07000144 | Shared | E07000144;E26000007 |
| Great Yarmouth | E07000145 | Shared | E07000145;E26000007 |
| North Norfolk | E07000147 | Shared | E07000147;E26000007 |
| Norwich | E07000148 | Shared | E07000148;E26000007 |
| South Norfolk | E07000149 | Shared | E07000149;E26000007 |
| Staffordshire Moorlands | E07000198 | Shared | E07000198;E26000006 |
| Adur | E07000223 | Shared | E07000223;E26000010 |
| Arun | E07000224 | Shared | E07000224;E26000010 |
| Chichester | E07000225 | Shared | E07000225;E26000010 |
| Horsham | E07000227 | Shared | E07000227;E26000010 |
| Mid Sussex | E07000228 | Shared | E07000228;E26000010 |
| Worthing | E07000229 | Shared | E07000229;E26000010 |
| East Suffolk | E07000244 | Shared | E07000244;E26000007 |
| Oldham | E08000004 | Shared | E08000004;E26000006 |
| Kirklees | E08000034 | Shared | E08000034;E26000006 |
| Barnsley | E08000038 | Shared | E08000038;E26000006 |
| Sheffield | E08000039 | Shared | E08000039;E26000006 |
| Brent | E09000005 | Shared | E09000005;E51000002 |
| Ealing | E09000009 | Shared | E09000009;E51000002 |
| Hammersmith and Fulham | E09000013 | Shared | E09000013;E51000002 |

The special-body code/name correspondence comes from unchanged source rows:
Dartmoor E26000001; Exmoor E26000002; Northumberland E26000004; North York Moors
E26000005; Peak District E26000006; Broads E26000007; New Forest E26000009;
South Downs E26000010; Lake District E26000011; Yorkshire Dales E26000012;
LLDC E51000001; OPDC E51000002; Ebbsfleet E51000003;
Middlesbrough E51000006; Hartlepool E51000007.

The [Dartmoor demographic report, section 2.1](https://www.dartmoor.gov.uk/__data/assets/pdf_file/0019/170542/Edge-Analytics-Demographic-Forecasts-Oct2016.pdf)
includes **Mid Devon** as well as South Hams, Teignbridge and West Devon; a
three-council assumption would miss an affected LA. The
[Peak District statement, Appendix 3](https://www.peakdistrict.gov.uk/__data/assets/pdf_file/0014/503051/Final-Statement-of-Community-Involvement-JAN24.pdf)
names nine district/unitary councils. County councils are not counted again as
district LAs. A separate park report's inconsistent constituent-count heading
is not used as a numerical authority. The
[Broads planning evidence, section 1.2](https://www.broads-authority.gov.uk/about-us/committees/archive-committee-papers-2025/planning-committee-meetings/planning-committee-05-december-2025/Local-Plan-for-the-Broads-Supporting-material.pdf)
explicitly distinguishes six district councils' territory outside the executive
area from the Broads Authority inside it. Other park sources and local council
evidence are linked individually in the relationship file, not inferred from names.

## Historical classification and addition opportunities

**Northumberland:** the [park planning statement](https://www.northumberlandnationalpark.org.uk/planning/)
places the separate planning authority wholly within the county; the
[adopted council plan](https://northumberland.moderngov.co.uk/documents/s9762/02.1%20Appendix%201%20-%20Northumberland%20Local%20Plan%20-%20FINAL%20ADOPTED%20VERSION%20WITH%20PHOTOS%20AND%20COVERS%20March%2020.pdf)
confirms the separate park/council territory. With MHCLG's exclusion rules,
the two returns form a documented partition for the selected district measures.
All required inputs are numeric for **2022 Q2–2026 Q2: 17 quarters**. The
conservative start is the first full quarter after adoption, not an inferred
boundary change. Earlier 2015–2022 Q1 observations remain Unverified pending
historical geography evidence. This is no independent polygon certification.

**Hartlepool and Middlesbrough:** the councils document transfer of planning
powers within their respective boroughs on 1 June 2023:
[Hartlepool](https://www.hartlepool.gov.uk/planning/hartlepool-development-corporation),
[Middlesbrough](https://www.middlesbrough.gov.uk/planning-and-development/middlesbrough-development-corporation/).
Both council/corporation pairs have numeric inputs for **2023 Q3–2026 Q2:
12 quarters each**. They support addition opportunities for the four measures.
2023 Q2 crosses the handover and remains Unverified; pre-handover coterminosity
is not certified merely from a council code. A source row beginning in Q2 is not
itself proof of a complete territorial partition over that entire quarter.

**Cross-LA corporations:** [City Hall OPDC documentation](https://www.london.gov.uk/about-us/organisations-we-work/old-oak-and-park-royal-development-corporation-opdc)
and dated planning statements support three boroughs from 2015 Q2; the
[Ebbsfleet Order](https://www.legislation.gov.uk/uksi/2015/747/made/data.xht?view=snippet&wrap=true)
and official planning-power statements support Dartford/Gravesham from 2015 Q3.
Their totals cannot be assigned to each borough. The
[Mayor's 2024/25 report](https://www.london.gov.uk/who-we-are/what-mayor-does/our-publications/mayor-londons-annual-report-2024-25)
records LLDC planning powers returning to Hackney, Newham, Tower Hamlets and
Waltham Forest on 1 December 2024. LLDC-related 2015 Q1–2024 Q3 observations
are Allocation required; transition 2024 Q4 and subsequent whole-LA verification
remain Unverified. Its retained 2024 Q4 return is not dropped or distributed.

Other shared park relations are classified Allocation required only for the
current assessment quarter, 2026 Q2. Earlier documentary memberships and source
rows are retained, but a complete dated jurisdiction ledger was not established;
earlier quarters stay Unverified. This deliberately understates historically
documentable allocation cases rather than projecting a current lookup backwards.
It does not imply earlier coterminosity. The
[Yorkshire Dales boundary extension](https://www.yorkshiredales.org.uk/about/about-the-national-park/history/boundary-extension/)
took effect on 1 August 2016; Lake District also expanded then. Lancaster's
inclusion cannot be projected into 2015. Reorganised counties/districts require
the statutory dated rosters as well as park boundary and reporting information.

## The 271 code-mismatch cases

| Successor | Code | Quarters without current code | Count |
|---|---|---|---:|
| Bournemouth, Christchurch and Poole | E06000058 | 2015 Q1–2019 Q1 | 17 |
| Dorset | E06000059 | 2015 Q1–2019 Q1 | 17 |
| Buckinghamshire | E06000060 | 2015 Q1–2020 Q1 | 21 |
| North Northamptonshire | E06000061 | 2015 Q1–2021 Q1 | 25 |
| West Northamptonshire | E06000062 | 2015 Q1–2021 Q1 | 25 |
| Cumberland | E06000063 | 2015 Q1–2023 Q1 | 33 |
| Westmorland and Furness | E06000064 | 2015 Q1–2023 Q1 | 33 |
| North Yorkshire | E06000065 | 2015 Q1–2023 Q1 | 33 |
| Somerset | E06000066 | 2015 Q1–2023 Q1 | 33 |
| East Suffolk | E07000244 | 2015 Q1–2019 Q1 | 17 |
| West Suffolk | E07000245 | 2015 Q1–2019 Q1 | 17 |
| Total, same 271 cases in each asset | | | 271 |

[Case-level evidence](historical-code-mismatches.csv.gz) retains each successor,
quarter and expected predecessor codes. The four-measure matrix adds original
predecessor source-record IDs, numeric/missing codes and geography evidence IDs.
Every expected predecessor is unique and numeric for these fields, including
Somerset's 2019 intermediate merger. Statistical numeric completeness is not
whole-LA territorial completeness. Dorset excludes Christchurch; East Suffolk
includes Broads territory; Somerset includes Exmoor territory; North Yorkshire
and the Cumbria successors involve cross-LA parks. Do not add a whole park total
to every successor or assume that an old county row is its successor footprint.
The [existing statutory roster](../014.3/predecessors.json) is reused unchanged.

## PS1/PS2 source observations and limitations

Both full files contain **15,001 authority-quarter rows** for these 46 quarters,
with identical authority-period rosters. The current quarter contains the 294
cohort councils plus 16 other bodies: the two excluded councils, ten parks/Broads
and four active corporations. LLDC is separately present historically. There
are no nonstandard/missing GSS identifiers inside this period. Across the full
retained histories, PS1 has 3,678 non-GSS rows and 30 collision/duplicate rows;
PS2 has 9,000 non-GSS rows and 1,905 collision rows. Their original identities
remain in Task 012; those earlier anomalies must not be deduplicated by this task.

Four detailed measures are assessed without changing definitions: PS1 Applications
received and Applications decided; PS2 Total granted, major dwellings (all) and
minor dwellings (all). The extra PS1 decision diagnostic is not a new approved
model feature. All **417 native count fields** (88 PS1, 329 PS2) also have
quarter-level numeric/missing availability counts across every retained authority
in scope. Other fields, including categories not collected in earlier periods,
must not inherit the four-measure Missing=0 result. The source's `..` is not zero.
PS1 is a summary of applications/actions; PS2 separates development/decision/time
categories. Some PS1 categories are excluded from PS2; cross-table equality must
use compatible definitions. Recent files overlap the full histories and are not
appended. Task 012's existing source comparison supports their separate audit role.

Current publication/retrieval dates are not historical availability. Retrospective
revisions and publisher imputation remain limitations (ISS-004/011); there is
no first-publication ledger, forecast cutoff policy or newly selected vintage.

## Practical options and remaining prerequisites

1. Obtain an approved retained copy of the lookup, or resolve ISS-022 before an
   affected acquisition. Verify Coterm semantics and E26/E51-to-LPA identifier
   relationships. Certify the 245 unresolved current relationships, then establish
   dated exceptions/changes before any Direct historical classification.
2. Review the 41 documented addition opportunities. Future implementation can
   sum only after confirming the approved measure, disjoint reporting and
   retained period/identity provenance. No numerical totals are calculated here.
3. Verify the 271 predecessor candidates against territorial reporting history.
   Several may ultimately be additive; cross-LA parks require within-LA breakdowns.
4. For shared totals, seek existing official application-location or LA-disaggregated
   evidence. Whole-body totals cannot be assigned using code matching. Area/population
   weighting would be an approximation with untested spatial application intensity;
   it requires separate owner approval and is not selected. Retain missing or
   unverified whole-LA observations if reliable allocation remains impossible.
5. Resolve transition quarters and delegated reporting explicitly; do not add an
   administering council's copy twice. Maintain source identity and vintage flags.

The overarching policy, A/B1 and Issue E remain unchanged. ISS-003/004/010/017/022
remain Open, alongside other existing quality/security restrictions. No new
overlapping issue or closure is needed. Source/units and rights gaps remain in
the existing register. No new policy decision is needed to report these findings;
particular approximations and material source/vintage decisions remain with the owner.

## Evidence and reproducibility

Audit tables use lossless gzip-compressed CSV to keep Git evidence small:

- [LA-quarter-measure classifications](la-quarter-measure-coverage.csv.gz):
  54,096 rows, source-record references and completeness indicators.
- [Native authority-quarter evidence](source-authority-quarters.csv.gz):
  30,002 rows, original selected tokens/names/codes/quarters/URLs/hashes and
  numeric/missing field counts. No reconstructed values.
- [All-field availability](all-field-quarter-availability.csv.gz):
  417 fields × 46 quarters; category missingness remains explicit.
- [Summary](assessment-summary.json), [documentary evidence](official-relationships.json),
  [current relationships](latest-la-relationships.csv.gz) and
  [independent validation](validation-evidence.json).

From an existing project environment, with the retained Task 012 snapshot and
raw bundles recovered locally, no network or new dependency is needed:

```powershell
uv run python reports/data_audits/014.6/assess_planning.py --source-root <retained-source-root>
uv run python reports/data_audits/014.6/validate_assessment.py --source-root <retained-source-root>
```

The independent validator parses the original CSV bodies with the standard-library
CSV reader, reconciles all selected tokens and per-row availability counts,
checks the full cohort/quarter grid and 271 gaps, and rechecks every input hash.
It independently checks source reconciliation and addition preconditions, **not
polygon geography or the unavailable lookup**. The source audit initially counted
numeric `F_Year` labels and a cohort-match metadata flag as count fields; independent checks caught this, the audit
restricted count fields to the explicit source contract and was rerun. Windows separator/BOM reader corrections changed
no source bytes. Original datasets and all earlier research remain untouched.
Production tests are not run for research-only changes; these source checks and
documentation/security/Git checks provide the relevant validation.

This branch derives from unmerged PR #16 at `a7a1474` to preserve the approved
Task 014.5 policy. It does not merge or modify PR #16. Review this task as a
dependent research PR targeting `research/014-4-cross-dataset-geography`; full geography certification remains unresolved. Original
prompt and owner continuation are in the [task archive](../../../docs/014.6-verify-planning-authority-geography-and-la-allocation.md).
