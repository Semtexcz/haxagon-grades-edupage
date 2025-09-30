from playwright.sync_api import sync_playwright
from auth_manager import AuthManager

def run_scenario(scenario_factory):
    """
    scenario_factory je funkce (lambda) nebo callable,
    která vrací instanci scénáře s připravenými parametry.
    """
    with sync_playwright() as playwright:
        auth = AuthManager(playwright)
        browser, context = auth.new_context()
        page = context.new_page()

        scenario = scenario_factory()
        scenario.run(page)

        context.close()
        browser.close()
