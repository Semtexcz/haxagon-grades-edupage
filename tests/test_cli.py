from click.testing import CliRunner

from edu_page_automat.cli import cli as main_cli
from edu_page_automat.scenarios import create_task as create_task_module
from edu_page_automat.scenarios import fill_grades as fill_grades_module


def test_cli_list_outputs_available_commands():
    runner = CliRunner()

    result = runner.invoke(main_cli, ["list"])

    print(result.output)
    assert result.exit_code == 0
    assert "createtask" in result.output


def test_cli_create_task_invokes_run_scenario(monkeypatch):
    runner = CliRunner()
    captured = {}

    def fake_run_scenario(factory):
        captured["scenario"] = factory()

    monkeypatch.setattr(create_task_module, "run_scenario", fake_run_scenario)

    result = runner.invoke(
        main_cli,
        ["create-task", "--class", "3.A", "--name", "Test", "--points", "15"],
    )

    assert result.exit_code == 0
    scenario = captured["scenario"]
    assert isinstance(scenario, create_task_module.CreateTaskScenario)
    assert scenario.class_ == "3.A"
    assert scenario.subject == "Informatika"
    assert scenario.tasks == [create_task_module.TaskDefinition(name="Test", points=15)]


def test_cli_list_outputs_fill_grades_command():
    """The scenario registry includes the grade-filling scenario."""
    runner = CliRunner()

    result = runner.invoke(main_cli, ["list"])

    assert result.exit_code == 0
    assert "fillgrades" in result.output


def test_cli_fill_grades_invokes_run_scenario(monkeypatch, tmp_path):
    """The fill-grades command builds a scenario from CSV input."""
    runner = CliRunner()
    captured = {}
    csv_path = tmp_path / "grades.csv"
    csv_path.write_text(
        "jmeno,prijmeni,jmeno_ulohy,pocet_bodu\nŽofie,Žužlavá,Task,100\n",
        encoding="utf-8",
    )

    def fake_run_scenario(factory):
        captured["scenario"] = factory()

    monkeypatch.setattr(fill_grades_module, "run_scenario", fake_run_scenario)

    result = runner.invoke(
        main_cli,
        [
            "fill-grades",
            "--class",
            "2.png",
            "--grades-csv",
            str(csv_path),
            "--subject",
            "Informatika",
            "--period",
            "P2",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    scenario = captured["scenario"]
    assert isinstance(scenario, fill_grades_module.FillGradesScenario)
    assert scenario.class_ == "2.png"
    assert scenario.subject == "Informatika"
    assert scenario.period == "P2"
    assert scenario.save is False
    assert scenario.entries == [
        fill_grades_module.GradeEntry(
            first_name="Žofie",
            last_name="Žužlavá",
            task_name="Task",
            points=100,
        )
    ]
