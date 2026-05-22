# TASK-002: Export Grades to CSV

## Status

Done

## Feature

`FEATURE-001-cli-edupage-automation`

## Scope

- Add a CLI scenario that opens an EduPage class grade table.
- Export all visible student/task grade cells to a CSV file.
- Use CSV headers compatible with the existing `fill-grades` input workflow.
- Include deterministic tests for extraction, CSV writing, and CLI registration.

## Done Criteria

- `export-grades` is registered in the CLI.
- The scenario writes `first_name`, `last_name`, `task_name`, and `points` columns.
- Empty grade cells are preserved as empty `points` values.
- Documentation, version, changelog, and tests are updated.
