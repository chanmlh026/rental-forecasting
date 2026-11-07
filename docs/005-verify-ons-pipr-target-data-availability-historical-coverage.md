# 005. Verify ONS PIPR Target Data Availability & Historical Coverage

## Role and Objective

Act as a senior UK economic data researcher, data engineer, and machine learning architect.

Your task is to investigate whether official Office for National Statistics (ONS) data can support the proposed rental forecasting target:

**Forecast the average monthly private rent, in GBP, 12 months ahead for each English Local Authority, separately for properties with 1, 2, and 3 bedrooms.**

This is a **data feasibility investigation**, not an implementation task.

Your conclusions must be supported by verifiable evidence from official sources. Do not assume that a dataset contains the required geographical, bedroom, and temporal breakdown simply because its title refers to private rents.

## 1. Review the Existing Project

Before conducting the investigation, read:

- README.md

- data-architecture-and-dictionary.md

- configs/storage.toml

- Any other existing documentation directly relevant to the target definition.

Preserve the decisions already established in Tasks 004, 004.1, and 004.2.

In particular:

- The forecast horizon is 12 calendar months.

- The forecast origin is the latest eligible published rent observation month (Option A).

- The target is the future average monthly rent in GBP, not rental growth.

- The forecast issue date, information cutoff, origin month, and target month must remain distinct.

- Historical features must respect publication availability.

- Cross-area comparisons should preferably use a common origin month.

- The verified Bank of England BTL mortgage rate source IUMZID4 must remain unchanged.

Do not redesign these decisions unless official evidence demonstrates a material feasibility problem. If so, explain the problem and propose alternatives for review rather than changing the design.

## 2. Identify Official ONS Rental Data Sources

Investigate the official ONS **Price Index of Private Rents (PIPR)** and its supporting datasets.

Search for:

1. PIPR monthly average private rent datasets.

2. PIPR datasets by Local Authority.

3. PIPR datasets by bedroom count.

4. Historical PIPR datasets and archived releases.

5. Relevant ONS downloadable CSV, XLSX, or other structured files.

6. Official ONS methodology and technical documentation.

7. Relevant historical predecessor series, including the Index of Private Housing Rental Prices (IPHRP), where appropriate.

For every relevant source, record:

- Official dataset title.

- Publisher.

- Official URL.

- Dataset/table/series identifier, if available.

- Download format.

- Whether the file or table is directly accessible.

- Last verified release or update date.

- The specific variables or tables r
