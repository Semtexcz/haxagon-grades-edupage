from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest

from edu_page_automat.scenarios.fill_grades import (
    FillGradesScenario,
    GradeEntry,
    _load_grade_entries_from_csv,
    _parse_grade_value,
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
        """Unsupported grade values fail before browser automation starts."""
        csv_path = tmp_path / "invalid_points.csv"
        write_csv(
            csv_path,
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Žofie,Žužlavá,Task,sto",
            ],
        )

        with pytest.raises(ValueError, match=r"Row 2: invalid grade value -> 'sto'"):
            _load_grade_entries_from_csv(csv_path)

    def test_accepts_absence_marker_m_for_points(self, tmp_path: Path) -> None:
        """CSV grade values may use the EduPage absence marker m."""
        csv_path = tmp_path / "absence.csv"
        write_csv(
            csv_path,
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Žofie,Žužlavá,Task,m",
            ],
        )

        entries = _load_grade_entries_from_csv(csv_path)

        assert entries == [
            GradeEntry(
                first_name="Žofie",
                last_name="Žužlavá",
                task_name="Task",
                points="m",
            )
        ]

    def test_skips_rows_with_empty_points(self, tmp_path: Path) -> None:
        """Review CSV files may include unfinished grade rows without filling them."""
        csv_path = tmp_path / "partial.csv"
        write_csv(
            csv_path,
            [
                "jmeno,prijmeni,jmeno_ulohy,pocet_bodu",
                "Žofie,Žužlavá,Task,",
                "Ada,Lovelace,Task,42",
            ],
        )

        entries = _load_grade_entries_from_csv(csv_path)

        assert entries == [
            GradeEntry(
                first_name="Ada",
                last_name="Lovelace",
                task_name="Task",
                points=42,
            )
        ]


def test_parse_grade_value_accepts_uppercase_m() -> None:
    """The m marker is normalized to lowercase before filling."""
    assert _parse_grade_value(" M ", row_index=2) == "m"


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
    page.evaluate.return_value = [
        {
            "text": "Žužlavá, Žofie",
            "href": "?what=zobraztriedu&studentid=-440&p=-91",
        }
    ]

    student_id = scenario._student_id_for_entry(page, scenario.entries[0])

    page.wait_for_selector.assert_called_once_with('a[href*="studentid="]', state="attached", timeout=10000)
    assert student_id == "-440"


def test_task_identifiers_read_task_header_attributes() -> None:
    """Task identifiers are read from the existing grade-table task header."""
    scenario = FillGradesScenario(
        class_="2.png",
        subject="Informatika",
        entries=[GradeEntry("Žofie", "Žužlavá", "Task", 100)],
    )
    page = MagicMock()
    page.evaluate.return_value = [
        {
            "text": "Task",
            "subjectId": "-91",
            "taskUid": "132812",
        }
    ]

    subject_id, task_uid = scenario._task_identifiers(page, "Task")

    assert subject_id == "-91"
    assert task_uid == "132812"
    page.wait_for_selector.assert_called_once_with(".znamkyUdalostHeader", state="attached", timeout=10000)


def test_fill_grade_entry_fills_expected_input(monkeypatch) -> None:
    """Grade entries fill the composed EduPage input name."""
    entry = GradeEntry("Žofie", "Žužlavá", "Task", 100)
    scenario = FillGradesScenario(class_="2.png", entries=[entry], subject="Informatika")
    page = MagicMock()
    grade_input = MagicMock()
    page.locator.return_value = grade_input

    monkeypatch.setattr(scenario, "_student_id_for_entry", lambda unused_page, unused_entry: "-440")
    monkeypatch.setattr(scenario, "_task_identifiers", lambda unused_page, unused_task_name: ("-91", "132812"))
    monkeypatch.setattr(scenario, "_current_grade_value", lambda unused_page, unused_input_name: "")

    scenario._fill_grade_entry(page, entry)

    page.locator.assert_called_once_with('input[name="nzn_-440_-91_132812_P2_1"]')
    grade_input.wait_for.assert_called_once_with(state="visible", timeout=10000)
    grade_input.fill.assert_called_once_with("100")


def test_fill_grade_entry_rejects_existing_grade_without_overwrite(monkeypatch) -> None:
    """Existing grades are protected unless overwrite mode is enabled."""
    entry = GradeEntry("Žofie", "Žužlavá", "Task", 80)
    scenario = FillGradesScenario(class_="2.png", entries=[entry], subject="Informatika")
    page = MagicMock()

    monkeypatch.setattr(scenario, "_student_id_for_entry", lambda unused_page, unused_entry: "-440")
    monkeypatch.setattr(scenario, "_task_identifiers", lambda unused_page, unused_task_name: ("-91", "132810"))
    monkeypatch.setattr(scenario, "_current_grade_value", lambda unused_page, unused_input_name: "100")

    with pytest.raises(ValueError, match="Use --overwrite-existing"):
        scenario._fill_grade_entry(page, entry)


def test_fill_grade_entry_overwrites_existing_grade(monkeypatch) -> None:
    """Overwrite mode replaces the stored existing EduPage grade field."""
    entry = GradeEntry("Žofie", "Žužlavá", "Task", "m")
    scenario = FillGradesScenario(
        class_="2.png",
        entries=[entry],
        subject="Informatika",
        overwrite_existing=True,
    )
    page = MagicMock()
    overwritten: list[tuple[str, str]] = []

    monkeypatch.setattr(scenario, "_student_id_for_entry", lambda unused_page, unused_entry: "-440")
    monkeypatch.setattr(scenario, "_task_identifiers", lambda unused_page, unused_task_name: ("-91", "132812"))
    monkeypatch.setattr(scenario, "_current_grade_value", lambda unused_page, unused_input_name: "90")
    monkeypatch.setattr(
        scenario,
        "_overwrite_grade_value",
        lambda unused_page, input_name, value: overwritten.append((input_name, value)),
    )

    scenario._fill_grade_entry(page, entry)

    assert overwritten == [("zn_-440_-91_132812_P2_1", "m")]
    page.locator.assert_not_called()


def test_overwrite_grade_value_updates_hidden_field() -> None:
    """Existing grade overwrites update the hidden field through page JavaScript."""
    scenario = FillGradesScenario(
        class_="2.png",
        entries=[GradeEntry("Žofie", "Žužlavá", "Task", 80)],
        subject="Informatika",
        overwrite_existing=True,
    )
    page = MagicMock()

    scenario._overwrite_grade_value(page, "zn_-440_-91_132810_P2_1", 80)

    _, payload = page.evaluate.call_args.args
    assert payload == {"inputName": "zn_-440_-91_132810_P2_1", "value": "80"}


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
    page.wait_for_selector.assert_called_once_with(".znamkyUdalostHeader", state="attached", timeout=15000)
    save_button.wait_for.assert_called_once_with(state="visible", timeout=10000)
    save_button.click.assert_called_once_with()
