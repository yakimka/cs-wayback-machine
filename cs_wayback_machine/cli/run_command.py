from __future__ import annotations

import argparse
import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from picodi.helpers import lifespan

from cs_wayback_machine.cli.core import Command

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


CURR_DIR = Path(__file__).parent


def collect_commands() -> Generator[tuple[str, type[Command]]]:
    for file in (CURR_DIR / "commands").glob("*.py"):
        module_name = file.stem
        if module_name == "__init__":
            continue
        module = importlib.import_module(
            f"cs_wayback_machine.cli.commands.{module_name}"
        )
        for command_cls in module.__dict__.values():
            if (
                command_cls is not Command
                and inspect.isclass(command_cls)
                and issubclass(command_cls, Command)
            ):
                yield module_name, command_cls
                break


def make_parser(
    commands: Iterable[tuple[str, type[Command]]],
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cs_wayback_machine.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, cls in commands:
        sub_parser = subparsers.add_parser(name, help=cls.__doc__)
        cls.setup_parser(sub_parser)
    return parser


@lifespan
def main() -> None:
    commands = list(collect_commands())
    parser = make_parser(commands)
    args = parser.parse_args()
    for name, cls in commands:
        if args.command == name:
            command = cls()
            command.run(args)
            break
