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

## Task Execution Time Tracking

- Track each development task in the single version-controlled
  `docs/task-execution-log.csv`. At the start of work, create or update its row
  with the recorded start timestamp and `In Progress` status. Use ISO 8601
  timestamps with timezone information, consistently in UTC (`+00:00`).
- Maintain exactly one row per `task_id`, preserving task IDs as text (including
  leading zeros and subtask numbers). Update that row when work resumes or the
  task is revised; keep rows in chronological task order where practical.
- At completion or when stopping work, record the measured end timestamp,
  elapsed wall-clock duration in numeric minutes, and status. Allowed statuses
  are `Completed`, `In Progress`, `Blocked`, and `Failed`. Keep paused or
  incomplete work `In Progress` (or `Blocked` when applicable), and explain the
  pause or stop in `timing_notes`; do not mark unfinished tasks completed.
- Use actual recorded timestamps or reliable session logs. Calculate minutes
  from measured elapsed seconds divided by 60, or a reliable logged millisecond
  duration divided by 60,000. Record the evidence source, timing precision and
  measurement cutoff in `timing_notes`; never invent or estimate missing times.
  Leave unavailable timestamp/duration fields blank and explain limitations.
- For multiple work sessions, retain the first recorded start and latest
  recorded stop in the same row, but sum only measured work-session intervals
  for `duration_minutes`; do not count gaps between sessions automatically.
  Preserve session intervals, evidence and prior measured totals in
  `timing_notes`. If the full total is unavailable, leave the total blank and
  record any measured subtotal and missing intervals in the notes.
- Where practical, record measured user-input/approval waits separately in
  `timing_notes`. Wall-clock duration includes waits within a work session;
  do not silently subtract them or estimate active execution time. Disclose
  unmeasured waits and any final reporting/commit time outside the cutoff.
- Update the same CSV after each development task, including stops/resumptions.
  Preserve its agreed seven columns and standard CSV quoting. Historical rows
  may be added only with reliable timing evidence; questions/discussions do not
  require task rows. Keep tracking manual and lightweight without new tools,
  dependencies, services or per-task execution logs.
- Include task ID, start, end, duration in minutes, status and timing limitations
  in the final task report, alongside the existing prompt archive path.

## Project Issue Register and Dependency Management

- Before a development task, review [docs/issue-register.md](docs/issue-register.md).
  Identify relevant unresolved issues by affected area and Required Before
  checkpoint; inspect detailed supporting evidence only as needed. Keep checks
  lightweight rather than rereading every historical task or research report.
- Classify each relevant issue for the current scope: it does not block the task,
  it can be investigated/handled safely within the authorised scope, or it needs
  prerequisite resolution/project-owner approval. Record applicable issue IDs
  and the dependency outcome in the task's normal report.
- **Proceed** when no unresolved prerequisite prevents reliable execution.
  **Proceed with documented limitations** when the issue can be preserved,
  investigated or safely handled within scope; record limitations and follow-up
  actions. Do not silently make methodological decisions to bypass issues.
- **Blocked - Approval Required:** stop the affected implementation when a
  material decision, unapproved data substitution or necessary prerequisite
  prevents correct execution. Report the issue ID, why it blocks, required
  decision/action and available alternatives. Continue independent unaffected
  activities when safe; do not block unrelated work unnecessarily.
- After each development task, review new findings, add material unresolved
  issues, update existing statuses/evidence and avoid duplicate or overlapping
  entries. Keep detailed measurements in source documentation and link them.
  Maintain stable IDs and retain resolved issues as a historical decision record.
- Use `Open`, `In Progress`, `Resolved` and `Deferred` consistently, as defined
  in the register. A Deferred issue needs a future checkpoint and must not bypass
  a current prerequisite. Mark Resolved only after the required action,
  validation and any necessary owner approval are complete; record the outcome
  and supporting approval/evidence, not merely an attempted or proposed solution.
- Routine engineering issues may be resolved within an authorised task. Material
  methodology, architecture, feature-definition and data-substitution decisions
  require project-owner approval. Known data-quality limitations are not
  automatically blockers or reasons to reject a dataset.
- Confirm project-owner authorisation for each ingestion task within its actual
  scope; approval of Task 007 does not authorise later ingestion tasks. Check
  access and licensing requirements for every applicable dataset, recording the
  evidence in that task's normal report/source documentation.
- Treat recurring authorisation and routine dataset checks as workflow duties,
  not permanent Open issues. Register concrete unresolved access/licensing
  findings and retain them until evidence and any necessary approval support
  resolution; task authorisation alone does not resolve a source-specific issue.
- Include a brief final issue summary: relevant issues reviewed, new issues,
  issues resolved/updated, and remaining blockers or owner decisions. Use this
  single register; do not add per-dataset issue files, automated enforcement,
  databases, services or dependencies solely for issue management.
