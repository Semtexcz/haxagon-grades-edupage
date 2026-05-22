"""Reference Playwright recording for the original grade rewrite flow.

This script is not part of the packaged CLI. It is retained only as a sanitized
recording that helped derive `fill-grades --overwrite-existing`.
Credentials are read from `EDUPAGE_USERNAME` and `EDUPAGE_PASSWORD`.
"""

import os

from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    """Run the original recorded grade-rewrite flow with credentials from env vars."""
    username_value = os.environ["EDUPAGE_USERNAME"]
    password_value = os.environ["EDUPAGE_PASSWORD"]

    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://1itg.edupage.org/")
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").fill(username_value)
    page.get_by_role("button", name="Další").click()
    page.get_by_role("textbox", name="Zadejte heslo:").click()
    page.get_by_role("textbox", name="Zadejte heslo:").fill(password_value)
    page.get_by_role("button", name="Další").click()
    page.get_by_text("Zapamatovat si přihlašovací").click()
    page.get_by_role("button", name="Uložit").click()
    page.get_by_role("button", name="Žádna hodina ").click()
    page.get_by_role("button", name="Zobrazit 2.png Informatika ").click()
    page.get_by_role("button", name="Známky").click()
    page.locator(".znamkyPriemerRow > td:nth-child(4)").click()
    page.get_by_role("cell", name="→ 1 ").locator("span").nth(1).click()
    page.get_by_role("cell", name="→ 1 ").locator("span").nth(1).click()
    page.get_by_role("cell", name="→ 1 + nová známka ").locator("span").nth(1).press("ArrowRight")
    page.get_by_role("cell", name="→ 1 ").locator("span").nth(1).click()
    page.get_by_role("cell", name="→ 1 ").locator("span").nth(1).click()
    page.get_by_role("cell", name="→ 1 + nová známka ").locator("span").nth(1).press("ArrowRight")
    page.get_by_role("cell", name="→ 1 + nová známka ").locator("span").nth(1).click()
    page.get_by_role("cell", name="→ 1 + nová známka ").locator("span").nth(1).fill("80")
    page.get_by_text("90", exact=True).nth(1).click()
    page.get_by_text("90", exact=True).nth(1).press("ArrowRight")
    page.get_by_text("90", exact=True).nth(1).fill("m")
    page.locator("a").filter(has_text="Uložitzměny").click()
    page.get_by_role("button", name="Uložit").first.click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
