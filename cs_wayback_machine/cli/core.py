from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from cs_wayback_machine.cli.controllers import Result


class Command:
    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: argparse.Namespace) -> None:
        raise NotImplementedError


def render_result(result: Result) -> None:
    print(result.message, flush=True)
    raise SystemExit(result.exit_code)


def only_print_result(result: Result) -> None:
    print(result.message, "Status:", result.exit_code, flush=True)
