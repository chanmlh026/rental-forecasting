# 004. Design Rental Forecasting Data Architecture & Data Dictionary

## Project Context

I am developing a production-oriented Rental Forecasting Machine Learning project using Python 3.12, uv, pytest, VS Code, Git, and GitHub, with future deployment on Google Cloud Platform (GCP).

The project environment, directory structure, dependency management, testing framework, and private GitHub repository have already been configured.

The project aims to forecast **average monthly private rents 12 months ahead for each English Local Authority, separately for 1-bedroom, 2-bedroom, and 3-bedroom properties**.

The primary rental data source is the Office for National Statistics (ONS), with historical data from January 2015 to September 2026, subject to verification of the available series and geographical coverage.

## Task 1: Inspect the Existing Project

Before proposing any changes:

1. Inspect the current project structure.

2. Review README.md, pyproject.toml, configs/storage.toml, and relevant existing Python modules.

3. Identify any existing data architecture decisions, storage configurations, or reusable components.

4. Preserve all existing files, configurations, and code.

5. Do not initialise another Git repository.

## Task 2: Design the Data Architecture

Propose a modular, maintainable data architecture with the following layers:

- Raw data: original source datasets.

- Validated data: datasets passing structural and quality checks.

- Processed data: cleaned and standardised datasets.

- Feature data: engineered explanatory variables.

- Modelling data: training, validation, and testing datasets.

Explain:

- The purpose and responsibility of each layer.

- How data moves between layers.

- Recommended file formats, including Parquet.

- Naming conventions and directory organisation.

- Dataset versioning and reproducibility.

- How the architecture could eventually integrate with GCP Cloud Storage.

Avoid introducing unnecessary infrastructure or dependencies.

## Task 3: Design the Data Dictionary

Investigate and document the following proposed data sources:

1. ONS Private Index of Rental Prices (PIPR) and available bedroom-level rental price series.

2. Bank of England base rate.

3. Two-year fixed buy-to-let mortgage rates at approximately 75% LTV.

4. Consumer Price Index (CPI).

5. Unemployment rates.

6. Household income.

7. House Price Index (HPI).

8. Population density.

9. Housing completions.

10. Planning approvals.

11. Domestic and international migration.

12. Student population.

For each source, document:

- Source organisation and dataset name.

- Official source URL, where verified.

- Variable definitions and units.

- Data frequency.

- Geographic granularity.

- Historical coverage.

- Publication frequency and lag.

- Revision policy, where known.

- Potential missing-data issues.

- Proposed ingestion method.

- Relevance to rental forecasting.

Do not invent unavailable datasets, historical coverage, or publication dates.

Clearly distinguish verified information from assumptions requiring further investigation.

## Task 4: Define the Target Variable

Propose a formal definition for the 12-month-ahead rental forecasting target.

Address:

- Local Authority identifiers and boundary changes.

- Bedroom categories: 1, 2, and 3 bedrooms.

- Monthly observation dates.

- Forecast origin and target date.

- Whether rental values are observed, estimated, or derived.

- Potential limitations of ONS rental statistics.

- Handling missing or discontinued series.

Use a target definition equivalent to:

y(LA, bedroom, t) = average monthly rent at t + 12 months

Clarify that the target is the future rent level, not the percentage growth rate.

## Task 5: Design Data Validation

Propose validation rules covering:

- Required columns and data types.

- Duplicate observations.

- Missing values.

- Geographic identifiers.

- Date continuity.

- Bedroom categories.

- Non-positive rental values.

- Unexpected outliers.

- Dataset schema changes.

- Source freshness and completeness.

Explain which checks should fail the pipeline and which should generate warnings.

## Task 6: Prevent Data Leakage

Design a point-in-time data strategy suitable for historical backtesting.

Address:

- Observation dates versus publication dates.

- Data revisions.

- Feature availability at each forecast origin.

- Appropriate feature lags.

- Monthly versus quarterly or annual variables.

- Forward-filling and its limitations.

- Avoiding the use of future observations or revised values unavailable at prediction time.

Explain how the proposed architecture supports realistic 12-month-ahead forecasts.

## Task 7: Proposed Deliverables

Produce the following for review:

1. A proposed project directory structure.

2. A Mermaid data architecture diagram.

3. A structured data dictionary.

4. A target variable specification.

5. A data validation strategy.

6. A point-in-time data leakage prevention strategy.

7. A staged implementation plan.

8. Key architectural decisions, assumptions, and unresolved questions.

## Constraints

- Do not modify existing Python code.

- Do not download datasets.

- Do not install additional packages.

- Do not train forecasting models.

- Do not configure GCP.

- Do not create CI/CD workflows.

- Do not commit or push changes to GitHub.

- Do not overwrite existing project files.

This task is a design and planning exercise only.

Present the proposed architecture and recommendations for review before implementation.
