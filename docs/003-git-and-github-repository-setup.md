## Project Context

I am developing a production-oriented Rental Forecasting Machine Learning project using Python 3.12, uv, VS Code, and eventually Google Cloud Platform (GCP).

The project structure and Python development environment have already been configured successfully.

I now want to set up Git and GitHub version control using professional software engineering practices.

## Task 1: Inspect Existing Git Configuration

Before making changes:

1. Check whether the current project is already a Git repository.

2. Check whether a GitHub remote is already configured.

3. Inspect the existing .gitignore.

4. Check whether Git is installed and available.

5. Preserve all existing project files and configurations.

Do not overwrite or reinitialise an existing Git repository.

## Task 2: Configure Git Repository

If the project is not already a Git repository:

1. Initialise Git in the current project root.

2. Use main as the default branch.

3. Ensure Git tracks source code, tests, documentation, configuration files, and uv.lock.

Verify that the .gitignore excludes:

- .venv/

- Python cache files

- pytest caches

- Jupyter checkpoints

- Local datasets (CSV, Parquet, etc.)

- Secrets and credentials

- Environment variable files containing secrets

- Generated model artifacts

- Temporary files

Preserve .gitkeep files so empty directories can be tracked.

Do not ignore uv.lock, pyproject.toml, or .python-version.

## Task 3: GitHub Repository

I want to create a private GitHub repository named:

rental-forecasting

Please:

1. Check whether GitHub CLI (gh) is installed and authenticated.

2. If authenticated, check whether a repository with this name already exists in my GitHub account.

3. If it does not exist, create a new private repository.

4. If it already exists, stop and explain the situation before changing its configuration.

5. Configure the local GitHub remote as origin.

If GitHub CLI is unavailable or authentication is required, explain the necessary steps instead of assuming access.

Do not create a public repository.

## Task 4: Initial Commit and Push

Before committing:

1. Review git status.

2. Review all files that would be committed.

3. Verify that no datasets, secrets, credentials, virtual environments, or large generated files are included.

4. Run uv run pytest.

If all checks pass:

1. Create the initial commit with the message:<br>Initial project setup

2. Push the main branch to the private GitHub repository.

Do not use force push.

## Task 5: Verification and Report

After completing the setup, report:

- Local Git repository status

- Current branch

- GitHub repository URL

- Whether the repository is private

- Initial commit hash

- Whether the push succeeded

- Test results

- Files included in the initial commit

- Any issues requiring manual action

Please implement the setup directly in the current VS Code workspace.

Do not modify the Machine Learning code, download datasets, configure GCP, or create CI/CD workflows at this stage.
