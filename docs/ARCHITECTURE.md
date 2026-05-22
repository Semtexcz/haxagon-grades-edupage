# Architecture

## Purpose

EduPageAutomat is a Python CLI for running repeatable EduPage browser automation flows with Playwright.

## Module Boundaries

- `edu_page_automat.cli` owns the public command line interface and scenario registration.
- `edu_page_automat.auth_manager` owns session discovery, validation, and login fallback.
- `edu_page_automat.setup_login` owns the interactive EduPage login flow and writes `auth.json`.
- `edu_page_automat.scenario_runner` owns Playwright lifecycle management and auto-wait wrappers.
- `edu_page_automat.scenarios` contains user-facing automation scenarios. Scenario modules should not manage browser startup or session setup directly.
- `data/` stores local test fixtures, sample task CSV files, spreadsheets, and captured EduPage HTML.
- `tests/` stores deterministic unit tests. Tests should avoid live EduPage access.

## Main Flow

1. `edupage` starts in `cli.py`.
2. A scenario command builds a `Scenario` instance.
3. `run_scenario` opens Playwright, obtains an authenticated context from `AuthManager`, wraps the page in `AutoWaitPage`, and calls `scenario.run(page)`.
4. The scenario performs page interactions and returns control to the runner.
5. The runner closes the Playwright context and browser.

## Authentication Flow

`AuthManager` first checks `auth.json`. If it exists, it opens a Firefox context with that storage state and visits the EduPage user page. If the resulting URL indicates a login page, the stored session is closed and `setup_login.run` performs a fresh login.

`auth.json` is intentionally ignored by Git because it contains session state.

## Scenario Design

Scenarios inherit from `Scenario` and implement:

- `register_cli(cls, cli_group)` to expose options and commands.
- `run(self, page)` to execute browser steps.

Scenario code should accept already-authenticated Playwright pages from `scenario_runner` and keep EduPage selectors local to the scenario module.

## Grade Filling Flow

`FillGradesScenario` reads CSV rows with first name, last name, task name, and points. After selecting the target course and opening the Známky module, it resolves each student from the grade-table link text `Last, First`, resolves each existing task from `.znamkyUdalostHeader`, fills the matching `nzn_{student_id}_{subject_id}_{task_uid}_{period}_1` input, and clicks the EduPage save button unless `--dry-run` is used.

The scenario assumes tasks already exist in EduPage. Task creation remains the responsibility of `CreateTaskScenario`.

## Test Strategy Boundary

Unit tests should mock Playwright objects where possible. Live browser and EduPage tests are outside the default test suite because they depend on credentials, network availability, and mutable EduPage state.
