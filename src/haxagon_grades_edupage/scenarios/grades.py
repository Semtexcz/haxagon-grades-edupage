import click
from .base import Scenario

class GradesScenario(Scenario):
    def __init__(self, year: int):
        self.year = year

    def run(self, page):
        page.goto("https://1itg.edupage.org/user/")
        page.click("text=Známky")
        # příklad filtrování
        page.select_option("select#year", str(self.year))
        print(f"Opened grades for year {self.year}: {page.url}")

    @classmethod
    def register_cli(cls, cli_group):
        @cli_group.command("grades")
        @click.option("--year", type=int, default=2025, help="School year")
        def run_grades(year):
            """Open grades for a specific year."""
            from auth_manager import AuthManager
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                auth = AuthManager(playwright)
                browser, context = auth.new_context()
                page = context.new_page()

                scenario = cls(year=year)
                scenario.run(page)

                context.close()
                browser.close()
