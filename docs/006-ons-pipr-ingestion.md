# 006. ONS PIPR target ingestion

This document describes the initial local ingestion of the ONS Price Index of
Private Rents (PIPR) rent-level workbook. The pipeline does not create
features, forecast labels, training splits, or models.

## Approved source and cohort

- Dataset: [ONS Price Index of Private Rents, UK: monthly price statistics](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics)
- Initial source release: 21 October 2026
- Direct workbook: [official XLSX](https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics/21october2026/priceindexofprivaterentsukmonthlypricestatistics.xlsx)
- Workbook table identifier: `PIPR_Index_of_Private_Rents_UK_monthly_price_statistics`
- Approved geography: 294 English Local Authorities from the audited
  [April 2025 ONS LAD reference](https://www.arcgis.com/home/item.html?id=5779a9578f0e48ccacef6af41546b56b),
  pinned as `configs/ons_lad_apr2025_v2.csv`.
- Explicit exclusions: City of London (`E09000001`) and Isles of Scilly
  (`E06000053`). Other aggregate and non-English rows are excluded from the
  LA target panel. Unexpected English LA codes fail validation.
- Bedroom categories: 1, 2, and 3.
- Target measure: monthly average rent level in GBP, not a rent index or
  growth rate.

The project target remains `y(LA, bedroom, t) = Rent(LA, bedroom, t + 12
calendar months)`. This ingestion stores the historical rent observations
only; it does not generate 12-month labels or change the approved Option A
origin definition.

## Run the pipeline

From the repository root, download, validate, and ingest the approved release:

```powershell
uv run python -m ingestion.ons_pipr
```

Options:

```text
--release-id YYYY-MM-DD
--source-url URL
--workbook PATH
--config PATH
--geography-reference PATH
--connect-timeout SECONDS
--read-timeout SECONDS
--large-movement-warning-threshold-percent PERCENT
--expected-start-month YYYY-MM
--expected-end-month YYYY-MM
```

For another ONS edition, provide both its release identifier and the direct
official workbook URL. A local XLSX can be supplied with `--workbook` to
validate and transform it without a network download; the copied snapshot is
marked `local_file_copy` in source metadata. Supplying a release ID does not
prove that its edition date is an exact publication timestamp. When the URL is
a recognisable official ONS workbook URL, its edition folder is parsed and
must match `--release-id`. This is an identity consistency check, not proof of
the public publication time. Offline local-workbook ingestion remains
available with a local source label or fixture URL.

The reference release has fixed expected coverage of January 2015 through
September 2026. For any other release, `--expected-end-month` is required;
this makes the latest expected source month an explicit release-specific
confirmation rather than assuming that every edition includes the immediately
preceding calendar month. `--expected-start-month` defaults to `2015-01` and
can be changed when an official coverage change has been confirmed.

Storage uses the existing `configs/storage.toml`; no second storage
configuration was added. Relative `local_root` values resolve from the
repository root. The pipeline supports the configured local backend only.

## Storage layout and versioning

For a release ID of `2026-10-21`, the pipeline writes:

```text
data/
  raw/ons_pipr/release=2026-10-21/
    priceindexofprivaterentsukmonthlypricestatistics.xlsx
    source_metadata.json
  validated/ons_pipr/release=2026-10-21/
    rent_observations.parquet
    manifest.json
    validation_summary.txt
    missing_observations.csv
    missing_gap_sequences.csv
    large_rent_movements.csv
  processed/ons_pipr/release=2026-10-21/
    rent_observations.parquet
    manifest.json
    validation_summary.txt
    missing_observations.csv
    missing_gap_sequences.csv
    large_rent_movements.csv
    _SUCCESS.json
```

The original workbook bytes are copied/downloaded into a temporary release
directory, checked as a readable XLSX, checksummed, and atomically moved into
the raw release path. `source_metadata.json` records the exact URL, edition
date/identifier, UTC retrieval timestamp, file size, SHA-256, table, and
retrieval method. Existing raw snapshots are reused only after checking their
metadata, file integrity, workbook structure, release identifier, and source
URL. For a supplied local file, its bytes are also compared with any existing
snapshot. Different bytes cannot overwrite an existing release.

Validated and processed Parquet, manifests, reports, and audit CSVs are
prepared in a temporary directory under the configured data root. Both
Parquet files are read back and checked before their release directories are
promoted. Once both layers have been verified, `_SUCCESS.json` is written to
the processed directory with the release ID, raw checksum, and processed
manifest checksum. A hard validation failure writes a human-readable report
under `data/validation_reports/` and does not publish validated or processed
Parquet.

Re-running a completed release checks the immutable raw snapshot and both
manifests, their shared release/source metadata, Parquet checksums, schemas,
types, full 294-authority cohort, bedroom categories, unique keys, rent
validity, continuous monthly coverage, and equality of observations across
layers. This content check reads the Parquet files but does not reparse the
workbook. Matching outputs are reported as `reused`; corrupt, inconsistent,
or incomplete outputs fail closed.

The two output directories cannot be published atomically as one filesystem
operation. If a process stops after publishing one complete layer, a rerun
validates that survivor, regenerates the release in staging, and completes
only the missing layer when its manifest and checksum match the regenerated
release. It does not overwrite the surviving layer or delete arbitrary files.
A conflicting or malformed directory is an error, not a recovery candidate.
If both layers exist but the completion marker is absent, they are fully
verified before the marker is added. This marker and recovery protocol provide
detectable completion and safe rerun recovery, not cross-directory atomicity.
New release IDs have separate directories; newer source data does not silently
replace older vintages.

Data files are excluded from Git. The geography reference is a small,
versioned source input and is kept in Git so a run can reproduce the exact
294-code cohort without a live geography-service request.

## Output schema

`data/processed/ons_pipr/release=YYYY-MM-DD/rent_observations.parquet` has one
row per unique
`local_authority_code × bedroom_count × observation_month`:

| Column | Type | Meaning |
|---|---|---|
| `observation_month` | timestamp at month start | PIPR reference month |
| `local_authority_code` | string | Official GSS code |
| `local_authority_name` | string | Name from the pinned reference and checked against PIPR |
| `bedroom_count` | int8 | 1, 2, or 3 bedrooms |
| `average_monthly_rent_gbp` | float64 | Published average monthly rent level in GBP |
| `source_name` | string | `ONS PIPR` |
| `source_release_date` | timestamp/date at midnight | Source edition date, not a precise public availability timestamp |
| `source_vintage_id` | string | Stable release identifier |

The validated-layer Parquet has the same observation columns plus
`source_workbook_row` (int32) to aid source tracing. Files are sorted by
observation month, GSS code, and bedroom count. separate manifests record raw and Parquet checksums, row counts, observation coverage, geography reference version, validation
findings, movement counts, and transformation version. The
manifest sets `published_at` to null and explains that an edition date is not
treated as a verified availability timestamp.

## Validation behavior

Hard failures prevent publication of validated/processed Parquet:

- Invalid XLSX/ZIP, missing named table, inconsistent table metadata, or
  required headings absent or inconsistent with visible worksheet headings.
- Invalid or ambiguous monthly dates, area name/code mismatches, or new
  English local-authority codes outside the pinned geography reference.
- Null, non-numeric, non-finite, or non-positive target rents.
- Duplicate LA-bedroom-month keys.
- Missing target cells, missing approved authorities/bedroom categories,
  non-contiguous monthly coverage, an expected start/end coverage mismatch,
  or a reference-release coverage mismatch.
- Conflicting existing release bytes, bad checksums, or incomplete output
  releases.

The 21 October 2026 reference release is additionally checked against the
audited expectations: 294 authorities, 3 bedroom categories, 141 months
(January 2015–September 2026), and 124,362 positive observations. This exact
count/range is not imposed on later releases; they must still contain the
approved cohort and a complete, contiguous panel for the explicitly confirmed
coverage period. A legitimate ONS coverage change must be confirmed and
reflected in the expected bounds before ingesting that edition; the pipeline
does not infer that a change is official from an incomplete workbook.

Year-over-year rent movements at or above the configurable default 20%
threshold produce review warnings and do not automatically fail ingestion.
The summary displays at most 25 movements and reports the total flagged and
displayed counts. The manifest records the summary rows and counts, while
`large_rent_movements.csv` contains the full detail list. Missing observations
and gap sequences are exported separately; no target rents are imputed.

## Initial run results

The verified 21 October 2026 workbook was downloaded from the official ONS
URL on 24 October 2026. The resulting source and processed data were checked:

| Check | Result |
|---|---:|
| Raw workbook size | 18,807,933 bytes |
| Raw workbook SHA-256 | `0d79a0b23041b200748edc84526aff286379f59e2367aeeb57ebb8813517a73c` |
| Retrieved at (UTC) | `2026-10-24T17:18:57.402772+00:00` |
| Eligible English Local Authorities | 294 |
| Bedroom categories | 3 |
| Observation months | January 2015–September 2026 (141) |
| Processed rows | 124,362 |
| Missing target cells | 0 |
| Duplicate target keys | 0 |
| Null/non-positive values | 0 |
| Processed Parquet SHA-256 | `94e2cb2bd5da1797611fec26f7f82b534f1f8905f016a28d81251e09a67ce308` |
| Validation | Passed; 25 large movements flagged for review |

The second run reused the matching raw and processed release after verifying
the checksums.

## Revisions, publication timing, and geography limitations

ONS describes the newest two UK rent months as provisional and subject to a
two-month revision policy. The March 2024 archive and October 2026 workbook
also differ across many overlapping historical rent values; this ingestion
records release vintages but does not establish why those older values differ.
The current edition's retrospective values therefore must not be presented as
values that were available at historical forecast cutoffs.

`source_release_date` is the edition date only. The pipeline does not invent
`published_at` or `available_at`; point-in-time feature joins and exact
historical backtests require independently verified availability timestamps
and archived source vintages. Use **approximate retrospective backtesting**
when those records are unavailable. PIPR was first published in March 2024;
its historical monthly observations before then were not publicly available
at their observation dates.

The reference comparison is the April 2025 LA geography. This pipeline
preserves official source codes and does not remap historical boundary
changes. The Task 005.1 audit also found Barnsley and Sheffield absent from
the March 2024 archived workbook. The project cohort excludes City of London
and Isles of Scilly because the audited target workbook does not provide
their rent series.

## Tests

Run the full suite with:

```powershell
uv run pytest
```

The offline PIPR tests use generated minimal XLSX fixtures and do not require
ONS network access:

```powershell
uv run pytest tests\test_ons_pipr.py -q
```

They cover table extraction, long-format conversion, geography exclusions,
schema/date/rent failures, duplicate and missing-panel detection, reference
release checks, checksums, immutable releases, output failure behavior, and
Parquet round-tripping.
