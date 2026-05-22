"""Helpers for installing and diagnosing Playwright browser binaries."""

import subprocess
import sys

PLAYWRIGHT_BROWSER_INSTALL_COMMAND = "edupage install-browsers"


def is_missing_browser_error(exc: Exception) -> bool:
    """Return whether a Playwright exception indicates missing browser binaries."""
    message = str(exc)
    return "Executable doesn't exist" in message and "playwright install" in message


def missing_browser_message() -> str:
    """Return a user-facing message for missing Playwright browser binaries."""
    return (
        "Playwright Firefox browser binaries are not installed for this Python environment.\n"
        f"Run `{PLAYWRIGHT_BROWSER_INSTALL_COMMAND}` and retry the EduPage command.\n"
        "When using Poetry, run `poetry run edupage install-browsers`."
    )


def install_firefox_browser() -> None:
    """Install the Playwright Firefox browser for the current Python environment."""
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "firefox"],
        check=True,
    )
