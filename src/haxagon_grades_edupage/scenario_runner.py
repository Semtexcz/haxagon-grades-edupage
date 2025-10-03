from typing import Any, Optional

from playwright.sync_api import FrameLocator, Locator, Page, sync_playwright

from src.haxagon_grades_edupage.auth_manager import AuthManager

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


def _wrap_result(result: Any, timeout: Optional[float]):
    if isinstance(result, Locator):
        return AutoWaitLocator(result, timeout)
    if isinstance(result, FrameLocator):
        return AutoWaitFrameLocator(result, timeout)
    return result


class AutoWaitLocator:
    """Locator proxy that waits for element readiness before key actions."""

    def __init__(self, locator: Locator, timeout: Optional[float]):
        self._locator = locator
        self._timeout = timeout

    def __getattribute__(self, item):
        if item == "__class__":
            locator = object.__getattribute__(self, "_locator")
            return locator.__class__
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        locator = object.__getattribute__(self, "_locator")
        attr = getattr(locator, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                state = _AUTO_WAIT_ACTION_STATES.get(item)
                if state:
                    locator.wait_for(state=state, timeout=object.__getattribute__(self, "_timeout"))
                result = attr(*args, **kwargs)
                return _wrap_result(result, object.__getattribute__(self, "_timeout"))
            return wrapper
        return attr

    def unwrap(self) -> Locator:
        return object.__getattribute__(self, "_locator")

    def __repr__(self) -> str:
        locator = object.__getattribute__(self, "_locator")
        return f"AutoWaitLocator({locator!r})"


class AutoWaitFrameLocator:
    """FrameLocator proxy that wraps returned locators with auto wait."""

    def __init__(self, frame_locator: FrameLocator, timeout: Optional[float]):
        self._frame_locator = frame_locator
        self._timeout = timeout

    def __getattribute__(self, item):
        if item == "__class__":
            frame_locator = object.__getattribute__(self, "_frame_locator")
            return frame_locator.__class__
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        frame_locator = object.__getattribute__(self, "_frame_locator")
        attr = getattr(frame_locator, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return _wrap_result(result, object.__getattribute__(self, "_timeout"))
            return wrapper
        return attr

    def unwrap(self) -> FrameLocator:
        return object.__getattribute__(self, "_frame_locator")

    def __repr__(self) -> str:
        frame_locator = object.__getattribute__(self, "_frame_locator")
        return f"AutoWaitFrameLocator({frame_locator!r})"


class AutoWaitPage:
    """Page proxy that ensures locators wait for readiness before interactions."""

    def __init__(self, page: Page, timeout: Optional[float]):
        self._page = page
        self._timeout = timeout

    def __getattribute__(self, item):
        if item == "__class__":
            page = object.__getattribute__(self, "_page")
            return page.__class__
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        page = object.__getattribute__(self, "_page")
        attr = getattr(page, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return _wrap_result(result, object.__getattribute__(self, "_timeout"))
            return wrapper
        return attr

    def unwrap(self) -> Page:
        return object.__getattribute__(self, "_page")

    def __repr__(self) -> str:
        page = object.__getattribute__(self, "_page")
        return f"AutoWaitPage({page!r})"


def run_scenario(scenario_factory, *, wait_timeout: float = DEFAULT_WAIT_TIMEOUT):
    """Spustí scénář ve Playwrightu s automatickým čekáním na elementy."""
    with sync_playwright() as playwright:
        auth = AuthManager(playwright)
        browser, context = auth.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        page.set_default_timeout(wait_timeout)
        page.set_default_navigation_timeout(wait_timeout)

        scenario = scenario_factory()
        scenario.run(AutoWaitPage(page, wait_timeout))

        context.close()
        browser.close()
