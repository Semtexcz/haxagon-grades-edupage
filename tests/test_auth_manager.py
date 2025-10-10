from types import SimpleNamespace

import pytest

from haxagon_grades_edupage import auth_manager as auth_module
from haxagon_grades_edupage.auth_manager import AuthManager


class DummyPage:
    def __init__(self, final_url: str):
        self._final_url = final_url
        self.url = ""

    def goto(self, unused_url: str):
        self.url = self._final_url


class DummyContext:
    def __init__(self, final_url: str):
        self._final_url = final_url
        self.closed = False

    @property
    def pages(self):
        return []

    def new_page(self):
        return DummyPage(self._final_url)

    def close(self):
        self.closed = True


class DummyBrowser:
    def __init__(self, final_url: str):
        self._final_url = final_url
        self.closed = False
        self.context = None

    def new_context(self, storage_state: str):
        self.storage_state = storage_state
        self.context = DummyContext(self._final_url)
        return self.context

    def close(self):
        self.closed = True


class DummyPlaywright:
    def __init__(self, final_url: str):
        self._final_url = final_url
        self.latest_browser: DummyBrowser | None = None
        self.firefox = SimpleNamespace(launch=self._launch)

    def _launch(self, headless=False, slow_mo=None):
        browser = DummyBrowser(self._final_url)
        self.latest_browser = browser
        return browser


def test_has_session(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    monkeypatch.setattr(auth_module, "AUTH_FILE", auth_file)
    manager = AuthManager(DummyPlaywright("https://example.com"))

    assert manager.has_session() is False

    auth_file.write_text("{}", encoding="utf-8")
    assert manager.has_session() is True


def test_try_open_session_missing_file(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    monkeypatch.setattr(auth_module, "AUTH_FILE", auth_file)
    manager = AuthManager(DummyPlaywright("https://example.com"))

    valid, browser, context = manager.try_open_session()

    assert (valid, browser, context) == (False, None, None)


def test_try_open_session_valid(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text("{}", encoding="utf-8")
    playwright = DummyPlaywright("https://1itg.edupage.org/user/dashboard")
    monkeypatch.setattr(auth_module, "AUTH_FILE", auth_file)
    manager = AuthManager(playwright)

    valid, browser, context = manager.try_open_session(headless=True, slow_mo=0)

    assert valid is True
    assert browser is playwright.latest_browser
    assert context is browser.context
    assert browser.closed is False
    assert context.closed is False


def test_try_open_session_invalid(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text("{}", encoding="utf-8")
    playwright = DummyPlaywright("https://1itg.edupage.org/user/login")
    monkeypatch.setattr(auth_module, "AUTH_FILE", auth_file)
    manager = AuthManager(playwright)

    valid, browser, context = manager.try_open_session()

    assert (valid, browser, context) == (False, None, None)
    assert playwright.latest_browser.closed is True
    assert playwright.latest_browser.context.closed is True


def test_new_context_reuses_valid(monkeypatch):
    manager = AuthManager(DummyPlaywright("https://example.com"))
    monkeypatch.setattr(
        manager,
        "try_open_session",
        lambda headless=False, slow_mo=200: (True, "browser", "context"),
    )

    browser, context = manager.new_context()

    assert (browser, context) == ("browser", "context")


def test_new_context_triggers_login(monkeypatch):
    playwright = DummyPlaywright("https://example.com")
    manager = AuthManager(playwright)
    monkeypatch.setattr(
        manager,
        "try_open_session",
        lambda headless=False, slow_mo=200: (False, None, None),
    )

    captured = {}

    def fake_setup_login(received_playwright):
        captured["playwright"] = received_playwright
        return "browser2", "context2"

    monkeypatch.setattr(auth_module, "setup_login", fake_setup_login)

    browser, context = manager.new_context()

    assert captured["playwright"] is playwright
    assert (browser, context) == ("browser2", "context2")
