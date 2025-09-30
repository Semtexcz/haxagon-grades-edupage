import click
from playwright.sync_api import sync_playwright
from auth_manager import AuthManager

# import všech scénářů
from scenarios.grades import GradesScenario
from scenarios.timetable import TimetableScenario

SCENARIOS = [GradesScenario, TimetableScenario]

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
        from setup_login import run as setup_login
        setup_login(playwright)
        click.echo("Login complete, session saved.")

# --- zaregistrovat scénáře ---
for scenario_cls in SCENARIOS:
    scenario_cls.register_cli(cli)

if __name__ == "__main__":
    cli()
