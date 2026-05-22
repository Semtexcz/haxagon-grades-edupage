# TASK-003: Export Grade Categories

## Status

Done

## Feature

`FEATURE-001-cli-edupage-automation`

## Scope

- Add the EduPage task category to exported grade CSV rows.
- Read the category from `.znHeaderKategoria` in each grade-table task header.
- Keep empty category values when EduPage does not expose a category for a visible task.
- Update deterministic tests and documentation.

## Done Criteria

- `export-grades` writes a `task_category` CSV column.
- Existing exported student, task, and points values are preserved.
- Documentation, version, changelog, and tests are updated.
