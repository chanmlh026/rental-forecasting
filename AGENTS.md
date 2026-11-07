# Codex Project Instructions

These instructions apply throughout this repository.

## Before starting any task

1. Read [docs/ENGINEERING_STANDARDS.md](docs/ENGINEERING_STANDARDS.md).
2. Follow those standards throughout implementation and follow the current
   task's requirements and acceptance criteria.
3. Review the relevant existing code, configuration, tests, and documentation
   before making changes. Preserve existing conventions and keep changes within
   the authorised task scope.
4. Obtain approval before major architecture or methodology changes.
5. Run relevant checks and tests, and report changes, results, limitations, and
   unresolved issues. Do not claim completion without verification evidence;
   state explicitly when a check could not be run and why.

The engineering standards are maintained in the linked document; do not copy
them into other instruction files. Report conflicting guidance rather than
silently changing approved project decisions.

## Repository conventions

- Use [README.md](README.md) for setup, the project layout, and current workflow
  commands. Use `uv` with `pyproject.toml`, `uv.lock`, and `.python-version` for
  the project environment. Run tests from the repository root with
  `uv run pytest`; select relevant tests when the task is narrower.
- Keep production logic in the existing `src/` packages, exploratory work in
  `notebooks/`, non-secret configuration in `configs/`, and deployment resources
  in `infra/`. Reuse `configs/storage.toml` for storage settings.
- Consult [the data architecture and dictionary](docs/data-architecture-and-dictionary.md)
  for design context and the confirmed Option A forecast horizon. Distinguish
  proposals and historical descriptions from approved decisions and implemented
  behavior; the proposal is not blanket approval for new architecture.
- For existing PIPR ingestion, consult [the Task 006 guide](docs/006-ons-pipr-ingestion.md)
  and [the Task 005.1 audit](docs/005.1-ons-pipr-workbook-coverage-audit.md).
  Preserve the approved cohort, immutable release handling, validation gates,
  and documented point-in-time limitations. Ingestion does not authorise feature
  engineering, model training, or onboarding another data source.
- Respect `.gitignore`: keep local datasets and generated artifacts out of Git,
  preserving the existing exceptions for the pinned geography reference and
  lightweight audit outputs.

## Task Prompt Archiving

- Save every new development task prompt in the existing `docs/` folder before
  implementing code changes. Do not archive ordinary questions or discussions.
- Preserve the original instructions and acceptance criteria verbatim, without
  summarising them.
- Follow the existing three-digit task numbering and descriptive, lowercase,
  hyphen-separated Markdown file naming conventions, such as
  `006-ons-pipr-ingestion.md`. Check existing task numbers before assigning the
  next number; retain established subtask numbering where applicable.
- Check for an existing prompt file for the task before creating one. Reuse it
  rather than duplicating the prompt in another file.
- Append subsequent task instructions and revisions verbatim to the same file
  in chronological order, with dated entries. Never overwrite the original
  prompt or earlier instructions.
- After completing each archived task, report the saved prompt file path.
