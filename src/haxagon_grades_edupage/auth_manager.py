from pathlib import Path

from playwright.sync_api import Playwright

AUTH_FILE = Path("auth.json")

class AuthManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright

    def has_session(self) -> bool:
        return AUTH_FILE.exists()

    def _is_session_valid(self) -> bool:
        """Try to open user page and check if we are logged in."""
        browser = self.playwright.firefox.launch(headless=False)
        context = browser.new_context(storage_state=str(AUTH_FILE)) if self.has_session() else browser.new_context()
        page = context.new_page()
        page.goto("https://1itg.edupage.org/user/")

        logged_in = "login" not in page.url
        context.close()
        browser.close()
        return logged_in

    def ensure_session(self):
        if not self.has_session() or not self._is_session_valid():
            from src.haxagon_grades_edupage.setup_login import run as setup_login
            setup_login(self.playwright)

    def new_context(self):
        """Always returns a valid context with session."""
        self.ensure_session()
        browser = self.playwright.firefox.launch(headless=False, slow_mo=200)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        return browser, context