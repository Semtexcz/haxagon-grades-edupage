# EduPageAutomat

EduPageAutomat is a Python CLI for repeatable EduPage browser automation built on Playwright. It reuses an authenticated session when possible and runs scenario commands such as creating tests or assignments from CLI options or CSV input.

## Capabilities

- Automates EduPage with Playwright Firefox.
- Provides a `click` based CLI through the `edupage` command.
- Stores local session state in `auth.json` after login.
- Logs through `loguru`; set `HAXAGON_LOG_LEVEL` to change verbosity.
- Keeps scenario implementations under `src/edu_page_automat/scenarios/`.

## Requirements

- Python 3.13 or newer.
- Poetry.
- Playwright Firefox browser binaries.

## Installation

For local development with Poetry:

```bash
poetry install
poetry run edupage install-browsers
```

For an isolated CLI install with pipx:

```bash
pipx install .
edupage install-browsers
```

Run `edupage install-browsers` again after Playwright upgrades if browser-backed commands report a missing browser executable.

## Configuration

Set EduPage credentials before the first login:

```bash
export EDUPAGE_USERNAME="user@example.com"
export EDUPAGE_PASSWORD="secret-password"
export EDUPAGE_URL="https://school.edupage.org/"
```

`EDUPAGE_URL` is optional and defaults to `https://1itg.edupage.org/`.

The login flow writes `auth.json` in the repository root. This file contains session state and is ignored by Git.

## CLI Usage

```bash
poetry run edupage --help
poetry run edupage list
poetry run edupage install-browsers
poetry run edupage login
```

Create a task directly:

```bash
poetry run edupage create-task --class "3.gpu" --name "Test 1" --points 50
```

Create multiple tasks:

```bash
poetry run edupage create-task \
  --class "3.gpu" \
  --task "Test 1:50" \
  --task "Revision:30"
```

Create tasks from CSV:

```bash
poetry run edupage create-task --class "3.gpu" --task-csv data/seznam_uloh_JS.csv
```

CSV input must include a task name column (`name`, `task`, or `nazev`) and a points column (`points`, `point`, `score`, or `body`).

Fill grades from CSV:

```bash
poetry run edupage fill-grades --class "2.png" --subject "Informatika" --grades-csv data/test_grades_2_png.csv
```

Use `--overwrite-existing` only when the CSV should replace grades that are already stored in EduPage:

```bash
poetry run edupage fill-grades --class "2.png" --subject "Informatika" --grades-csv data/test_grades_2_png.csv --overwrite-existing
```

Convert Google Classroom grades to the `fill-grades` CSV format:

```bash
poetry run edupage convert-classroom-grades \
  --input-csv data/classroom_grades_801460822073_2026-05-22.csv \
  --output-csv data/edupage_classroom_grades_801460822073_2026-05-22.csv \
  --topic "JavaScript – Certifications"
```

Write a minimal grade diff CSV for values that still need to be saved to EduPage:

```bash
poetry run edupage diff-grades \
  --current-csv data/jpg_grades_export_edupage.csv \
  --truth-csv data/edupage_classroom_grades_801460822073_2026-05-22.csv \
  --output-csv data/jpg_grades_diff.csv
```

The diff output can be used with `fill-grades --overwrite-existing`. `--truth-csv` accepts either an EduPage-style grade CSV or a raw Google Classroom export. Empty raw Google Classroom point values are treated as `m`; empty EduPage-style source-of-truth grades and rows missing from the current EduPage export are reported in the command summary for manual review.

## Development

Run tests with:

```bash
poetry run pytest
```

Important project documentation:

- `docs/ARCHITECTURE.md`: module boundaries and runtime flow.
- `docs/TASK_SEQUENCE.md`: backlog ordering.
- `context/test-strategy.md`: deterministic and live-test boundaries.
- `data/README.md`: fixture data rules.

## Repository Layout

```text
src/edu_page_automat/
  cli.py                CLI registration and commands
  auth_manager.py       session validation and login fallback
  setup_login.py        interactive EduPage login flow
  scenario_runner.py    Playwright lifecycle and auto-wait wrappers
  scenarios/            automation scenario implementations
tests/                  deterministic unit tests
data/                   sample inputs and captured EduPage fixtures
docs/                   architecture and task sequence documentation
tools/playwright_recordings/
                        sanitized manual Playwright recordings
product/features/       feature scope documents
project/backlog/        active task documents
project/done/           completed task documents
```
