"""Command line entry point for EduPage automation scenarios."""

from pathlib import Path

import click
from playwright.sync_api import sync_playwright

from edu_page_automat import setup_login
from edu_page_automat.classroom_grades import convert_classroom_grades_csv
from edu_page_automat.logging_config import setup_logging
from edu_page_automat.scenarios.create_task import CreateTaskScenario
from edu_page_automat.scenarios.export_grades import ExportGradesScenario
from edu_page_automat.scenarios.fill_grades import FillGradesScenario

logger = setup_logging()
SCENARIOS = [CreateTaskScenario, FillGradesScenario, ExportGradesScenario]

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


@cli.command("convert-classroom-grades")
@click.option(
    "--input-csv",
    "input_csv",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    required=True,
    help="Path to a Google Classroom grade export CSV.",
)
@click.option(
    "--output-csv",
    "output_csv",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Path where the EduPage-compatible grade CSV should be written.",
)
@click.option("--topic", "topics", multiple=True, help="Only convert rows from this Google Classroom topic. Can be repeated.")
@click.option("--task", "tasks", multiple=True, help="Only convert this Google Classroom task. Can be repeated.")
def convert_classroom_grades(input_csv: Path, output_csv: Path, topics: tuple[str, ...], tasks: tuple[str, ...]):
    """Convert Google Classroom grades into EduPage grade CSV input."""
    try:
        row_count = convert_classroom_grades_csv(input_csv, output_csv, topics=topics, tasks=tasks)
    except ValueError as exc:
        raise click.BadParameter(str(exc)) from exc
    click.echo(f"Wrote {row_count} grade rows to {output_csv}")

for scenario_cls in SCENARIOS:
    scenario_cls.register_cli(cli)

if __name__ == "__main__":
    cli()
