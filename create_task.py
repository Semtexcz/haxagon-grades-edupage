import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://1itg.edupage.org/")
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").fill("daniel.kopecky@itgmynazium.cz")
    page.get_by_role("textbox", name="Uživatelské jméno:").click()
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowLeft")
    page.get_by_role("textbox", name="Uživatelské jméno:").fill("daniel.kopecky@itgynazium.cz")
    page.get_by_role("textbox", name="Uživatelské jméno:").press("ArrowRight")
    page.get_by_role("textbox", name="Uživatelské jméno:").fill("daniel.kopecky@itgymnazium.cz")
    page.get_by_role("button", name="Další").click()
    page.get_by_role("textbox", name="Zadejte heslo:").click()
    page.get_by_role("textbox", name="Zadejte heslo:").fill("HDgVR8Sy")
    page.get_by_role("button", name="Další").click()
    page.get_by_role("button", name="Nic neukládat a víc se neptát").click()


    ###Zde začíná scénář
    page.locator("#edubar").get_by_role("link", name="Známky").click()
    page.get_by_text("3.gpu").nth(1).click()
    page.locator("a").filter(has_text="Nová písemka/ zkoušení").click()
    page.locator("input[name=\"p_meno\"]").click()
    page.locator("input[name=\"p_meno\"]").fill("Test/smažu")
    page.locator("select[name=\"kategoriaid\"]").select_option("3")
    page.get_by_role("spinbutton").click()
    page.get_by_role("spinbutton").fill("68")
    page.get_by_role("button", name="Uložit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
