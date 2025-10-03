from pathlib import Path
from playwright.sync_api import Playwright
from src.haxagon_grades_edupage.setup_login import run as setup_login
from src.haxagon_grades_edupage.logging_config import setup_logging

AUTH_FILE = Path("auth.json")
logger = setup_logging()

class AuthManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright

    def has_session(self) -> bool:
        return AUTH_FILE.exists()

    def try_open_session(self, headless=False, slow_mo=200):
        """
        Pokusí se otevřít browser+context se session.
        Vrací tuple (is_valid, browser, context).
        Pokud session neexistuje -> (False, browser, context=None).
        """
        if not self.has_session():
            logger.debug("No stored session found")
            return False, None, None

        browser = self.playwright.firefox.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        page = context.new_page()
        page.goto("https://1itg.edupage.org/user/")

        logged_in = "login" not in page.url
        if not logged_in:
            logger.debug("Stored session invalid, discarding")
            context.close()
            browser.close()
            return False, None, None

        logger.debug("Stored session validated")
        return True, browser, context

    def new_context(self):
        """
        Vrátí vždy validní (browser, context) se session.
        Pokud není platná, spustí setup_login.
        """
        valid, browser, context = self.try_open_session(headless=False, slow_mo=200)
        if valid:
            logger.info("Reusing existing EduPage session")
            return browser, context

        logger.info("Session missing or invalid, performing login")
        # pokud session není platná, udělej login a vrať přihlášený browser+context
        return setup_login(self.playwright)
