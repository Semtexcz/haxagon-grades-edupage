from .base import Scenario

class TimetableScenario(Scenario):
    def run(self, page):
        page.goto("https://1itg.edupage.org/user/")
        page.click("text=Rozvrh")  # příklad
        print("Otevřen rozvrh:", page.url)
