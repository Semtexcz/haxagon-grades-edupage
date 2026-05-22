"""Reference Playwright recording for the original create-task flow.

This script is not part of the packaged CLI. Keep it as a sanitized reference
only; active implementation lives in `edu_page_automat.scenarios.create_task`.
"""

import os
import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    """Run the original recorded browser flow with credentials from env vars."""
    username_value = os.environ["EDUPAGE_USERNAME"]
    password_value = os.environ["EDUPAGE_PASSWORD"]

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://1itg.edupage.org/")
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").fill(username_value)
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").fill(username_value)
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowRight")
    page.get_by_role("textbox", name="Uživatelské jméno:").fill(username_value)
    page.get_by_role("button", name="Další").click()
    page.get_by_role("textbox", name="Zadejte heslo:").click()
    page.get_by_role("textbox", name="Zadejte heslo:").fill(password_value)
    page.get_by_role("button", name="Další").click()
    page.get_by_role("button", name="Nic neukládat a víc se neptát").click()


    # Scenario starts here.
    class_ = "3.gpu"
    task_name = "Test/smažu"
    task_points = "68"

    page.locator("#edubar").get_by_role("link", name="Známky").click()
    page.get_by_text(class_).nth(1).click()
    page.locator("a").filter(has_text="Nová písemka/ zkoušení").click()
    page.locator("input[name=\"p_meno\"]").click()
    page.locator("input[name=\"p_meno\"]").fill(task_name)
    page.locator("select[name=\"kategoriaid\"]").select_option("3")
    page.get_by_role("spinbutton").click()
    page.get_by_role("spinbutton").fill(task_points)
    page.get_by_role("button", name="Uložit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
