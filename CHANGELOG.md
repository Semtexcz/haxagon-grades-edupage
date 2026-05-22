# Changelog

All notable changes to this project are documented here.

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
