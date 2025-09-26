from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False, slow_mo=200)  # slow_mo = zpomalí akce, ať je to přehlednější
    context = browser.new_context()
    page = context.new_page()

    # otevřít stránku a počkat, až se načte
    page.goto("https://1itg.edupage.org/", wait_until="domcontentloaded")

    # kliknout na odkaz "Přihlásit se"
    page.get_by_role("link", name="Přihlásit se pomocí účtu").click()

    # počkat na zobrazení pole pro uživatelské jméno
    username = page.get_by_role("textbox", name="Uživatelské jméno:")
    expect(username).to_be_visible()
    username.fill("daniel.kopecky@itgymnazium.cz")

    # kliknout na "Další" a počkat na přesměrování
    page.get_by_role("button", name="Další").click()

    # počkat na pole pro heslo
    password = page.get_by_role("textbox", name="Zadejte heslo:")
    expect(password).to_be_visible()
    password.fill("HDgVR8Sy")

    # kliknout na "Další"
    page.get_by_role("button", name="Další").click()

    # počkat na checkbox "Zapamatovat si přihlašovací"
    

    # remember = page.locator('[name="remember_usr"]')
    remember = page.locator("label.mainlogin-block-checkbox").nth(0)
    print(remember, remember.count())
    # remember = page.get_by_role("checkbox", name="Zapamatovat si přihlašovací")
    expect(remember).to_be_visible()
    remember.check()

    # kliknout na "Další"
    page.get_by_role("button", name="Uložit").click()


    # po úspěšném loginu počkat na cílovou stránku
    page.wait_for_url("https://1itg.edupage.org/user/**")

    print("Login proběhl úspěšně:", page.url)

    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
