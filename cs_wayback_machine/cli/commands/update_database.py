from __future__ import annotations

from typing import TYPE_CHECKING

from cs_wayback_machine.cli.controllers import scrape_liquidpedia_and_replace_result
from cs_wayback_machine.cli.core import Command, render_result

if TYPE_CHECKING:
    import argparse


class UpdateDatabaseCommand(Command):
    """Update rosters database"""

    def run(self, args: argparse.Namespace) -> None:  # noqa: U100
        result = scrape_liquidpedia_and_replace_result()
        render_result(result)
