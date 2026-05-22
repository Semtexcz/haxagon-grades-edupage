import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://1itg.edupage.org/")
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").fill("daniel.kopecky@itgymnazium.cz")
    page.get_by_role("button", name="Další").click()
    page.get_by_role("textbox", name="Zadejte heslo:").click()
    page.get_by_role("textbox", name="Zadejte heslo:").fill("HDgVR8Sy")
    page.get_by_role("button", name="Další").click()
    page.get_by_role("checkbox", name="Zapamatovat si přihlašovací").check()
    page.goto("https://1itg.edupage.org/user/")
    page.get_by_role("button", name="Žádna hodina ").click()
    page.get_by_role("button", name="Zobrazit 2.jpg Informatika ").click()
    page.get_by_role("button", name="Známky").click()
    page.get_by_role("button", name="2.jpg Informatika ").click()
    page.get_by_role("button", name="Zobrazit 2.png Informatika ").click()
    page.get_by_role("cell", name="Žužlavá, Žofie").click()
    page.locator("input[name=\"nzn_-440_-91_132812_P2_1\"]").click()
    page.locator("input[name=\"nzn_-440_-91_132812_P2_1\"]").fill("100")
    page.locator("a").filter(has_text="Uložitzměny").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
