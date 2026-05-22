# Test Strategy

## Default Test Command

Run the deterministic test suite with:

```bash
poetry run pytest
```

## Unit Tests

Unit tests cover CLI wiring, authentication decisions, scenario runner wrappers, and CSV task parsing. They use dummy objects or mocks instead of launching a real browser.

## Fixture Data

Local sample data and captured EduPage HTML live in `data/`. Tests may read from this directory when static fixtures are needed.

## Live EduPage Checks

Live checks require credentials, Playwright browser binaries, network access, and mutable EduPage state. They should be run manually and kept out of the default test suite.
