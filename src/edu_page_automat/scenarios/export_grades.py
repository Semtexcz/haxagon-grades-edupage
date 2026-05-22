"""Scenario for exporting EduPage class grades to a CSV file."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List

import click

from edu_page_automat.logging_config import setup_logging
from edu_page_automat.scenario_runner import run_scenario
from edu_page_automat.scenarios.base import Scenario

logger = setup_logging()

_GRADE_PAGE_URL = "https://1itg.edupage.org/user/"
_TASK_HEADER_LOCATOR = ".znamkyUdalostHeader"
_STUDENT_LINK_SELECTOR = 'a[href*="studentid="]'
_CSV_HEADERS = ["first_name", "last_name", "task_category", "task_name", "points"]


@dataclass(frozen=True)
class GradeExportRow:
    """Single exported EduPage grade-table cell."""

    first_name: str
    last_name: str
    task_category: str
    task_name: str
    points: str


def _split_student_display_name(display_name: str) -> tuple[str, str]:
    """Split an EduPage student label from `Last, First` into first and last names."""
    last_name, separator, first_name = display_name.partition(",")
    if not separator:
        return "", display_name.strip()
    return first_name.strip(), last_name.strip()


def _write_grade_rows_to_csv(csv_path: Path, rows: list[GradeExportRow]) -> None:
    """Write exported grade rows to a UTF-8 CSV file."""
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "first_name": row.first_name,
                    "last_name": row.last_name,
                    "task_category": row.task_category,
                    "task_name": row.task_name,
                    "points": row.points,
                }
            )


class ExportGradesScenario(Scenario):
    """Export all visible class grade-table cells for one EduPage course."""

    def __init__(self, class_: str, output_csv: Path, subject: str = "Informatika"):
        """Initialize the target class, subject, and output CSV path."""
        self.class_ = class_
        self.subject = subject
        self.output_csv = output_csv

    def run(self, page):
        """Select the target course, extract visible grade rows, and write the CSV file."""
        page.goto(_GRADE_PAGE_URL, wait_until="domcontentloaded")
        self._select_course(page)
        page.locator("a.edubarCourseModuleLink", has_text="Známky").click()
        page.wait_for_selector(_TASK_HEADER_LOCATOR, state="attached", timeout=15000)

        rows = self._extract_grade_rows(page)
        _write_grade_rows_to_csv(self.output_csv, rows)

        logger.info(
            "Grade export finished for class %s, subject %s (rows=%s, output=%s)",
            self.class_,
            self.subject,
            len(rows),
            self.output_csv,
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

    def _extract_grade_rows(self, page) -> List[GradeExportRow]:
        """Read all visible student/task grade cells from the EduPage grade table."""
        page.wait_for_selector(_STUDENT_LINK_SELECTOR, state="attached", timeout=10000)
        raw_rows = page.evaluate(
            """() => {
                const normalize = (value) => value.replace(/\\s+/g, " ").trim();
                const gradeValueFromCell = (cell) => {
                    const storedInput = Array.from(cell.querySelectorAll('input[name^="zn_"]'))
                        .find((input) => input.name !== "znamky[]");
                    if (storedInput && storedInput.value) {
                        return storedInput.value;
                    }

                    const editableInput = cell.querySelector('input[name^="nzn_"]');
                    if (editableInput && editableInput.value) {
                        return editableInput.value;
                    }

                    return normalize(cell.textContent || "");
                };

                const tasks = Array.from(document.querySelectorAll(".znamkyUdalostHeader"))
                    .map((header) => ({
                        name: normalize(header.querySelector(".znHeaderUdalost")?.textContent || ""),
                        category: normalize(header.querySelector(".znHeaderKategoria")?.textContent || ""),
                        subjectId: header.getAttribute("data-pid"),
                        taskUid: header.getAttribute("data-uid"),
                    }))
                    .filter((task) => task.name && task.subjectId && task.taskUid);

                const rows = [];
                for (const studentLink of document.querySelectorAll('a[href*="studentid="]')) {
                    const tableRow = studentLink.closest("tr");
                    if (!tableRow) {
                        continue;
                    }

                    const studentName = normalize(studentLink.textContent || "");
                    for (const task of tasks) {
                        const gradeCell = Array.from(tableRow.querySelectorAll(".znEditTd"))
                            .find((cell) => (
                                cell.getAttribute("data-pid") === task.subjectId
                                && cell.getAttribute("data-uid") === task.taskUid
                            ));
                        if (!gradeCell) {
                            continue;
                        }

                        rows.push({
                            studentName,
                            taskCategory: task.category,
                            taskName: task.name,
                            points: gradeValueFromCell(gradeCell),
                        });
                    }
                }

                return rows;
            }"""
        )

        rows: List[GradeExportRow] = []
        for raw_row in raw_rows:
            first_name, last_name = _split_student_display_name(raw_row["studentName"])
            rows.append(
                GradeExportRow(
                    first_name=first_name,
                    last_name=last_name,
                    task_category=raw_row["taskCategory"],
                    task_name=raw_row["taskName"],
                    points=raw_row["points"],
                )
            )

        if not rows:
            raise ValueError("No grade rows were found in the current EduPage grade table")

        return rows

    @classmethod
    def register_cli(cls, cli_group):
        """Register the `export-grades` command on the provided Click group."""

        @cli_group.command("export-grades")
        @click.option("--class", "class_", required=True, help="Class name (e.g., 2.png)")
        @click.option(
            "--output-csv",
            "output_csv",
            type=click.Path(path_type=Path, dir_okay=False),
            required=True,
            help="Path where the exported grade CSV should be written.",
        )
        @click.option("--subject", "subject", default="Informatika", show_default=True, help="Subject name in EduPage course list")
        def run_export_grades(class_, output_csv, subject):
            """Export visible EduPage class grades to a CSV file."""
            run_scenario(lambda: cls(class_, output_csv, subject=subject))
