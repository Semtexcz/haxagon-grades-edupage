from abc import ABC, abstractmethod
from playwright.sync_api import Page

class Scenario(ABC):
    """Base class for all scenarios."""

    @classmethod
    @abstractmethod
    def register_cli(cls, cli_group):
        """Register CLI command for this scenario."""
        pass

    @abstractmethod
    def run(self, page: Page):
        """Execute scenario steps."""
        pass
