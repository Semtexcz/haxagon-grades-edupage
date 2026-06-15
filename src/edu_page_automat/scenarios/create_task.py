"""Scenario for creating EduPage tests or assignments from CLI task data."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Iterable, List

import typer

from edu_page_automat.logging_config import setup_logging
from edu_page_automat.scenario_runner import ScenarioRunnerError, run_scenario
from edu_page_automat.scenarios.base import Scenario

logger = setup_logging()

TASK_ROW_LOCATOR = ".znamkyUdalostHeader"
_CSV_SAMPLE_SIZE = 2048


@dataclass(frozen=True)
class TaskDefinition:
    """Single EduPage task definition parsed from CLI or CSV input."""

    name: str
    points: int


def _load_tasks_from_csv(csv_path: Path) -> List[TaskDefinition]:
    """Load task definitions from a CSV file with flexible header names."""
    if not csv_path.exists():
        raise ValueError(f"CSV file {csv_path} does not exist")

    logger.debug("Loading tasks from CSV {}", csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        sample = handle.read(_CSV_SAMPLE_SIZE)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;	")
        except (csv.Error, TypeError):
            dialect = csv.excel

        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header with columns 'name' (or 'task') and 'points'")

        headers = [header.strip().lower() for header in reader.fieldnames]
        name_header = None
        points_header = None
        for original, header in zip(reader.fieldnames, headers):
            if header in {"name", "task", "nazev"} and name_header is None:
                name_header = original
            if header in {"points", "point", "score", "body"} and points_header is None:
                points_header = original

        if not name_header or not points_header:
            raise ValueError("CSV header must contain columns 'name' (or 'task') and 'points'")

        tasks: List[TaskDefinition] = []
        for row_index, row in enumerate(reader, start=2):
            name_value = (row.get(name_header) or "").strip()
            points_value = (row.get(points_header) or "").strip()

            if not name_value:
                raise ValueError(f"Row {row_index}: missing task name")

            try:
                points_int = int(points_value)
            except ValueError as exc:
                raise ValueError(f"Row {row_index}: invalid integer for points -> '{points_value}'") from exc

            tasks.append(TaskDefinition(name=name_value, points=points_int))

    if not tasks:
        raise ValueError("CSV file did not contain any task rows")

    return tasks


class CreateTaskScenario(Scenario):
    """Create one or more EduPage test or assignment records."""

    def __init__(self, class_: str, tasks: Iterable[TaskDefinition], subject: str = "Informatika", category: str | None = None):
        """Initialize the target class, subject, category, and task list."""
        self.class_ = class_
        self.subject = subject
        self.category = category
        self.tasks: List[TaskDefinition] = list(tasks)
        if not self.tasks:
            raise ValueError("At least one task must be provided")

    def run(self, page):
        """Select the target course and create every missing task."""
        page.goto("https://1itg.edupage.org/user/", wait_until="domcontentloaded")

        page.locator(".edubarCourseListBtn").click()
        locator = page.locator("div.ecourse-standards-subject-title").filter(
            has=page.locator("div.className", has_text=self.class_)
        ).filter(
            has=page.locator("div.subjectName", has_text=self.subject)
        )

        locator.click()
        logger.debug(f"Selected subject {self.subject} for class {self.class_}")

        page.locator("a.edubarCourseModuleLink", has_text="Známky").click()

        locator_configured = "TODO" not in TASK_ROW_LOCATOR
        if not locator_configured:
            logger.warning("Task row locator not configured; skipping duplicate check")

        created = 0
        for task in self.tasks:
            if locator_configured and not self._task_missing(page, task):
                continue

            self._create_task(page, task)
            created += 1

        logger.info(
            "Task creation finished for class {}, subject {} (created={}, skipped={})",
            self.class_,
            self.subject,
            created,
            len(self.tasks) - created,
        )

    def _task_missing(self, page, task: TaskDefinition) -> bool:
        """Return whether the task does not already appear in the grade table."""
        existing_task = page.locator(TASK_ROW_LOCATOR).filter(has_text=task.name)
        existing_count = existing_task.count()
        logger.debug("Found {} existing tasks matching {}", existing_count, task.name)
        if existing_count > 0:
            logger.info(
                "Task {} already exists for class {} and subject {}; skipping creation",
                task.name,
                self.class_,
                self.subject,
            )
            return False
        return True

    def _create_task(self, page, task: TaskDefinition):
        """Fill and submit the EduPage new-task form."""
        logger.info("Creating new task: {}", task.name)

        new_task_button = page.locator("a").filter(has_text="Nová písemka/ zkoušení")
        new_task_button.wait_for(state="visible", timeout=10000)
        new_task_button.click()

        page.wait_for_selector('input[name="p_meno"]', state="visible", timeout=15000)
        page.locator('input[name="p_meno"]').fill(task.name)

        dropdown = page.locator('select[name="kategoriaid"]')
        dropdown.wait_for(state="attached", timeout=15000)

        if self.category:
            try:
                logger.debug("Selecting category by label: {}", self.category)
                dropdown.select_option(label=self.category)
            except Exception as e:
                logger.warning("Selecting by label failed ({}), trying JS fallback", e)
                page.evaluate(
                    """(labelText) => {
                        const select = document.querySelector('select[name="kategoriaid"]');
                        if (!select) return;
                        const option = Array.from(select.options).find(opt => opt.text.trim() === labelText);
                        if (option) {
                            select.value = option.value;
                            select.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }""",
                    self.category,
                )
        else:
            logger.warning("No category specified, selecting first available option")
            page.evaluate("""
                () => {
                    const select = document.querySelector('select[name="kategoriaid"]');
                    if (select && select.options.length > 0) {
                        select.selectedIndex = 0;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            """)

        page.get_by_role("spinbutton").wait_for(state="visible", timeout=10000)
        page.get_by_role("spinbutton").fill(str(task.points))

        save_button = page.get_by_role("button", name="Uložit")
        save_button.wait_for(state="visible", timeout=10000)
        save_button.click()

        logger.info(
            "Created task {} for class {} with {} points (subject {}, category {})",
            task.name,
            self.class_,
            task.points,
            self.subject,
            self.category or "(default)",
        )

    @classmethod
    def register_cli(cls, cli_group):
        """Register the `create-task` command on the provided Typer app."""
        @cli_group.command("create-task")
        def run_task(
            class_: Annotated[str, typer.Option(..., "--class", help="Class name (e.g., 3.gpu)")],
            task_name: Annotated[str | None, typer.Option("--name", help="Task name (use with --points)")] = None,
            task_points: Annotated[int | None, typer.Option("--points", help="Task points (use with --name)")] = None,
            task_defs: Annotated[
                list[str] | None,
                typer.Option("--task", help="Task definition in format 'name:points'. Repeat for multiple entries."),
            ] = None,
            task_csv: Annotated[
                Path | None,
                typer.Option(
                    "--task-csv",
                    exists=True,
                    file_okay=True,
                    dir_okay=False,
                    help="Path to CSV file with columns 'name' and 'points'",
                ),
            ] = None,
            subject: Annotated[
                str,
                typer.Option("--subject", help="Subject name in EduPage course list", show_default=True),
            ] = "Informatika",
            category: Annotated[
                str | None,
                typer.Option(
                    "--category",
                    help="Dropdown label for task category (e.g., 'Dan - Linux' or 'Písemka')",
                ),
            ] = None,
        ):
            """Create a new test/task in EduPage."""
            tasks: List[TaskDefinition] = []

            if task_csv:
                try:
                    tasks.extend(_load_tasks_from_csv(task_csv))
                except ValueError as exc:
                    raise typer.BadParameter(str(exc)) from exc

            if task_defs:
                for definition in task_defs:
                    try:
                        name_part, points_part = definition.split(":", 1)
                        task = TaskDefinition(name=name_part.strip(), points=int(points_part.strip()))
                    except ValueError as exc:
                        raise typer.BadParameter(
                            "Each --task must be in format 'name:points' with integer points."
                        ) from exc
                    tasks.append(task)

            if not tasks:
                if not task_name or task_points is None:
                    raise typer.BadParameter(
                        "Provide tasks via --task-csv/--task or supply both --name and --points."
                    )
                tasks.append(TaskDefinition(name=task_name, points=task_points))

            try:
                run_scenario(lambda: cls(class_, tasks, subject=subject, category=category))
            except ScenarioRunnerError as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(code=1) from exc

if __name__ == "__main__":
    # jednoduchý test bez CLI
    run_scenario(lambda: CreateTaskScenario(
        class_="3.cpu",
        subject="Informatika",
        tasks=[
            TaskDefinition(name="Test/smažu", points=68),
        ],
        category="Dan - Linux",
    ))
