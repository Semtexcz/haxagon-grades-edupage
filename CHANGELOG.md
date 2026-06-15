# Changelog

All notable changes to this project are documented here.

## 0.9.10 - 2026-06-15

### Fixed

- Normalized EduPage export grade displays like `m · 20` and `15 · 20` so `export-grades` and `diff-grades` keep using fill-compatible point values.

## 0.9.9 - 2026-06-15

### Fixed

- Made `convert-classroom-grades` treat only the final student-name token as `prijmeni`, preserving multi-part given names in `jmeno`.

## 0.9.8 - 2026-06-15

### Added

- Re-enabled Typer shell completion commands on the `edupage` root CLI.

## 0.9.7 - 2026-06-15

### Fixed

- Stopped the scenario auto-wait wrapper from blocking Playwright click actions when an explicit pre-wait times out on filtered locators.

## 0.9.6 - 2026-06-15

### Changed

- Migrated the `edupage` command-line app from Click to Typer while keeping existing command names and options.
- Updated CLI documentation to describe the Typer app and the user-level login storage path.

## 0.9.5 - 2026-05-27

### Changed

- Persisted EduPage login in a global user-level storage-state file instead of the current working directory.

## 0.9.4 - 2026-05-22

### Fixed

- Allowed `diff-grades --truth-csv` to read raw Google Classroom exports directly.

## 0.9.3 - 2026-05-22

### Changed

- Changed `convert-classroom-grades` to output `m` for empty Google Classroom point values.

## 0.9.2 - 2026-05-22

### Added

- Added `install-browsers` to install Playwright Firefox browser binaries in the active CLI environment.

### Fixed

- Replaced raw missing-browser Playwright tracebacks with actionable install guidance.
- Documented pipx browser installation.

## 0.9.1 - 2026-05-22

### Fixed

- Made `fill-grades --overwrite-existing` use the visible EduPage cell editor and confirm the save dialog when shown.
- Fixed Loguru message interpolation so scenario logs include concrete values.

## 0.9.0 - 2026-05-22

### Added

- Added `diff-grades` for generating minimal `fill-grades` CSV files from current EduPage exports and source-of-truth grade CSVs.
- Documented the offline grade diff flow and its skipped-row summary counts.

## 0.8.0 - 2026-05-22

### Added

- Added `convert-classroom-grades` for offline Google Classroom grade CSV conversion into `fill-grades` input.
- Documented the Google Classroom grade conversion flow and CLI filters.

### Changed

- Made `fill-grades` skip CSV rows with empty point values before browser automation starts.

## 0.7.0 - 2026-05-22

### Added

- Added `task_category` to `export-grades` CSV output from EduPage task headers.

## 0.6.0 - 2026-05-22

### Added

- Added the `export-grades` CLI scenario for saving visible class grade-table values to CSV.
- Documented the grade export flow and CSV output format.

## 0.5.1 - 2026-05-22

### Changed

- Moved raw Playwright recordings into `tools/playwright_recordings/` with clearer names and module documentation.
- Sanitized reference recordings to read credentials from environment variables.

## 0.5.0 - 2026-05-22

### Added

- Added `--overwrite-existing` to `fill-grades` for intentionally replacing existing EduPage grade values.

## 0.4.2 - 2026-05-22

### Fixed

- Allowed `fill-grades` CSV grade values to use the EduPage `m` marker in addition to numeric points.

## 0.4.1 - 2026-05-22

### Fixed

- Made `fill-grades` wait for the grade table and resolve students/tasks through DOM data with clearer diagnostics.

## 0.4.0 - 2026-05-22

### Added

- Added the `fill-grades` CLI scenario for filling existing EduPage task points from CSV input.
- Documented the grade-filling flow and supported CSV headers.

## 0.3.1 - 2026-05-22

### Added

- Added baseline architecture, feature, task sequence, test strategy, and fixture documentation.
- Added a cleanup task record under `project/done/`.

### Changed

- Moved sample task and EduPage fixture files into `data/`.
- Updated project-facing documentation to describe the current repository layout in English.
