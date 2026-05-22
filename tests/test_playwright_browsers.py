import sys
from unittest.mock import MagicMock

from edu_page_automat.playwright_browsers import install_firefox_browser, is_missing_browser_error


def test_is_missing_browser_error_detects_playwright_install_message() -> None:
    """Playwright missing-browser launch errors are recognized."""
    exc = RuntimeError("Executable doesn't exist at /tmp/firefox. Please run: playwright install")

    assert is_missing_browser_error(exc) is True


def test_is_missing_browser_error_ignores_unrelated_errors() -> None:
    """Unrelated Playwright errors should not be rewritten as install help."""
    exc = RuntimeError("Timeout while waiting for selector")

    assert is_missing_browser_error(exc) is False


def test_install_firefox_browser_uses_current_python(monkeypatch) -> None:
    """Browser installation runs through the current Python interpreter."""
    run = MagicMock()
    monkeypatch.setattr("edu_page_automat.playwright_browsers.subprocess.run", run)

    install_firefox_browser()

    run.assert_called_once_with(
        [sys.executable, "-m", "playwright", "install", "firefox"],
        check=True,
    )
