from abc import ABC, abstractmethod
from playwright.sync_api import Page

class Scenario(ABC):
    @abstractmethod
    def run(self, page: Page):
        """Execute scenario steps using a logged-in page."""
        pass