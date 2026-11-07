I have completed the initial folder structure for my Rental Forecasting project.

The next step is to configure the local Python development environment using uv.

Please work in the currently opened VS Code workspace.

Requirements:

1. Inspect the existing pyproject.toml and project structure before making any changes.

2. Use Python 3.12 if it is available. Otherwise, report the available versions before choosing an alternative.

3. Create a project-specific virtual environment using uv.

4. Configure the following initial dependencies:

    - pandas

    - numpy

    - pyarrow

    - matplotlib

    - scikit-learn

    - jupyter

    - pytest (development dependency)

5. Update pyproject.toml appropriately and generate uv.lock.

6. Ensure .venv/ is excluded from Git.

7. Configure VS Code to use the project's virtual environment without changing global Python settings.

8. Create one simple smoke test under tests/ to verify that the Python environment and essential dependencies work correctly.

9. Run pytest and report the results.

10. Do not download datasets, implement forecasting models, deploy to GCP, or install additional dependencies without explaining why they are needed.

11. Do not overwrite existing configurations without checking them first.

After completing the setup, explain:

- Which Python version is being used

- Which packages were installed

- Whether pytest passed

- Which files were created or modified

- How I can run Python scripts and pytest from the VS Code terminal

Please implement the setup directly in my workspace.

# 002. Python Development Environment Setup – Completion and Verification

The initial Python environment setup has been completed, but two items need to be addressed before proceeding to data ingestion.

## Task 1: Python Version

The project currently uses Python 3.14.6.

I would prefer Python 3.12 for broader compatibility with the Machine Learning ecosystem and future deployment to Google Cloud Platform.

Please:

1. Use uv to install Python 3.12 if necessary.

2. Update .python-version and pyproject.toml appropriately.

3. Recreate or synchronise the project's virtual environment using Python 3.12.

4. Ensure VS Code continues to use the correct project virtual environment.

5. Verify that the environment works correctly.

Do not change the global Python installation or settings.

## Task 2: Install Data Science Dependencies

The previous setup only installed pytest.

Please add the following dependencies:

Runtime dependencies:

- pandas

- numpy

- pyarrow

- matplotlib

- scikit-learn

Development dependencies:

- pytest

- jupyter

Use uv to manage dependencies and update pyproject.toml and uv.lock.

Do not install additional ML frameworks or cloud libraries yet.

## Task 3: Environment Verification

Please verify:

1. The Python version used by the project.

2. Successful imports of pandas, numpy, pyarrow, matplotlib, and scikit-learn.

3. That uv sync --locked completes successfully.

4. That uv run pytest passes.

5. That the existing project structure remains unchanged except where necessary.

Update the existing environment smoke test if appropriate.

## Task 4: Report Results

After completing the tasks, provide:

- Python version

- Installed dependencies and versions

- Test results

- Files created or modified

- Any remaining issues

Do not download datasets, implement forecasting models, or deploy anything to GCP.

Please implement these changes directly in the current VS Code workspace.
