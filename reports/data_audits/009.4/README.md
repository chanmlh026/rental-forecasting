# Task 009.4: Nomis UMB production ingestion

**PASS WITH CONDITIONS.** Source-level ingestion and validation passed; this is
not a harmonised or model-ready panel. See the [task archive/report](../../../docs/009.4-nomis-umb-unemployment-ingestion.md)
for authorisation, execution history and limitations.

## Reproduce

Run from the clean repository root with the existing uv environment:

```powershell
uv run pytest
uv run python reports/data_audits/009.4/validate_ingestion.py
```

The offline audit requires the ignored official Task 009.3 response bundles and
Task 009.4 production snapshot already present in this checkout. A fresh clone
needs those source files acquired/verified through ingestion; the lightweight
Git evidence does not substitute for datasets. For the retained snapshot:

```powershell
uv run python -m ingestion.nomis_umb --snapshot-id 2026-11-22-task009-4 --source-cache data/raw/umb-009-3-investigation
```

The audit replaces the downloader with a failing stub for its production rerun;
any attempted network use fails. Its checksums cover all 342 clean-checkout data
files. The successful audit compares 51,504 full primary records and processed
measure fields, all 87 periods' coverage, and 592 rate/confidence cells from the
independently requested latest-period source. Seven validated/processed tables
also agree. No source bytes or production outputs were changed for ISS-021.

## Evidence and the original audit failure

- `validation-failure.json` is the preserved original failed-check receipt.
- `preservation-before.json` records all 290 files present before production ingestion.
- `resumption-preservation-before.json` records the subsequent 342-file snapshot
  plus the two original JSON evidence hashes; the corrected audit verifies them.
- `validation-evidence.json` records the passing corrected audit and offline rerun.
- `security-validation.json` records project-source/history scans and raw HTTP
  metadata checks. Ignored third-party dependency findings from the initial broad
  scan are disclosed separately; no suppressions were added to the source scan.

The independent latest query requested ITEM 1 **and** ITEM 2, with MEASURES 20100
and 20701 for each. ITEM 1 is unemployment count; ITEM 2 is unemployment rate.
The failed key omitted ITEM, and the failed equality included request-local
sort orders, record count and offset. The corrected key is
`(DATE_CODE, GEOGRAPHY, ITEM, MEASURES)`. ITEM 2 is selected explicitly; all
non-request fields (including GSS code/name/family, reference label, URN, original
value and source flags) must agree exactly. Only DATE/GEOGRAPHY/ITEM/MEASURES
SORTORDER fields and RECORD_COUNT/OFFSET are excluded from cross-request equality.
Request identity, response checksums, provenance, within-response completeness,
unique keys and sequential offsets are validated separately. Count rows remain
unchanged in the research evidence and are explicitly reported as excluded.

Regression tests in `tests/test_nomis_umb_audit.py` cover the exact mixed-item
failure, request-local differences, altered values/flags/URN/geography/period,
missing confidence, duplicate observations and invalid provenance/pagination.

## Coverage and remaining conditions

The fixed approved history contains 87 overlapping annual periods, January?December
2004 through July 2025?June 2026, released quarterly. All 296 source areas are
retained; 292 match the approved cohort exactly. Across periods there are 281?292
numeric matched rates and 273?274 numeric matched confidence margins. Latest:
292 matched numerical rates and 273 confidence margins. Q means source missingness;
OBS_CONF is a confidentiality flag. Confidence gaps do not invalidate rate values.

Barnsley and Sheffield source codes E08000016/E08000019 differ from target
E08000038/E08000039. City of London and Isles of Scilly remain outside the target
cohort but are retained source observations. No recoding, imputation or threshold
filtering is applied. Historic publication metadata includes placeholders,
non-month-end period fields and inconsistent revision labels. Source release
timestamps retain their original unverified timezone; no first-publication,
fixed-lag or model-input vintage claim is made. Separate M01 archives are excluded.
