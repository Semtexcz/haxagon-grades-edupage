from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest

from edu_page_automat.scenarios.fill_grades import (
    FillGradesScenario,
    GradeEntry,
    _load_grade_entries_from_csv,
)


def write_csv(path: Path, rows: List[str]) -> None:
    """Write CSV test rows to a temporary file."""
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


class TestLoadGradeEntriesFromCsv:
    """Tests for grade CSV parsing and validation."""

    def test_loads_grade_entries_with_czech_headers(self, tmp_path: Path) -> None:
        """CSV files can use Czech headers from the user-facing workflow."""
        csv_path = tmp_path / "grades.csv"
        write_csv(
            csv_path,
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Žofie,Žužlavá,Build an RPG Creature Search App Project,100",
            ],
        )

        entries = _load_grade_entries_from_csv(csv_path)

        assert entries == [
            GradeEntry(
                first_name="Žofie",
                last_name="Žužlavá",
                task_name="Build an RPG Creature Search App Project",
                points=100,
            )
        ]

    def test_supports_english_headers_and_semicolon_delimiter(self, tmp_path: Path) -> None:
        """CSV parsing accepts English headers and semicolon delimiters."""
        csv_path = tmp_path / "grades_alt.csv"
        write_csv(
            csv_path,
            [
                "first_name;last_name;task_name;points",
                " Ada ; Lovelace ; Algorithms ; 42 ",
            ],
        )

        entries = _load_grade_entries_from_csv(csv_path)

        assert entries == [
            GradeEntry(
                first_name="Ada",
                last_name="Lovelace",
                task_name="Algorithms",
                points=42,
            )
        ]

    def test_raises_for_invalid_points(self, tmp_path: Path) -> None:
        """Invalid point values fail before browser automation starts."""
        csv_path = tmp_path / "invalid_points.csv"
        write_csv(
            csv_path,
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Žofie,Žužlavá,Task,sto",
            ],
        )

        with pytest.raises(ValueError, match=r"Row 2: invalid integer for points -> 'sto'"):
            _load_grade_entries_from_csv(csv_path)


def test_grade_entry_student_display_name() -> None:
    """Student display names match EduPage grade-table links."""
    entry = GradeEntry(
        first_name="Žofie",
        last_name="Žužlavá",
        task_name="Task",
        points=100,
    )

    assert entry.student_display_name == "Žužlavá, Žofie"


def test_fill_grades_scenario_requires_entries() -> None:
    """The scenario rejects empty grade input."""
    with pytest.raises(ValueError, match="At least one grade entry must be provided"):
        FillGradesScenario(class_="2.png", entries=[], subject="Informatika")


def test_student_id_for_entry_reads_student_link_query() -> None:
    """Student ids are extracted from EduPage student links."""
    scenario = FillGradesScenario(
        class_="2.png",
        subject="Informatika",
        entries=[GradeEntry("Žofie", "Žužlavá", "Task", 100)],
    )
    page = MagicMock()
    student_locator = MagicMock()
    first_student = MagicMock()
    student_locator.count.return_value = 1
    student_locator.first.return_value = first_student
    first_student.get_attribute.return_value = "?what=zobraztriedu&studentid=-440&p=-91"
    page.locator.return_value = student_locator

    student_id = scenario._student_id_for_entry(page, scenario.entries[0])

    page.locator.assert_called_once_with("a.edubarSmartLink", has_text="Žužlavá, Žofie")
    assert student_id == "-440"


def test_task_identifiers_read_task_header_attributes() -> None:
    """Task identifiers are read from the existing grade-table task header."""
    scenario = FillGradesScenario(
        class_="2.png",
        subject="Informatika",
        entries=[GradeEntry("Žofie", "Žužlavá", "Task", 100)],
    )
    page = MagicMock()
    headers = MagicMock()
    header = MagicMock()
    headers.filter.return_value = headers
    headers.count.return_value = 1
    headers.first.return_value = header
    header.get_attribute.side_effect = lambda name: {"data-pid": "-91", "data-uid": "132812"}[name]
    page.locator.return_value = headers

    subject_id, task_uid = scenario._task_identifiers(page, "Task")

    assert subject_id == "-91"
    assert task_uid == "132812"
    page.locator.assert_any_call(".znamkyUdalostHeader")
    page.locator.assert_any_call(".znHeaderUdalost", has_text="Task")


def test_fill_grade_entry_fills_expected_input(monkeypatch) -> None:
    """Grade entries fill the composed EduPage input name."""
    entry = GradeEntry("Žofie", "Žužlavá", "Task", 100)
    scenario = FillGradesScenario(class_="2.png", entries=[entry], subject="Informatika")
    page = MagicMock()
    grade_input = MagicMock()
    page.locator.return_value = grade_input

    monkeypatch.setattr(scenario, "_student_id_for_entry", lambda unused_page, unused_entry: "-440")
    monkeypatch.setattr(scenario, "_task_identifiers", lambda unused_page, unused_task_name: ("-91", "132812"))

    scenario._fill_grade_entry(page, entry)

    page.locator.assert_called_once_with('input[name="nzn_-440_-91_132812_P2_1"]')
    grade_input.wait_for.assert_called_once_with(state="visible", timeout=10000)
    grade_input.fill.assert_called_once_with("100")


def test_run_fills_entries_and_saves(monkeypatch) -> None:
    """The run flow selects the course, fills entries, and saves by default."""
    entries = [
        GradeEntry("Ada", "Lovelace", "Algorithms", 42),
        GradeEntry("Grace", "Hopper", "Compilers", 50),
    ]
    scenario = FillGradesScenario(class_="3.A", entries=entries, subject="Informatika")
    page = MagicMock()
    grades_link = MagicMock()
    save_button = MagicMock()
    filled: list[str] = []

    def locator_side_effect(selector, *args, **kwargs):
        if selector == "a.edubarCourseModuleLink":
            return grades_link
        if selector == "a.ulozitBtn":
            return save_button
        return MagicMock()

    page.locator.side_effect = locator_side_effect
    monkeypatch.setattr(scenario, "_select_course", lambda unused_page: None)
    monkeypatch.setattr(scenario, "_fill_grade_entry", lambda unused_page, entry: filled.append(entry.task_name))

    scenario.run(page)

    assert filled == ["Algorithms", "Compilers"]
    grades_link.click.assert_called_once_with()
    save_button.wait_for.assert_called_once_with(state="visible", timeout=10000)
    save_button.click.assert_called_once_with()
