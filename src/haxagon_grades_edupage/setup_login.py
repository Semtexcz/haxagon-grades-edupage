import os
from pathlib import Path
from playwright.sync_api import Playwright, expect

AUTH_FILE = Path("auth.json")

def run(playwright: Playwright, browser=None):
    """
    Provede login a vrátí (browser, context), kde je session již přihlášená.
    Pokud browser není předán, vytvoří se nový.
    """
    base_url = os.environ.get("EDUPAGE_URL", "https://1itg.edupage.org/")
    username_value = os.environ.get("EDUPAGE_USERNAME")
    password_value = os.environ.get("EDUPAGE_PASSWORD")

    if not username_value or not password_value:
        raise RuntimeError("Chybí EDUPAGE_USERNAME a EDUPAGE_PASSWORD v prostředí")

    own_browser = False
    if browser is None:
        browser = playwright.firefox.launch(headless=False, slow_mo=200)
        own_browser = True

    context = browser.new_context()
    page = context.new_page()

    # login flow
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
    print("Login proběhl úspěšně:", page.url)

    # uložit session
    context.storage_state(path=str(AUTH_FILE))
    print(f"Session uložena do {AUTH_FILE}")

    return browser, context


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser, context = run(playwright)
        context.close()
        browser.close()
