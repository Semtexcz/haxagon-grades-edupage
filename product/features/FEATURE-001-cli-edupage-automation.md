# FEATURE-001: CLI EduPage Automation

## Summary

The project provides a command line interface for authenticated EduPage automation scenarios.

## Scope

- Reuse a stored EduPage session when `auth.json` is valid.
- Perform a fresh login when the stored session is missing or invalid.
- Register scenario commands through the `Scenario` base class.
- Support the `create-task` scenario for creating tests or assignments from CLI options or CSV input.

## Out of Scope

- Running live EduPage tests in the default unit test suite.
- Managing credentials outside environment variables or interactive prompts.
- Persisting task creation history outside EduPage.

## Integration Points

- EduPage website through Playwright Firefox.
- `click` for CLI commands and validation.
- `loguru` for console logging.
