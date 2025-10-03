import click

from src.haxagon_grades_edupage.scenario_runner import run_scenario
from src.haxagon_grades_edupage.scenarios.base import Scenario
from src.haxagon_grades_edupage.logging_config import setup_logging

logger = setup_logging()


class CreateTaskScenario(Scenario):
    def __init__(self, class_: str, task_name: str, task_points: int):
        self.class_ = class_
        self.task_name = task_name
        self.task_points = task_points

    def run(self, page):
        page.goto("https://1itg.edupage.org/user/", wait_until="domcontentloaded")

        # vybrat třídu
        page.locator(".edubarCourseListBtn").click()
        locator = page.locator("div.ecourse-standards-subject-title").filter(
            has=page.locator("div.className", has_text=self.class_)
        ).filter(
            has=page.locator("div.subjectName", has_text="Informatika") # TODO: Vyměnit informatika za proměnnou
        )

        locator.click()

        # otevřít sekci známek
        page.get_by_role("link", name="Známky").click()

        # vybrat třídu
        # page.get_by_text(self.class_).nth(1).click()

        # vytvořit novou písemku
        page.locator("a").filter(has_text="Nová písemka/ zkoušení").click()
        page.locator("input[name=\"p_meno\"]").fill(self.task_name)
        page.locator("select[name=\"kategoriaid\"]").select_option("3")
        page.get_by_role("spinbutton").fill(str(self.task_points))

        # uložit
        page.get_by_role("button", name="Uložit").click()

        logger.info("Created task %s for class %s with %s points", self.task_name, self.class_, self.task_points)

    @classmethod
    def register_cli(cls, cli_group):
        @cli_group.command("create-task")
        @click.option("--class", "class_", required=True, help="Class name (e.g., 3.gpu)")
        @click.option("--name", "task_name", required=True, help="Task name")
        @click.option("--points", "task_points", type=int, required=True, help="Task points")
        def run_task(class_, task_name, task_points):
            """Create a new test/task in EduPage."""
            run_scenario(lambda: cls(class_, task_name, task_points))

if __name__ == "__main__":
    # jednoduchý test bez CLI
    run_scenario(lambda: CreateTaskScenario(
        class_="3.gpu",
        task_name="Test/smažu",
        task_points=68
    ))