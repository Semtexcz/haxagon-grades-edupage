from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from haxagon_grades_edupage import scenario_runner as sr


class DummyLocator:
    def __init__(self):
        self.wait_calls = []
        self.click_calls = []

    def wait_for(self, **kwargs):
        self.wait_calls.append(kwargs)

    def click(self, *args, **kwargs):
        self.click_calls.append((args, kwargs))
        return DummyLocator()

    def bounding_box(self):
        return {"width": 10}


class DummyFrameLocator:
    def __init__(self):
        self.locator_calls = 0

    def locator(self):
        self.locator_calls += 1
        return DummyLocator()


class DummyPage:
    def __init__(self):
        self.locator_calls = []

    def locator(self, selector):
        self.locator_calls.append(selector)
        return DummyLocator()


def test_auto_wait_locator_waits_and_wraps(monkeypatch):
    monkeypatch.setattr(sr, "Locator", DummyLocator)
    locator = DummyLocator()
    auto = sr.AutoWaitLocator(locator, timeout=123)

    result = auto.click()

    assert locator.wait_calls == [{"state": "visible", "timeout": 123}]
    assert locator.click_calls == [((), {})]
    assert isinstance(result, sr.AutoWaitLocator)


def test_auto_wait_locator_passthrough(monkeypatch):
    monkeypatch.setattr(sr, "Locator", DummyLocator)
    locator = DummyLocator()
    auto = sr.AutoWaitLocator(locator, timeout=50)

    assert auto.bounding_box() == {"width": 10}
    assert locator.wait_calls == []


def test_auto_wait_frame_locator_wraps(monkeypatch):
    monkeypatch.setattr(sr, "FrameLocator", DummyFrameLocator)
    monkeypatch.setattr(sr, "Locator", DummyLocator)
    frame = DummyFrameLocator()
    auto = sr.AutoWaitFrameLocator(frame, timeout=200)

    result = auto.locator()

    assert frame.locator_calls == 1
    assert isinstance(result, sr.AutoWaitLocator)


def test_auto_wait_page_wraps_locator(monkeypatch):
    monkeypatch.setattr(sr, "Locator", DummyLocator)
    page = DummyPage()
    auto_page = sr.AutoWaitPage(page, timeout=75)

    locator = auto_page.locator("div.selector")

    assert page.locator_calls == ["div.selector"]
    assert isinstance(locator, sr.AutoWaitLocator)


def test_run_scenario_happy_path(monkeypatch):
    events = []

    class FakePage:
        def __init__(self):
            self.set_default_timeout_calls = []
            self.set_default_navigation_timeout_calls = []

        def set_default_timeout(self, value):
            self.set_default_timeout_calls.append(value)

        def set_default_navigation_timeout(self, value):
            self.set_default_navigation_timeout_calls.append(value)

    class FakeContext:
        def __init__(self):
            self.pages = [FakePage()]

        def new_page(self):
            page = FakePage()
            self.pages.append(page)
            return page

        def close(self):
            events.append("context.close")

    class FakeBrowser:
        def close(self):
            events.append("browser.close")

    class FakeAuthManager:
        def __init__(self, playwright):
            events.append(("auth.init", playwright))

        def new_context(self):
            return FakeBrowser(), FakeContext()

    class DummyCM:
        def __enter__(self):
            events.append("playwright.enter")
            return "playwright"

        def __exit__(self, exc_type, exc, tb):
            events.append(("playwright.exit", exc_type))

    def fake_sync_playwright():
        return DummyCM()

    monkeypatch.setattr(sr, "sync_playwright", fake_sync_playwright)
    monkeypatch.setattr(sr, "AuthManager", FakeAuthManager)

    received_pages = []
    captured = {}

    class DummyScenario:
        def run(self, page):
            received_pages.append(page)
            captured["page"] = page.unwrap()

    sr.run_scenario(lambda: DummyScenario(), wait_timeout=5000)

    assert events == [
        "playwright.enter",
        ("auth.init", "playwright"),
        "context.close",
        "browser.close",
        ("playwright.exit", None),
    ]
    assert len(received_pages) == 1
    assert isinstance(received_pages[0], sr.AutoWaitPage)
    assert captured["page"].set_default_timeout_calls == [5000]
    assert captured["page"].set_default_navigation_timeout_calls == [5000]


def test_run_scenario_propagates_error(monkeypatch):
    events = []

    class FakeContext:
        def __init__(self):
            self.pages = [SimpleNamespace(set_default_timeout=lambda *a: None, set_default_navigation_timeout=lambda *a: None)]

        def close(self):
            events.append("context.close")

    class FakeBrowser:
        def close(self):
            events.append("browser.close")

    class FakeAuthManager:
        def __init__(self, playwright):
            events.append(("auth.init", playwright))

        def new_context(self):
            return FakeBrowser(), FakeContext()

    class DummyCM:
        def __enter__(self):
            events.append("playwright.enter")
            return "playwright"

        def __exit__(self, exc_type, exc, tb):
            events.append(("playwright.exit", exc_type))

    def fake_sync_playwright():
        return DummyCM()

    monkeypatch.setattr(sr, "sync_playwright", fake_sync_playwright)
    monkeypatch.setattr(sr, "AuthManager", FakeAuthManager)

    class FailingScenario:
        def run(self, page):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        sr.run_scenario(lambda: FailingScenario())

    assert events == [
        "playwright.enter",
        ("auth.init", "playwright"),
        "context.close",
        "browser.close",
        ("playwright.exit", RuntimeError),
    ]
