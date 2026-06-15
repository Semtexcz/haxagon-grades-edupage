"""Command line entry point for EduPage automation scenarios."""

from pathlib import Path
from typing import Annotated

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright
import typer

from edu_page_automat import setup_login
from edu_page_automat.classroom_grades import convert_classroom_grades_csv
from edu_page_automat.grade_diff import write_grade_diff_csv
from edu_page_automat.logging_config import setup_logging
from edu_page_automat.playwright_browsers import (
    install_firefox_browser,
    is_missing_browser_error,
    missing_browser_message,
)
from edu_page_automat.scenarios.create_task import CreateTaskScenario
from edu_page_automat.scenarios.export_grades import ExportGradesScenario
from edu_page_automat.scenarios.fill_grades import FillGradesScenario

logger = setup_logging()
SCENARIOS = [CreateTaskScenario, FillGradesScenario, ExportGradesScenario]

cli = typer.Typer(help="EduPage automation CLI.")


@cli.command("list")
def list_commands():
    """List available scenarios."""
    for scenario_cls in SCENARIOS:
        typer.echo(scenario_cls.__name__.replace("Scenario", "").lower())


@cli.command()
def login():
    """Force a new login and save session."""
    with sync_playwright() as playwright:
        try:
            setup_login.run(playwright)
        except PlaywrightError as exc:
            if is_missing_browser_error(exc):
                typer.echo(missing_browser_message(), err=True)
                raise typer.Exit(code=1) from exc
            raise
        typer.echo(f"Login complete, session saved to {setup_login.AUTH_FILE}.")


@cli.command("install-browsers")
def install_browsers():
    """Install Playwright browser binaries used by EduPage automation."""
    try:
        install_firefox_browser()
    except Exception as exc:
        typer.echo(f"Playwright browser installation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo("Playwright Firefox browser installed.")


@cli.command("convert-classroom-grades")
def convert_classroom_grades(
    input_csv: Annotated[
        Path,
        typer.Option(
            ...,
            "--input-csv",
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Path to a Google Classroom grade export CSV.",
        ),
    ],
    output_csv: Annotated[
        Path,
        typer.Option(
            ...,
            "--output-csv",
            file_okay=True,
            dir_okay=False,
            help="Path where the EduPage-compatible grade CSV should be written.",
        ),
    ],
    topics: Annotated[
        list[str] | None,
        typer.Option("--topic", help="Only convert rows from this Google Classroom topic. Can be repeated."),
    ] = None,
    tasks: Annotated[
        list[str] | None,
        typer.Option("--task", help="Only convert this Google Classroom task. Can be repeated."),
    ] = None,
):
    """Convert Google Classroom grades into EduPage grade CSV input."""
    try:
        row_count = convert_classroom_grades_csv(
            input_csv,
            output_csv,
            topics=tuple(topics or []),
            tasks=tuple(tasks or []),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {row_count} grade rows to {output_csv}")


@cli.command("diff-grades")
def diff_grades(
    current_csv: Annotated[
        Path,
        typer.Option(
            ...,
            "--current-csv",
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Path to the current EduPage grade export CSV.",
        ),
    ],
    truth_csv: Annotated[
        Path,
        typer.Option(
            ...,
            "--truth-csv",
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Path to the source-of-truth grade CSV.",
        ),
    ],
    output_csv: Annotated[
        Path,
        typer.Option(
            ...,
            "--output-csv",
            file_okay=True,
            dir_okay=False,
            help="Path where the fill-grades diff CSV should be written.",
        ),
    ],
):
    """Write only grade rows that need to be saved to EduPage."""
    try:
        summary = write_grade_diff_csv(current_csv, truth_csv, output_csv)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(
        f"Wrote {summary.written_rows} grade rows to {output_csv} "
        f"(equal={summary.equal_rows}, empty-target={summary.skipped_empty_target_rows}, "
        f"missing-current={summary.missing_current_rows}, extra-current={summary.extra_current_rows})"
    )

for scenario_cls in SCENARIOS:
    scenario_cls.register_cli(cli)


def main():
    """Run the Typer CLI application."""
    cli()


if __name__ == "__main__":
    main()
