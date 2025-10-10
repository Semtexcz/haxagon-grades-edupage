from click.testing import CliRunner

from haxagon_grades_edupage.cli import cli as main_cli
from haxagon_grades_edupage.scenarios import create_task as create_task_module


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
