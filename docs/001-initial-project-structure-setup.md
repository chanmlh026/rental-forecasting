I am starting a new end-to-end Data Science / Machine Learning project called **Rental Forecasting**.

## Project Background

The objective is to forecast average monthly private rental prices 12 months ahead for each Local Authority in England, separately for 1-bedroom, 2-bedroom, and 3-bedroom properties.

The primary data source will be the ONS Price Index of Private Rents (PIPR). Additional economic, demographic, housing supply, and rental demand variables will be incorporated later.

This project is intended to simulate a real-world, production-oriented Data Science / ML Engineering workflow.

I will initially develop and test the project locally using Python, VS Code, Parquet files, and GitHub.

Eventually, I plan to deploy the data pipelines, forecasting models, and an interactive dashboard and/or generated reports to Google Cloud Platform (GCP).

## Task

Please set up a clean, modular, production-oriented Python project structure in the currently opened VS Code workspace.

Use the following structure:

```text
rental-forecasting/
├── data/
│   ├── raw/
│   ├── external/
│   └── processed/
├── notebooks/
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── features/
│   ├── models/
│   ├── evaluation/
│   └── pipelines/
├── dashboard/
├── reports/
├── tests/
├── configs/
├── infra/
├── .github/
│   └── workflows/
├── README.md
├── pyproject.toml
├── .gitignore
└── Dockerfile
```

## Requirements

1. Create all directories and files in the existing workspace root. Do not create an additional nested rental-forecasting folder if the workspace already represents the project.

2. Use a modern Python project structure compatible with uv for dependency management.

3. Create a valid pyproject.toml with basic project metadata and a suitable Python version requirement. Do not install dependencies yet.

4. Create a .gitignore suitable for Python, VS Code, Jupyter, virtual environments, caches, secrets, and local datasets. Ignore the contents of the data/ directories while preserving their folder structure using .gitkeep files.

5. Create a README.md explaining:

    - Project objective

    - Data sources

    - High-level project architecture

    - Purpose of each directory

    - Local development workflow

    - Planned GCP deployment approach

6. Prepare the project for future GCP integration, potentially including Cloud Storage, Cloud Run Jobs, Cloud Run Services, and GitHub Actions.

7. Keep data storage configurable so that the same Python code can eventually work with local Parquet files or GCP Cloud Storage without major restructuring.

8. Create an appropriate .dockerignore and a minimal Dockerfile placeholder. Do not implement a working container image yet.

9. Use empty directories, .gitkeep files, or minimal \_\_init\_\_.py files where appropriate. Avoid creating unnecessary placeholder Python scripts.

10. Do not download datasets, implement ML models, create a dashboard, provision cloud infrastructure, or configure CI/CD pipelines at this stage.

11. Do not initialise Git or modify any existing Git repository without asking me first.

12. Before making changes, inspect the existing workspace. Preserve existing files and avoid overwriting anything without my approval.

## Expected Output

After completing the setup:

- Show me the final directory tree.

- Explain briefly what each directory is used for.

- List all files created or modified.

- Explain how I can verify that the project structure has been created correctly.

- Recommend the next step, which should be setting up the Python environment and obtaining the ONS PIPR dataset.

Please implement the setup directly in my VS Code workspace rather than just describing what I should do.
