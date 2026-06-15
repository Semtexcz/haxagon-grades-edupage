"""Playwright lifecycle helpers for running EduPage scenarios."""

from typing import Any, Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import FrameLocator, Locator, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from edu_page_automat.auth_manager import AuthManager
from edu_page_automat.logging_config import setup_logging
from edu_page_automat.playwright_browsers import is_missing_browser_error, missing_browser_message

DEFAULT_WAIT_TIMEOUT = 10_000
_AUTO_WAIT_ACTION_STATES = {
    "check": "visible",
    "click": "visible",
    "dblclick": "visible",
    "drag_to": "visible",
    "fill": "visible",
    "focus": "visible",
    "hover": "visible",
    "press": "attached",
    "select_option": "attached",
    "set_input_files": "attached",
    "tap": "visible",
    "type": "attached",
    "uncheck": "visible",
}
_PLAYWRIGHT_AUTO_WAIT_ACTIONS = {"check", "click", "dblclick", "fill", "hover", "tap", "uncheck"}

logger = setup_logging()


class ScenarioRunnerError(RuntimeError):
    """User-facing scenario runner error that should be rendered by the CLI."""


def _wrap_result(result: Any, timeout: Optional[float]):
    """Wrap Playwright locator-like return values with auto-wait proxies."""
    if isinstance(result, Locator):
        return AutoWaitLocator(result, timeout)
    if isinstance(result, FrameLocator):
        return AutoWaitFrameLocator(result, timeout)
    return result


class AutoWaitLocator:
    """Locator proxy that waits for element readiness before key actions."""

    def __init__(self, locator: Locator, timeout: Optional[float]):
        """Store the wrapped locator and default wait timeout."""
        self._locator = locator
        self._timeout = timeout

    def __getattribute__(self, item):
        """Preserve Playwright class identity for wrapped locators."""
        if item == "__class__":
            locator = object.__getattribute__(self, "_locator")
            return locator.__class__
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        """Delegate locator attributes and wrap methods that return locators."""
        locator = object.__getattribute__(self, "_locator")
        attr = getattr(locator, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                state = _AUTO_WAIT_ACTION_STATES.get(item)
                if state:
                    logger.debug("Waiting for locator {} before {}", locator, item)
                    try:
                        locator.wait_for(state=state, timeout=object.__getattribute__(self, "_timeout"))
                    except PlaywrightTimeoutError:
                        if item not in _PLAYWRIGHT_AUTO_WAIT_ACTIONS:
                            raise
                        logger.debug(
                            "Locator {} did not satisfy explicit {} wait before {}; using Playwright action auto-wait",
                            locator,
                            state,
                            item,
                        )
                result = attr(*args, **kwargs)
                return _wrap_result(result, object.__getattribute__(self, "_timeout"))
            return wrapper
        return attr

    def unwrap(self) -> Locator:
        """Return the underlying Playwright locator."""
        return object.__getattribute__(self, "_locator")

    def __repr__(self) -> str:
        """Return a debug representation of the wrapped locator."""
        locator = object.__getattribute__(self, "_locator")
        return f"AutoWaitLocator({locator!r})"


class AutoWaitFrameLocator:
    """FrameLocator proxy that wraps returned locators with auto wait."""

    def __init__(self, frame_locator: FrameLocator, timeout: Optional[float]):
        """Store the wrapped frame locator and default wait timeout."""
        self._frame_locator = frame_locator
        self._timeout = timeout

    def __getattribute__(self, item):
        """Preserve Playwright class identity for wrapped frame locators."""
        if item == "__class__":
            frame_locator = object.__getattribute__(self, "_frame_locator")
            return frame_locator.__class__
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        """Delegate frame locator attributes and wrap returned locators."""
        frame_locator = object.__getattribute__(self, "_frame_locator")
        attr = getattr(frame_locator, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return _wrap_result(result, object.__getattribute__(self, "_timeout"))
            return wrapper
        return attr

    def unwrap(self) -> FrameLocator:
        """Return the underlying Playwright frame locator."""
        return object.__getattribute__(self, "_frame_locator")

    def __repr__(self) -> str:
        """Return a debug representation of the wrapped frame locator."""
        frame_locator = object.__getattribute__(self, "_frame_locator")
        return f"AutoWaitFrameLocator({frame_locator!r})"


class AutoWaitPage:
    """Page proxy that ensures locators wait for readiness before interactions."""

    def __init__(self, page: Page, timeout: Optional[float]):
        """Store the wrapped page and default wait timeout."""
        self._page = page
        self._timeout = timeout

    def __getattribute__(self, item):
        """Preserve Playwright class identity for wrapped pages."""
        if item == "__class__":
            page = object.__getattribute__(self, "_page")
            return page.__class__
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        """Delegate page attributes and wrap returned locators."""
        page = object.__getattribute__(self, "_page")
        attr = getattr(page, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return _wrap_result(result, object.__getattribute__(self, "_timeout"))
            return wrapper
        return attr

    def unwrap(self) -> Page:
        """Return the underlying Playwright page."""
        return object.__getattribute__(self, "_page")

    def __repr__(self) -> str:
        """Return a debug representation of the wrapped page."""
        page = object.__getattribute__(self, "_page")
        return f"AutoWaitPage({page!r})"


def run_scenario(scenario_factory, *, wait_timeout: float = DEFAULT_WAIT_TIMEOUT):
    """Run a scenario in Playwright with authenticated auto-waiting page access."""
    with sync_playwright() as playwright:
        auth = AuthManager(playwright)
        try:
            browser, context = auth.new_context()
        except PlaywrightError as exc:
            if is_missing_browser_error(exc):
                raise ScenarioRunnerError(missing_browser_message()) from exc
            raise
        page = context.pages[0] if context.pages else context.new_page()

        page.set_default_timeout(wait_timeout)
        page.set_default_navigation_timeout(wait_timeout)

        scenario = scenario_factory()
        scenario_name = scenario.__class__.__name__
        logger.info("Running scenario {}", scenario_name)

        try:
            scenario.run(AutoWaitPage(page, wait_timeout))
        except Exception:
            logger.exception("Scenario {} failed", scenario_name)
            raise
        else:
            logger.info("Scenario {} completed", scenario_name)
        finally:
            context.close()
            browser.close()
