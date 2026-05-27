"""Session management for EduPage Playwright contexts."""

from playwright.sync_api import Playwright

from edu_page_automat.auth_storage import get_auth_file_path
from edu_page_automat.logging_config import setup_logging
from edu_page_automat.setup_login import run as setup_login

AUTH_FILE = get_auth_file_path()
logger = setup_logging()

class AuthManager:
    """Create authenticated Playwright contexts for EduPage scenarios."""

    def __init__(self, playwright: Playwright):
        """Store the Playwright driver used to launch browsers."""
        self.playwright = playwright

    def has_session(self) -> bool:
        """Return whether a stored EduPage session file is available."""
        return AUTH_FILE.exists()

    def try_open_session(self, headless=False, slow_mo=200):
        """Try to open and validate the stored EduPage session."""
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
        """Return a valid authenticated `(browser, context)` pair."""
        valid, browser, context = self.try_open_session(headless=False, slow_mo=200)
        if valid:
            logger.info("Reusing existing EduPage session")
            return browser, context

        logger.info("Session missing or invalid, performing login")
        return setup_login(self.playwright, auth_file=AUTH_FILE)
