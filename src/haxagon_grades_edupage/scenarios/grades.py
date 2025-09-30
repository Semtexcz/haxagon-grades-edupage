import click
from .base import Scenario
from scenario_runner import run_scenario

class GradesScenario(Scenario):
    def __init__(self, year: int):
        self.year = year

    def run(self, page):
        page.goto("https://1itg.edupage.org/user/")
        page.click("text=Známky")
        page.select_option("select#year", str(self.year))
        print(f"Opened grades for year {self.year}")

    @classmethod
    def register_cli(cls, cli_group):
        @cli_group.command("grades")
        @click.option("--year", type=int, default=2025, help="School year")
        def run_grades(year):
            """Open grades for a specific year."""
            run_scenario(lambda: cls(year=year))
