from click.testing import CliRunner

from edu_page_automat import cli as cli_module
from edu_page_automat.cli import cli as main_cli
from edu_page_automat.grade_diff import GradeDiffSummary
from edu_page_automat.scenarios import create_task as create_task_module
from edu_page_automat.scenarios import export_grades as export_grades_module
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
            "--overwrite-existing",
        ],
    )

    assert result.exit_code == 0
    scenario = captured["scenario"]
    assert isinstance(scenario, fill_grades_module.FillGradesScenario)
    assert scenario.class_ == "2.png"
    assert scenario.subject == "Informatika"
    assert scenario.period == "P2"
    assert scenario.save is False
    assert scenario.overwrite_existing is True
    assert scenario.entries == [
        fill_grades_module.GradeEntry(
            first_name="Žofie",
            last_name="Žužlavá",
            task_name="Task",
            points=100,
        )
    ]


def test_cli_list_outputs_export_grades_command():
    """The scenario registry includes the grade-export scenario."""
    runner = CliRunner()

    result = runner.invoke(main_cli, ["list"])

    assert result.exit_code == 0
    assert "exportgrades" in result.output


def test_cli_export_grades_invokes_run_scenario(monkeypatch, tmp_path):
    """The export-grades command builds a scenario with the selected CSV path."""
    runner = CliRunner()
    captured = {}
    output_csv = tmp_path / "grades.csv"

    def fake_run_scenario(factory):
        captured["scenario"] = factory()

    monkeypatch.setattr(export_grades_module, "run_scenario", fake_run_scenario)

    result = runner.invoke(
        main_cli,
        [
            "export-grades",
            "--class",
            "2.png",
            "--output-csv",
            str(output_csv),
            "--subject",
            "Informatika",
        ],
    )

    assert result.exit_code == 0
    scenario = captured["scenario"]
    assert isinstance(scenario, export_grades_module.ExportGradesScenario)
    assert scenario.class_ == "2.png"
    assert scenario.subject == "Informatika"
    assert scenario.output_csv == output_csv


def test_cli_convert_classroom_grades_invokes_converter(monkeypatch, tmp_path):
    """The Classroom conversion command runs outside the Playwright scenario registry."""
    runner = CliRunner()
    captured = {}
    input_csv = tmp_path / "classroom.csv"
    output_csv = tmp_path / "edupage.csv"
    input_csv.write_text("Student,Task,Topic,Points earned\nAda Lovelace,Task,Topic,42\n", encoding="utf-8")

    def fake_convert_classroom_grades_csv(input_path, output_path, *, topics, tasks):
        captured["input_path"] = input_path
        captured["output_path"] = output_path
        captured["topics"] = topics
        captured["tasks"] = tasks
        return 1

    monkeypatch.setattr(
        cli_module,
        "convert_classroom_grades_csv",
        fake_convert_classroom_grades_csv,
    )

    result = runner.invoke(
        main_cli,
        [
            "convert-classroom-grades",
            "--input-csv",
            str(input_csv),
            "--output-csv",
            str(output_csv),
            "--topic",
            "JavaScript – Certifications",
            "--task",
            "Task",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "input_path": input_csv,
        "output_path": output_csv,
        "topics": ("JavaScript – Certifications",),
        "tasks": ("Task",),
    }
    assert f"Wrote 1 grade rows to {output_csv}" in result.output


def test_cli_diff_grades_invokes_diff_writer(monkeypatch, tmp_path):
    """The grade diff command runs offline and reports summary counts."""
    runner = CliRunner()
    captured = {}
    current_csv = tmp_path / "current.csv"
    truth_csv = tmp_path / "truth.csv"
    output_csv = tmp_path / "diff.csv"
    current_csv.write_text("first_name,last_name,task_name,points\nAda,Lovelace,Task,m\n", encoding="utf-8")
    truth_csv.write_text("jmeno,prijmeni,jmeno_ulohy,pocet_bodu\nAda,Lovelace,Task,100\n", encoding="utf-8")

    def fake_write_grade_diff_csv(current_path, truth_path, output_path):
        captured["current_path"] = current_path
        captured["truth_path"] = truth_path
        captured["output_path"] = output_path
        return GradeDiffSummary(
            written_rows=1,
            equal_rows=2,
            skipped_empty_target_rows=3,
            missing_current_rows=4,
            extra_current_rows=5,
        )

    monkeypatch.setattr(cli_module, "write_grade_diff_csv", fake_write_grade_diff_csv)

    result = runner.invoke(
        main_cli,
        [
            "diff-grades",
            "--current-csv",
            str(current_csv),
            "--truth-csv",
            str(truth_csv),
            "--output-csv",
            str(output_csv),
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "current_path": current_csv,
        "truth_path": truth_csv,
        "output_path": output_csv,
    }
    assert f"Wrote 1 grade rows to {output_csv}" in result.output
    assert "equal=2" in result.output
    assert "empty-target=3" in result.output
    assert "missing-current=4" in result.output
    assert "extra-current=5" in result.output
