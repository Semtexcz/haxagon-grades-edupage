# Architecture

## Purpose

EduPageAutomat is a Python CLI for running repeatable EduPage browser automation flows with Playwright.

## Module Boundaries

- `edu_page_automat.cli` owns the public command line interface and scenario registration.
- `edu_page_automat.classroom_grades` owns offline CSV conversion from Google Classroom grade exports to EduPage grade input CSV files.
- `edu_page_automat.grade_diff` owns offline CSV diffing between current EduPage exports and source-of-truth grade CSV files.
- `edu_page_automat.auth_manager` owns session discovery, validation, and login fallback.
- `edu_page_automat.setup_login` owns the interactive EduPage login flow and writes `auth.json`.
- `edu_page_automat.playwright_browsers` owns Playwright browser binary installation and missing-browser diagnostics.
- `edu_page_automat.scenario_runner` owns Playwright lifecycle management and auto-wait wrappers.
- `edu_page_automat.scenarios` contains user-facing automation scenarios. Scenario modules should not manage browser startup or session setup directly.
- `data/` stores local test fixtures, sample task CSV files, spreadsheets, and captured EduPage HTML.
- `tests/` stores deterministic unit tests. Tests should avoid live EduPage access.
- `tools/playwright_recordings/` stores sanitized manual Playwright recordings used as implementation references. These files are not packaged CLI modules.

## Main Flow

1. `edupage` starts in `cli.py`.
2. A scenario command builds a `Scenario` instance.
3. `run_scenario` opens Playwright, obtains an authenticated context from `AuthManager`, wraps the page in `AutoWaitPage`, and calls `scenario.run(page)`.
4. The scenario performs page interactions and returns control to the runner.
5. The runner closes the Playwright context and browser.

## Authentication Flow

`AuthManager` first checks `auth.json`. If it exists, it opens a Firefox context with that storage state and visits the EduPage user page. If the resulting URL indicates a login page, the stored session is closed and `setup_login.run` performs a fresh login.

`auth.json` is intentionally ignored by Git because it contains session state.

## Browser Installation Flow

Playwright requires browser binaries outside the Python package files. The `install-browsers` command runs `python -m playwright install firefox` through the same Python interpreter that launched `edupage`, so it works in both Poetry and pipx environments.

If a login or scenario command fails because the Firefox executable is missing, the CLI rewrites Playwright's raw launch exception into a short message that points to `edupage install-browsers`.

## Scenario Design

Scenarios inherit from `Scenario` and implement:

- `register_cli(cls, cli_group)` to expose options and commands.
- `run(self, page)` to execute browser steps.

Scenario code should accept already-authenticated Playwright pages from `scenario_runner` and keep EduPage selectors local to the scenario module.

## Grade Filling Flow

`FillGradesScenario` reads CSV rows with first name, last name, task name, and a grade value. Grade values may be whole-number points or the EduPage `m` marker. After selecting the target course and opening the Známky module, it resolves each student from the grade-table link text `Last, First`, resolves each existing task from `.znamkyUdalostHeader`, fills the matching `nzn_{student_id}_{subject_id}_{task_uid}_{period}_1` input for empty cells, and clicks the EduPage save button unless `--dry-run` is used.

Rows without a grade value are ignored before browser automation starts. This allows review/export CSV files to include unfinished students without requiring manual cleanup before import.

Existing grade values are protected by default. With `--overwrite-existing`, the scenario opens the existing cell editor through the matching `nzn_{student_id}_{subject_id}_{task_uid}_{period}_1` input and fills the replacement value through the visible EduPage editor. Saving clicks the ribbon save action and confirms the EduPage save dialog when it appears.

The scenario assumes tasks already exist in EduPage. Task creation remains the responsibility of `CreateTaskScenario`.

## Grade Export Flow

`ExportGradesScenario` selects the target course, opens the Známky module, reads all visible task headers from `.znamkyUdalostHeader`, and walks each visible student row in the grade table. It exports one CSV row for each visible student/task grade cell using the headers `first_name`, `last_name`, `task_category`, `task_name`, and `points`.

The export is a snapshot of the currently visible EduPage table. Empty grade cells are included with an empty `points` value so the CSV can be reviewed or reused as compatible input for `fill-grades`.

## Google Classroom Grade Conversion

The `convert-classroom-grades` CLI command runs offline and does not use the scenario runner or Playwright. It reads a Google Classroom grade export, optionally filters rows by Classroom topic or task name, splits the `Student` display name on whitespace into first and last name fields, and writes the EduPage grade CSV headers `jmeno`, `prijmeni`, `jmeno_ulohy`, and `pocet_bodu`.

The converter preserves empty `Points earned` values as empty `pocet_bodu` cells for review. Whole-number point values are written unchanged, keeping the output compatible with `fill-grades`.

## Grade Diff Flow

The `diff-grades` CLI command runs offline and does not use the scenario runner or Playwright. It compares a current EduPage grade export with a source-of-truth grade CSV by first name, last name, and task name, then writes only rows where the source-of-truth value is non-empty and differs from the current EduPage value.

The generated diff uses the `fill-grades` Czech headers `jmeno`, `prijmeni`, `jmeno_ulohy`, and `pocet_bodu`. Empty source-of-truth values are reported in the CLI summary but not written because `fill-grades` deliberately skips empty grades and cannot clear an existing EduPage value. Rows that are missing from the current EduPage export are also reported instead of written, because they usually indicate a visibility, task, or name-matching problem that should be reviewed before browser automation.

## Test Strategy Boundary

Unit tests should mock Playwright objects where possible. Live browser and EduPage tests are outside the default test suite because they depend on credentials, network availability, and mutable EduPage state.
