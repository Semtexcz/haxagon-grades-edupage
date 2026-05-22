from pathlib import Path
from unittest.mock import MagicMock

import pytest

from edu_page_automat.scenarios.export_grades import (
    ExportGradesScenario,
    GradeExportRow,
    _split_student_display_name,
    _write_grade_rows_to_csv,
)


def test_split_student_display_name_reads_edupage_label() -> None:
    """EduPage student labels are split into CSV-compatible name columns."""
    assert _split_student_display_name("Žužlavá, Žofie") == ("Žofie", "Žužlavá")


def test_split_student_display_name_preserves_unexpected_label() -> None:
    """Unexpected labels are kept in the last-name column for diagnostics."""
    assert _split_student_display_name("Ada Lovelace") == ("", "Ada Lovelace")


def test_write_grade_rows_to_csv(tmp_path: Path) -> None:
    """Exported rows are written with the same headers accepted by fill-grades."""
    csv_path = tmp_path / "grades.csv"
    rows = [
        GradeExportRow("Žofie", "Žužlavá", "Dan - Frontend", "Task A", "100"),
        GradeExportRow("Ada", "Lovelace", "", "Task B", ""),
    ]

    _write_grade_rows_to_csv(csv_path, rows)

    assert csv_path.read_text(encoding="utf-8") == (
        "first_name,last_name,task_category,task_name,points\n"
        "Žofie,Žužlavá,Dan - Frontend,Task A,100\n"
        "Ada,Lovelace,,Task B,\n"
    )


def test_extract_grade_rows_maps_page_payload() -> None:
    """Browser-extracted student/task grade cells become typed export rows."""
    scenario = ExportGradesScenario(class_="2.png", output_csv=Path("grades.csv"))
    page = MagicMock()
    page.evaluate.return_value = [
        {
            "studentName": "Žužlavá, Žofie",
            "taskCategory": "Dan - Frontend",
            "taskName": "Build an App",
            "points": "100",
        },
        {
            "studentName": "Lovelace, Ada",
            "taskCategory": "Dan - Frontend",
            "taskName": "Build an App",
            "points": "",
        },
    ]

    rows = scenario._extract_grade_rows(page)

    page.wait_for_selector.assert_called_once_with('a[href*="studentid="]', state="attached", timeout=10000)
    assert rows == [
        GradeExportRow("Žofie", "Žužlavá", "Dan - Frontend", "Build an App", "100"),
        GradeExportRow("Ada", "Lovelace", "Dan - Frontend", "Build an App", ""),
    ]


def test_extract_grade_rows_requires_visible_grades() -> None:
    """An empty grade-table extraction fails before writing an empty CSV."""
    scenario = ExportGradesScenario(class_="2.png", output_csv=Path("grades.csv"))
    page = MagicMock()
    page.evaluate.return_value = []

    with pytest.raises(ValueError, match="No grade rows were found"):
        scenario._extract_grade_rows(page)


def test_run_exports_rows(monkeypatch, tmp_path: Path) -> None:
    """The run flow selects grades and writes the extracted CSV."""
    output_csv = tmp_path / "grades.csv"
    scenario = ExportGradesScenario(class_="3.A", output_csv=output_csv, subject="Informatika")
    page = MagicMock()
    grades_link = MagicMock()
    page.locator.return_value = grades_link

    monkeypatch.setattr(scenario, "_select_course", lambda unused_page: None)
    monkeypatch.setattr(
        scenario,
        "_extract_grade_rows",
        lambda unused_page: [GradeExportRow("Ada", "Lovelace", "Programming", "Algorithms", "42")],
    )

    scenario.run(page)

    grades_link.click.assert_called_once_with()
    page.wait_for_selector.assert_called_once_with(".znamkyUdalostHeader", state="attached", timeout=15000)
    assert output_csv.read_text(encoding="utf-8") == (
        "first_name,last_name,task_category,task_name,points\n"
        "Ada,Lovelace,Programming,Algorithms,42\n"
    )
