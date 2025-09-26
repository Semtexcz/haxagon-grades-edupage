from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"

def run(playwright):
    browser = playwright.firefox.launch(headless=False, slow_mo=200)
    # vytvoří nový context, ale už se session z auth.json
    context = browser.new_context(storage_state=AUTH_FILE)

    page = context.new_page()
    page.goto("https://1itg.edupage.org/user/")

    print("Načtená stránka:", page.url)
    print("Titulek:", page.title())

    # teď jste rovnou přihlášený, můžete spouštět další akce
    # např. otevřít známky, rozvrh apod.

    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
