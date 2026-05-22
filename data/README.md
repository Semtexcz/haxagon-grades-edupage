# Data Fixtures

This directory contains local sample inputs and captured EduPage pages used for development and testing.

## Files

- `znamky.html`: captured EduPage grades page for selector inspection and offline tests.
- `seznam_uloh_*.csv`: sample task lists that can be passed to `edupage create-task --task-csv`.
- `seznam_uloh_*.ods` and `Haxagon_*.ods`: spreadsheet source files for sample task lists.
- `Haxagon_seznam_uloh_2026_02_19.csv`: exported sample task list.

## Rules

- Keep fixture data in this directory instead of the repository root.
- Do not commit credentials or live session state here.
- Prefer small CSV fixtures for automated tests.
