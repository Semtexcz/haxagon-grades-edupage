"""Scenario for filling EduPage grade points from CSV rows."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import click

from edu_page_automat.logging_config import setup_logging
from edu_page_automat.scenario_runner import run_scenario
from edu_page_automat.scenarios.base import Scenario

logger = setup_logging()

_CSV_SAMPLE_SIZE = 2048
_GRADE_PAGE_URL = "https://1itg.edupage.org/user/"
_TASK_HEADER_LOCATOR = ".znamkyUdalostHeader"
_SAVE_BUTTON_LOCATOR = "a.ulozitBtn"
_STUDENT_LINK_SELECTOR = 'a[href*="studentid="]'


@dataclass(frozen=True)
class GradeEntry:
    """Single student grade entry parsed from CSV input."""

    first_name: str
    last_name: str
    task_name: str
    points: int

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


def _load_grade_entries_from_csv(csv_path: Path) -> List[GradeEntry]:
    """Load grade entries from a CSV file with flexible header names."""
    if not csv_path.exists():
        raise ValueError(f"CSV file {csv_path} does not exist")

    logger.debug("Loading grades from CSV %s", csv_path)

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

            try:
                points = int(points_value)
            except ValueError as exc:
                raise ValueError(f"Row {row_index}: invalid integer for points -> '{points_value}'") from exc

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
    ):
        """Initialize the target course, grading period, and CSV grade entries."""
        self.class_ = class_
        self.subject = subject
        self.period = period
        self.save = save
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
            save_button = page.locator(_SAVE_BUTTON_LOCATOR)
            save_button.wait_for(state="visible", timeout=10000)
            save_button.click()

        logger.info(
            "Grade fill finished for class %s, subject %s, period %s (filled=%s, saved=%s)",
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
        logger.debug("Selected subject %s for class %s", self.subject, self.class_)

    def _fill_grade_entry(self, page, entry: GradeEntry):
        """Fill one grade-table input identified by student and task names."""
        student_id = self._student_id_for_entry(page, entry)
        subject_id, task_uid = self._task_identifiers(page, entry.task_name)
        input_name = f"nzn_{student_id}_{subject_id}_{task_uid}_{self.period}_1"
        grade_input = page.locator(f'input[name="{input_name}"]')
        grade_input.wait_for(state="visible", timeout=10000)
        grade_input.fill(str(entry.points))
        logger.info(
            "Filled %s points for %s in task %s",
            entry.points,
            entry.student_display_name,
            entry.task_name,
        )

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
        """Register the `fill-grades` command on the provided Click group."""

        @cli_group.command("fill-grades")
        @click.option("--class", "class_", required=True, help="Class name (e.g., 2.png)")
        @click.option(
            "--grades-csv",
            "grades_csv",
            type=click.Path(path_type=Path, exists=True, dir_okay=False),
            required=True,
            help="Path to CSV file with first name, last name, task name, and points columns.",
        )
        @click.option("--subject", "subject", default="Informatika", show_default=True, help="Subject name in EduPage course list")
        @click.option("--period", "period", default="P2", show_default=True, help="EduPage grading period used in grade input names")
        @click.option("--dry-run", "dry_run", is_flag=True, help="Fill fields but do not click the save button")
        def run_fill_grades(class_, grades_csv, subject, period, dry_run):
            """Fill EduPage grade points from CSV rows."""
            try:
                entries = _load_grade_entries_from_csv(grades_csv)
            except ValueError as exc:
                raise click.BadParameter(str(exc)) from exc

            run_scenario(lambda: cls(class_, entries, subject=subject, period=period, save=not dry_run))
