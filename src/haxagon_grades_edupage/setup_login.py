import os
from playwright.sync_api import Playwright, sync_playwright, expect

AUTH_FILE = "auth.json"

def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False, slow_mo=200)
    context = browser.new_context()
    page = context.new_page()

    # otevřít stránku a počkat, až se načte
    page.goto("https://1itg.edupage.org/", wait_until="domcontentloaded")

    # kliknout na odkaz "Přihlásit se"
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()

    # uživatelské jméno
    username = page.get_by_role("textbox", name="Uživatelské jméno:")
    expect(username).to_be_visible()
    username.fill("daniel.kopecky@itgymnazium.cz")
    page.get_by_role("button", name="Další").click()

    # heslo z environment variable
    password_value = os.environ.get("EDUPAGE_PASSWORD")
    if not password_value:
        raise RuntimeError("Heslo není nastaveno v EDUPAGE_PASSWORD")

    password = page.get_by_role("textbox", name="Zadejte heslo:")
    expect(password).to_be_visible()
    password.fill(password_value)
    page.get_by_role("button", name="Další").click()

    remember = page.locator("label.mainlogin-block-checkbox").nth(0)
    expect(remember).to_be_visible()
    remember.check()

    # kliknout na "Uložit"
    page.get_by_role("button", name="Uložit").click()

    # počkat na cílovou stránku
    page.wait_for_url("https://1itg.edupage.org/user/**")
    print("Login proběhl úspěšně:", page.url)

    # uložit session
    context.storage_state(path=AUTH_FILE)
    print(f"Session uložena do {AUTH_FILE}")

    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
