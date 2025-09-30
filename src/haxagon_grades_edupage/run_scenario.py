import sys
from playwright.sync_api import sync_playwright
from auth_manager import AuthManager
from scenarios.grades import GradesScenario
from scenarios.timetable import TimetableScenario

SCENARIOS = {
    "grades": GradesScenario,
    "timetable": TimetableScenario,
}

def main(name: str):
    with sync_playwright() as playwright:
        auth = AuthManager(playwright)
        browser, context = auth.new_context()
        page = context.new_page()

        scenario_cls = SCENARIOS.get(name)
        if not scenario_cls:
            print(f"Unknown scenario '{name}'. Available: {list(SCENARIOS)}")
            return

        scenario = scenario_cls()
        scenario.run(page)

        context.close()
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_scenario.py [scenario_name]")
    else:
        main(sys.argv[1])
