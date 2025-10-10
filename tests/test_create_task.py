from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest

from haxagon_grades_edupage.scenarios.create_task import (
    CreateTaskScenario,
    TASK_ROW_LOCATOR,
    TaskDefinition,
    _load_tasks_from_csv,
)


def write_csv(path: Path, rows: List[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


class TestLoadTasksFromCsv:
    def test_loads_tasks_with_standard_headers(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "tasks.csv"
        write_csv(
            csv_path,
            [
                "name,points",
                "Task A,10",
                "Task B,20",
            ],
        )

        tasks = _load_tasks_from_csv(csv_path)

        assert tasks == [
            TaskDefinition(name="Task A", points=10),
            TaskDefinition(name="Task B", points=20),
        ]

    def test_supports_alternate_headers_and_delimiters(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "tasks_alt.csv"
        write_csv(
            csv_path,
            [
                "task;body",
                "  Úloha 1 ;  15 ",
                "Úloha 2;30",
            ],
        )

        tasks = _load_tasks_from_csv(csv_path)

        assert tasks == [
            TaskDefinition(name="Úloha 1", points=15),
            TaskDefinition(name="Úloha 2", points=30),
        ]

    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "absent.csv"

        with pytest.raises(ValueError, match=r"CSV file .+ does not exist"):
            _load_tasks_from_csv(missing)

    def test_raises_for_missing_name(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "missing_name.csv"
        write_csv(
            csv_path,
            [
                "name,points",
                ",10",
            ],
        )

        with pytest.raises(ValueError, match=r"Row 2: missing task name"):
            _load_tasks_from_csv(csv_path)

    def test_raises_for_invalid_points(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "invalid_points.csv"
        write_csv(
            csv_path,
            [
                "name,points",
                "Task,not_a_number",
            ],
        )

        with pytest.raises(ValueError, match=r"Row 2: invalid integer for points -> 'not_a_number'"):
            _load_tasks_from_csv(csv_path)


def test_create_task_scenario_requires_task() -> None:
    with pytest.raises(ValueError, match="At least one task must be provided"):
        CreateTaskScenario(class_="3.A", tasks=[], subject="Informatika")


class TestTaskMissing:
    def _make_scenario(self) -> CreateTaskScenario:
        return CreateTaskScenario(
            class_="3.A",
            subject="Informatika",
            category="Kategorie",
            tasks=[TaskDefinition(name="Existing", points=1)],
        )

    def test_returns_false_when_task_exists(self) -> None:
        scenario = self._make_scenario()
        page = MagicMock()
        locator = MagicMock()
        filtered = MagicMock()
        filtered.count.return_value = 2
        locator.filter.return_value = filtered
        page.locator.return_value = locator

        missing = scenario._task_missing(page, TaskDefinition(name="Existing", points=1))

        page.locator.assert_called_once_with(TASK_ROW_LOCATOR)
        locator.filter.assert_called_once_with(has_text="Existing")
        filtered.count.assert_called_once_with()
        assert missing is False

    def test_returns_true_when_task_missing(self) -> None:
        scenario = self._make_scenario()
        page = MagicMock()
        locator = MagicMock()
        filtered = MagicMock()
        filtered.count.return_value = 0
        locator.filter.return_value = filtered
        page.locator.return_value = locator

        missing = scenario._task_missing(page, TaskDefinition(name="New Task", points=2))

        page.locator.assert_called_once_with(TASK_ROW_LOCATOR)
        locator.filter.assert_called_once_with(has_text="New Task")
        filtered.count.assert_called_once_with()
        assert missing is True


def test_create_task_fills_form_and_selects_category() -> None:
    task = TaskDefinition(name="Praktická písemka", points=50)
    scenario = CreateTaskScenario(
        class_="3.B",
        subject="Informatika",
        category="Dan - Linux",
        tasks=[task],
    )

    page = MagicMock()

    new_task_button = MagicMock()
    new_task_locator = MagicMock()
    new_task_locator.filter.return_value = new_task_button

    name_input = MagicMock()
    dropdown = MagicMock()
    spinbutton = MagicMock()
    save_button = MagicMock()

    def locator_side_effect(selector, *args, **kwargs):
        if selector == "a":
            return new_task_locator
        if selector == 'input[name="p_meno"]':
            return name_input
        if selector == 'select[name="kategoriaid"]':
            return dropdown
        return MagicMock()

    def get_by_role_side_effect(role, name=None, **kwargs):
        if role == "spinbutton":
            return spinbutton
        if role == "button" and name == "Uložit":
            return save_button
        return MagicMock()

    page.locator.side_effect = locator_side_effect
    page.get_by_role.side_effect = get_by_role_side_effect

    scenario._create_task(page, task)

    page.locator.assert_any_call("a")
    new_task_locator.filter.assert_called_once_with(has_text="Nová písemka/ zkoušení")
    new_task_button.wait_for.assert_called_once_with(state="visible", timeout=10000)
    new_task_button.click.assert_called_once_with()

    page.wait_for_selector.assert_called_once_with('input[name="p_meno"]', state="visible", timeout=15000)
    name_input.fill.assert_called_once_with("Praktická písemka")

    dropdown.wait_for.assert_called_once_with(state="attached", timeout=15000)
    dropdown.select_option.assert_called_once_with(label="Dan - Linux")
    page.evaluate.assert_not_called()

    spinbutton.wait_for.assert_called_once_with(state="visible", timeout=10000)
    spinbutton.fill.assert_called_once_with("50")

    save_button.wait_for.assert_called_once_with(state="visible", timeout=10000)
    save_button.click.assert_called_once_with()


def test_create_task_without_category_uses_fallback() -> None:
    task = TaskDefinition(name="Bez kategorie", points=5)
    scenario = CreateTaskScenario(
        class_="3.C",
        subject="Informatika",
        category=None,
        tasks=[task],
    )

    page = MagicMock()

    new_task_button = MagicMock()
    new_task_locator = MagicMock()
    new_task_locator.filter.return_value = new_task_button

    name_input = MagicMock()
    dropdown = MagicMock()
    spinbutton = MagicMock()
    save_button = MagicMock()

    def locator_side_effect(selector, *args, **kwargs):
        if selector == "a":
            return new_task_locator
        if selector == 'input[name="p_meno"]':
            return name_input
        if selector == 'select[name="kategoriaid"]':
            return dropdown
        return MagicMock()

    def get_by_role_side_effect(role, name=None, **kwargs):
        if role == "spinbutton":
            return spinbutton
        if role == "button" and name == "Uložit":
            return save_button
        return MagicMock()

    page.locator.side_effect = locator_side_effect
    page.get_by_role.side_effect = get_by_role_side_effect

    scenario._create_task(page, task)

    dropdown.wait_for.assert_called_once_with(state="attached", timeout=15000)
    dropdown.select_option.assert_not_called()
    page.evaluate.assert_called_once()


def test_run_creates_only_missing_tasks(monkeypatch):
    tasks = [
        TaskDefinition(name="Úloha 1", points=10),
        TaskDefinition(name="Úloha 2", points=20),
    ]
    scenario = CreateTaskScenario(
        class_="3.A",
        subject="Informatika",
        category="Dan - Linux",
        tasks=tasks,
    )

    class DummyLocator:
        def __init__(self):
            self._returned_self = False

        def filter(self, *args, **kwargs):
            self._returned_self = True
            return self

        def click(self):
            return None

    class DummyPage:
        def __init__(self):
            self.goto_calls = []

        def goto(self, url, wait_until=None):
            self.goto_calls.append((url, wait_until))

        def locator(self, *args, **kwargs):
            return DummyLocator()

    page = DummyPage()

    missing_results: list[str] = []
    created_results: list[str] = []
    missing_iter = iter([True, False])

    def fake_task_missing(unused_page, task):
        missing_results.append(task.name)
        return next(missing_iter)

    def fake_create_task(unused_page, task):
        created_results.append(task.name)

    monkeypatch.setattr(scenario, "_task_missing", fake_task_missing)
    monkeypatch.setattr(scenario, "_create_task", fake_create_task)

    scenario.run(page)

    assert missing_results == ["Úloha 1", "Úloha 2"]
    assert created_results == ["Úloha 1"]
