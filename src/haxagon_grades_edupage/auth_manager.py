from pathlib import Path
from playwright.sync_api import Playwright
from src.haxagon_grades_edupage.setup_login import run as setup_login

AUTH_FILE = Path("auth.json")

class AuthManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright

    def has_session(self) -> bool:
        return AUTH_FILE.exists()

    def _is_session_valid(self) -> bool:
        if not self.has_session():
            return False
        browser = self.playwright.firefox.launch(headless=False)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        page = context.new_page()
        page.goto("https://1itg.edupage.org/user/")
        logged_in = "login" not in page.url
        context.close()
        browser.close()
        return logged_in

    def new_context(self):
        """Always returns a valid browser and context with session."""
        if not self.has_session() or not self._is_session_valid():
            # provede login a rovnou vrátí hotový browser+context
            return setup_login(self.playwright)
        # jinak vytvoří context ze session
        browser = self.playwright.firefox.launch(headless=False, slow_mo=200)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        return browser, context
