"""Command line entry point for EduPage automation scenarios."""

import click
from playwright.sync_api import sync_playwright

from edu_page_automat import setup_login
from edu_page_automat.logging_config import setup_logging
from edu_page_automat.scenarios.create_task import CreateTaskScenario
from edu_page_automat.scenarios.fill_grades import FillGradesScenario

logger = setup_logging()
SCENARIOS = [CreateTaskScenario, FillGradesScenario]

@click.group()
def cli():
    """EduPage automation CLI."""
    pass

@cli.command()
def list():
    """List available scenarios."""
    for scenario_cls in SCENARIOS:
        click.echo(scenario_cls.__name__.replace("Scenario", "").lower())

@cli.command()
def login():
    """Force a new login and save session."""
    with sync_playwright() as playwright:
        setup_login.run(playwright)
        click.echo("Login complete, session saved.")

for scenario_cls in SCENARIOS:
    scenario_cls.register_cli(cli)

if __name__ == "__main__":
    cli()
