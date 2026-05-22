"""Interactive EduPage login flow used when no valid session exists."""

import os
from getpass import getpass
from pathlib import Path

from playwright.sync_api import Playwright, expect

from edu_page_automat.logging_config import setup_logging

AUTH_FILE = Path("auth.json")
logger = setup_logging()

def run(playwright: Playwright, browser=None):
    """Perform login and return an authenticated `(browser, context)` pair."""
    base_url = os.environ.get("EDUPAGE_URL", "https://1itg.edupage.org/")
    username_value = os.environ.get("EDUPAGE_USERNAME")
    password_value = os.environ.get("EDUPAGE_PASSWORD")

    if not username_value or not password_value:
        username_value = input("Login: ")
        password_value = getpass("Password: ")
        os.environ["EDUPAGE_USERNAME"] = username_value
        os.environ["EDUPAGE_PASSWORD"] = password_value

    if not username_value or not password_value:
        raise RuntimeError("Missing EDUPAGE_USERNAME and EDUPAGE_PASSWORD in the environment")

    own_browser = False
    if browser is None:
        browser = playwright.firefox.launch(headless=False, slow_mo=200)
        own_browser = True

    context = browser.new_context()
    page = context.new_page()

    page.goto(base_url, wait_until="domcontentloaded")
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()

    username = page.get_by_role("textbox", name="Uživatelské jméno:")
    expect(username).to_be_visible()
    username.fill(username_value)
    page.get_by_role("button", name="Další").click()

    password = page.get_by_role("textbox", name="Zadejte heslo:")
    expect(password).to_be_visible()
    password.fill(password_value)
    page.get_by_role("button", name="Další").click()

    remember = page.locator("label.mainlogin-block-checkbox").nth(0)
    expect(remember).to_be_visible()
    remember.check()
    page.get_by_role("button", name="Uložit").click()

    page.wait_for_url(f"{base_url}user/**")
    logger.info("Login completed: {}", page.url)

    context.storage_state(path=str(AUTH_FILE))
    logger.info("Session saved to {}", AUTH_FILE)

    return browser, context


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser, context = run(playwright)
        context.close()
        browser.close()
