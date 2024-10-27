from __future__ import annotations

from typing import TYPE_CHECKING

import sentry_sdk
from picodi import Provide, inject

from cs_wayback_machine.deps import get_settings

if TYPE_CHECKING:
    import argparse

    from cs_wayback_machine.cli.controllers import Result
    from cs_wayback_machine.settings import Settings


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


@inject
def setup_monitoring(settings: Settings = Provide(get_settings)) -> None:
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.3,
            profiles_sample_rate=0.3,
        )
