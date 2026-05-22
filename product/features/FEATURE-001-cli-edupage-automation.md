# FEATURE-001: CLI EduPage Automation

## Summary

The project provides a command line interface for authenticated EduPage automation scenarios.

## Scope

- Reuse a stored EduPage session when `auth.json` is valid.
- Perform a fresh login when the stored session is missing or invalid.
- Register scenario commands through the `Scenario` base class.
- Support the `create-task` scenario for creating tests or assignments from CLI options or CSV input.
- Support the `fill-grades` scenario for filling existing task point values from CSV input.
- Support the `export-grades` scenario for saving visible class grade values to CSV.
- Support offline Google Classroom grade CSV conversion into the `fill-grades` input format.

## Out of Scope

- Running live EduPage tests in the default unit test suite.
- Managing credentials outside environment variables or interactive prompts.
- Persisting task creation history outside EduPage.

## Integration Points

- EduPage website through Playwright Firefox.
- `click` for CLI commands and validation.
- `loguru` for console logging.

## CSV Grade Input

The `fill-grades` command accepts a CSV with columns for first name, last name, task name, and points. Czech-friendly headers such as `jmeno`, `prijmeni`, `jmeno_ulohy`, and `pocet_bodu` are supported alongside English alternatives. Grade values may be whole-number points or the EduPage `m` marker.

Rows with empty point values are skipped before browser automation starts, which lets review CSV files keep unfinished assignments visible without filling them.

By default, `fill-grades` refuses to replace non-empty grade cells. Use `--overwrite-existing` when the CSV is intended to replace already stored EduPage grade values.

## CSV Grade Export

The `export-grades` command writes a CSV with `first_name`, `last_name`, `task_category`, `task_name`, and `points` columns. It exports all visible student/task cells from the selected class and subject grade table, including empty cells with an empty `points` value.

The exported CSV keeps task categories from EduPage headers such as `Dan - Frontend`. The remaining required headers are compatible with `fill-grades`, so the file can be reviewed, edited, and used later as grade input.

## Google Classroom Grade Conversion

The `convert-classroom-grades` command converts Google Classroom grade exports into the Czech `fill-grades` CSV format. It is intentionally outside the scenario registry because it only reads and writes local CSV files.

Use `--topic` or `--task` filters to keep only the Classroom rows that correspond to EduPage tasks intended for import.
