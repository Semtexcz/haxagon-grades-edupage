"""Base abstractions for EduPage automation scenarios."""

from abc import ABC, abstractmethod

from playwright.sync_api import Page
import typer

class Scenario(ABC):
    """Base class for all scenarios."""

    @classmethod
    @abstractmethod
    def register_cli(cls, cli_group: typer.Typer):
        """Register CLI command for this scenario."""
        pass

    @abstractmethod
    def run(self, page: Page):
        """Execute scenario steps."""
        pass
