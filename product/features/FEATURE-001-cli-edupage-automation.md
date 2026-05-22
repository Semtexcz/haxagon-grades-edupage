# FEATURE-001: CLI EduPage Automation

## Summary

The project provides a command line interface for authenticated EduPage automation scenarios.

## Scope

- Reuse a stored EduPage session when `auth.json` is valid.
- Perform a fresh login when the stored session is missing or invalid.
- Register scenario commands through the `Scenario` base class.
- Support the `create-task` scenario for creating tests or assignments from CLI options or CSV input.
- Support the `fill-grades` scenario for filling existing task point values from CSV input.

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

By default, `fill-grades` refuses to replace non-empty grade cells. Use `--overwrite-existing` when the CSV is intended to replace already stored EduPage grade values.
