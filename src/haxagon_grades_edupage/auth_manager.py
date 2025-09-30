import os
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright

AUTH_FILE = Path("auth.json")

class AuthManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright

    def has_session(self) -> bool:
        return AUTH_FILE.exists()

    def ensure_session(self):
        if not self.has_session():
            from setup_login import run as setup_login
            setup_login(self.playwright)

    def new_context(self):
        """Always returns a valid context with session."""
        self.ensure_session()
        browser = self.playwright.firefox.launch(headless=False, slow_mo=200)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        return browser, context