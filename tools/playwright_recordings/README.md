# Playwright Recordings

This directory stores sanitized reference scripts exported from manual Playwright recordings.

These files are not part of the packaged CLI and should not be imported by production code. They document browser flows that were used to implement maintained scenarios under `src/edu_page_automat/scenarios/`.

## Files

- `create_task_recording.py`: original manual flow for creating an EduPage task.
- `fill_grade_recording.py`: original manual flow for filling an empty grade cell.
- `rewrite_grade_recording.py`: original manual flow for rewriting existing grade values.

## Rules

- Keep credentials out of recordings. Use `EDUPAGE_USERNAME` and `EDUPAGE_PASSWORD`.
- Prefer implementing maintained behavior in scenario modules instead of editing these recordings.
- Keep recordings small and clearly named by the behavior they demonstrate.
