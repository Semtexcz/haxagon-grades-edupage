"""Scenario for filling EduPage grade points from CSV rows."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Iterable, List, TypeAlias

import typer

from edu_page_automat.logging_config import setup_logging
from edu_page_automat.scenario_runner import ScenarioRunnerError, run_scenario
from edu_page_automat.scenarios.base import Scenario

logger = setup_logging()

_CSV_SAMPLE_SIZE = 2048
_GRADE_PAGE_URL = "https://1itg.edupage.org/user/"
_TASK_HEADER_LOCATOR = ".znamkyUdalostHeader"
_SAVE_BUTTON_LOCATOR = "a.ulozitBtn"
_STUDENT_LINK_SELECTOR = 'a[href*="studentid="]'
GradeValue: TypeAlias = int | str


@dataclass(frozen=True)
class GradeEntry:
    """Single student grade entry parsed from CSV input."""

    first_name: str
    last_name: str
    task_name: str
    points: GradeValue

    @property
    def student_display_name(self) -> str:
        """Return the EduPage grade-table student label."""
        return f"{self.last_name}, {self.first_name}"


def _normalize_header(header: str) -> str:
    """Normalize CSV header text for flexible column matching."""
    return header.strip().casefold().replace(" ", "_").replace("-", "_")


def _find_header(fieldnames: list[str], accepted_names: set[str], label: str) -> str:
    """Find a required CSV header by accepted normalized names."""
    for fieldname in fieldnames:
        if _normalize_header(fieldname) in accepted_names:
            return fieldname
    raise ValueError(f"CSV header must contain a column for {label}")


def _parse_grade_value(value: str, row_index: int) -> GradeValue:
    """Parse a CSV grade value accepted by EduPage grade inputs."""
    normalized_value = value.strip()
    if normalized_value.casefold() == "m":
        return "m"

    try:
        return int(normalized_value)
    except ValueError as exc:
        raise ValueError(f"Row {row_index}: invalid grade value -> '{value}'") from exc


def _load_grade_entries_from_csv(csv_path: Path) -> List[GradeEntry]:
    """Load grade entries from a CSV file with flexible header names."""
    if not csv_path.exists():
        raise ValueError(f"CSV file {csv_path} does not exist")

    logger.debug("Loading grades from CSV {}", csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        sample = handle.read(_CSV_SAMPLE_SIZE)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except (csv.Error, TypeError):
            dialect = csv.excel

        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header")

        first_name_header = _find_header(reader.fieldnames, {"first_name", "jmeno", "name"}, "first name")
        last_name_header = _find_header(reader.fieldnames, {"last_name", "prijmeni", "surname"}, "last name")
        task_name_header = _find_header(
            reader.fieldnames,
            {"task_name", "task", "uloha", "jmeno_ulohy", "nazev_ulohy"},
            "task name",
        )
        points_header = _find_header(reader.fieldnames, {"points", "point", "score", "body", "pocet_bodu"}, "points")

        entries: List[GradeEntry] = []
        for row_index, row in enumerate(reader, start=2):
            first_name = (row.get(first_name_header) or "").strip()
            last_name = (row.get(last_name_header) or "").strip()
            task_name = (row.get(task_name_header) or "").strip()
            points_value = (row.get(points_header) or "").strip()

            if not first_name:
                raise ValueError(f"Row {row_index}: missing first name")
            if not last_name:
                raise ValueError(f"Row {row_index}: missing last name")
            if not task_name:
                raise ValueError(f"Row {row_index}: missing task name")
            if not points_value:
                logger.debug("Skipping row {} without points", row_index)
                continue

            points = _parse_grade_value(points_value, row_index)

            entries.append(
                GradeEntry(
                    first_name=first_name,
                    last_name=last_name,
                    task_name=task_name,
                    points=points,
                )
            )

    if not entries:
        raise ValueError("CSV file did not contain any grade rows")

    return entries


class FillGradesScenario(Scenario):
    """Fill grade-table point inputs for existing EduPage tasks."""

    def __init__(
        self,
        class_: str,
        entries: Iterable[GradeEntry],
        subject: str = "Informatika",
        period: str = "P2",
        save: bool = True,
        overwrite_existing: bool = False,
    ):
        """Initialize the target course, grading period, overwrite mode, and grade entries."""
        self.class_ = class_
        self.subject = subject
        self.period = period
        self.save = save
        self.overwrite_existing = overwrite_existing
        self.entries: List[GradeEntry] = list(entries)
        if not self.entries:
            raise ValueError("At least one grade entry must be provided")

    def run(self, page):
        """Select the target course, fill grade cells, and save changes."""
        page.goto(_GRADE_PAGE_URL, wait_until="domcontentloaded")
        self._select_course(page)
        page.locator("a.edubarCourseModuleLink", has_text="Známky").click()
        page.wait_for_selector(_TASK_HEADER_LOCATOR, state="attached", timeout=15000)

        filled = 0
        for entry in self.entries:
            self._fill_grade_entry(page, entry)
            filled += 1

        if self.save:
            self._save_changes(page)

        logger.info(
            "Grade fill finished for class {}, subject {}, period {} (filled={}, saved={})",
            self.class_,
            self.subject,
            self.period,
            filled,
            self.save,
        )

    def _select_course(self, page):
        """Select the target class and subject in the EduPage course switcher."""
        page.locator(".edubarCourseListBtn").click()
        course = page.locator("div.ecourse-standards-subject-title").filter(
            has=page.locator("div.className", has_text=self.class_)
        ).filter(
            has=page.locator("div.subjectName", has_text=self.subject)
        )
        course.click()
        logger.debug("Selected subject {} for class {}", self.subject, self.class_)

    def _save_changes(self, page):
        """Click EduPage save controls and confirm the save dialog when shown."""
        save_button = page.locator(_SAVE_BUTTON_LOCATOR)
        save_button.wait_for(state="visible", timeout=10000)
        save_button.click()

        confirm_button = page.get_by_role("button", name="Uložit").first
        try:
            confirm_button.wait_for(state="visible", timeout=3000)
        except Exception:
            return
        confirm_button.click()

    def _fill_grade_entry(self, page, entry: GradeEntry):
        """Fill one grade-table input identified by student and task names."""
        student_id = self._student_id_for_entry(page, entry)
        subject_id, task_uid = self._task_identifiers(page, entry.task_name)
        grade_key = f"{student_id}_{subject_id}_{task_uid}_{self.period}_1"
        existing_input_name = f"zn_{grade_key}"
        current_value = self._current_grade_value(page, existing_input_name)

        if current_value:
            if not self.overwrite_existing:
                raise ValueError(
                    f"Grade for {entry.student_display_name} in task {entry.task_name} already has value "
                    f"'{current_value}'. Use --overwrite-existing to replace it."
                )
            self._overwrite_grade_value(page, existing_input_name, entry.points)
            logger.info(
                "Overwrote {} with {} for {} in task {}",
                current_value,
                entry.points,
                entry.student_display_name,
                entry.task_name,
            )
            return

        input_name = f"nzn_{grade_key}"
        grade_input = page.locator(f'input[name="{input_name}"]')
        grade_input.wait_for(state="visible", timeout=10000)
        grade_input.fill(str(entry.points))
        logger.info(
            "Filled {} points for {} in task {}",
            entry.points,
            entry.student_display_name,
            entry.task_name,
        )

    def _current_grade_value(self, page, input_name: str) -> str:
        """Return the current stored EduPage grade value for an existing grade field."""
        return page.evaluate(
            """(inputName) => {
                const field = document.querySelector(`input[name="${inputName}"]`);
                return field ? field.value : "";
            }""",
            input_name,
        )

    def _overwrite_grade_value(self, page, input_name: str, value: GradeValue):
        """Replace an existing grade through the visible EduPage cell editor."""
        editor_input_name = input_name.replace("zn_", "nzn_", 1)
        grade_input = page.locator(f'input[name="{editor_input_name}"]')
        grade_input.wait_for(state="attached", timeout=10000)
        grade_input.click()
        grade_input.fill(str(value))

        updated_value = page.evaluate(
            """({ storedInputName, editorInputName }) => {
                const storedField = document.querySelector(`input[name="${storedInputName}"]`);
                const editorField = document.querySelector(`input[name="${editorInputName}"]`);
                return {
                    stored: storedField ? storedField.value : "",
                    editor: editorField ? editorField.value : "",
                };
            }""",
            {"storedInputName": input_name, "editorInputName": editor_input_name},
        )
        if str(updated_value.get("editor", "")).strip() != str(value):
            raise ValueError(f"EduPage editor did not keep overwritten value for {input_name}")

    def _student_id_for_entry(self, page, entry: GradeEntry) -> str:
        """Return the EduPage student id for a CSV grade entry."""
        page.wait_for_selector(_STUDENT_LINK_SELECTOR, state="attached", timeout=10000)
        matches = page.evaluate(
            """(expectedName) => {
                const normalize = (value) => value.replace(/\\s+/g, " ").trim();
                return Array.from(document.querySelectorAll('a[href*="studentid="]'))
                    .map((link) => ({
                        text: normalize(link.textContent || ""),
                        href: link.getAttribute("href") || "",
                    }))
                    .filter((link) => link.text === expectedName);
            }""",
            entry.student_display_name,
        )

        if len(matches) != 1:
            available = self._available_student_names(page)
            raise ValueError(
                f"Expected one student named {entry.student_display_name}, found {len(matches)}. "
                f"Current URL: {page.url}. Available students include: {available}"
            )

        href = matches[0]["href"]
        marker = "studentid="
        if marker not in href:
            raise ValueError(f"Could not read student id for {entry.student_display_name}")

        return href.split(marker, 1)[1].split("&", 1)[0]

    def _available_student_names(self, page) -> str:
        """Return a short sample of student names currently visible in the grade table."""
        names = page.evaluate(
            """() => {
                const normalize = (value) => value.replace(/\\s+/g, " ").trim();
                return Array.from(document.querySelectorAll('a[href*="studentid="]'))
                    .map((link) => normalize(link.textContent || ""))
                    .filter((name) => name.length > 0)
                    .slice(0, 10);
            }"""
        )
        return ", ".join(names) if names else "(none)"

    def _task_identifiers(self, page, task_name: str) -> tuple[str, str]:
        """Return subject id and task uid for an existing grade-table task."""
        page.wait_for_selector(_TASK_HEADER_LOCATOR, state="attached", timeout=10000)
        matches = page.evaluate(
            """(expectedTaskName) => {
                const normalize = (value) => value.replace(/\\s+/g, " ").trim();
                return Array.from(document.querySelectorAll(".znamkyUdalostHeader"))
                    .map((header) => ({
                        text: normalize(header.querySelector(".znHeaderUdalost")?.textContent || ""),
                        subjectId: header.getAttribute("data-pid"),
                        taskUid: header.getAttribute("data-uid"),
                    }))
                    .filter((header) => header.text === expectedTaskName);
            }""",
            task_name,
        )

        if len(matches) != 1:
            available = self._available_task_names(page)
            raise ValueError(
                f"Expected one task named {task_name}, found {len(matches)}. "
                f"Current URL: {page.url}. Available tasks include: {available}"
            )

        subject_id = matches[0]["subjectId"]
        task_uid = matches[0]["taskUid"]
        if not subject_id or not task_uid:
            raise ValueError(f"Could not read identifiers for task {task_name}")

        return subject_id, task_uid

    def _available_task_names(self, page) -> str:
        """Return a short sample of task names currently visible in the grade table."""
        names = page.evaluate(
            """() => {
                const normalize = (value) => value.replace(/\\s+/g, " ").trim();
                return Array.from(document.querySelectorAll(".znamkyUdalostHeader .znHeaderUdalost"))
                    .map((header) => normalize(header.textContent || ""))
                    .filter((name) => name.length > 0)
                    .slice(0, 10);
            }"""
        )
        return ", ".join(names) if names else "(none)"

    @classmethod
    def register_cli(cls, cli_group):
        """Register the `fill-grades` command on the provided Typer app."""

        @cli_group.command("fill-grades")
        def run_fill_grades(
            class_: Annotated[str, typer.Option(..., "--class", help="Class name (e.g., 2.png)")],
            grades_csv: Annotated[
                Path,
                typer.Option(
                    ...,
                    "--grades-csv",
                    exists=True,
                    file_okay=True,
                    dir_okay=False,
                    help="Path to CSV file with first name, last name, task name, and points columns.",
                ),
            ],
            subject: Annotated[
                str,
                typer.Option("--subject", help="Subject name in EduPage course list", show_default=True),
            ] = "Informatika",
            period: Annotated[
                str,
                typer.Option("--period", help="EduPage grading period used in grade input names", show_default=True),
            ] = "P2",
            dry_run: Annotated[
                bool,
                typer.Option("--dry-run", help="Fill fields but do not click the save button"),
            ] = False,
            overwrite_existing: Annotated[
                bool,
                typer.Option(
                    "--overwrite-existing",
                    help="Replace existing grade values instead of failing when a grade is already present.",
                ),
            ] = False,
        ):
            """Fill EduPage grade points from CSV rows."""
            try:
                entries = _load_grade_entries_from_csv(grades_csv)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc

            try:
                run_scenario(
                    lambda: cls(
                        class_,
                        entries,
                        subject=subject,
                        period=period,
                        save=not dry_run,
                        overwrite_existing=overwrite_existing,
                    )
                )
            except ScenarioRunnerError as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(code=1) from exc
