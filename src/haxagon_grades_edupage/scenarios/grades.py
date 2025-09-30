from .base import Scenario

class GradesScenario(Scenario):
    def run(self, page):
        page.goto("https://1itg.edupage.org/user/")
        page.click("text=Známky")  # příklad
        print("Otevřeny známky:", page.url)
