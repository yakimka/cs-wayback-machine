from __future__ import annotations

from typing import TYPE_CHECKING

from cs_wayback_machine.cli.core import Command

if TYPE_CHECKING:
    import argparse


class UpdateDatabaseCommand(Command):
    """Update rosters database"""

    def run(self, args: argparse.Namespace) -> None:  # noqa: U100
        print("Updating database...")
