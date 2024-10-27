from __future__ import annotations

import sched
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from cs_wayback_machine.cli.controllers import scrape_liquidpedia_and_replace_result
from cs_wayback_machine.cli.core import (
    Command,
    only_print_result,
    render_result,
    setup_monitoring,
)

if TYPE_CHECKING:
    import argparse


class UpdateDatabaseCommand(Command):
    """Update rosters database"""

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--schedule",
            type=schedule_time,
            help=(
                "Run the command in schedule mode. Format:"
                "'WEEKDAY-HOUR-MINUTE'. Example: '0-12-30' for Monday 12:30 UTC"
            ),
        )

    def run(self, args: argparse.Namespace) -> None:
        if not args.schedule:
            result = scrape_liquidpedia_and_replace_result()
            render_result(result)
            return

        self.schedule_job(args.schedule)

    def schedule_job(self, schedule: tuple[int, int, int]) -> None:
        setup_monitoring()
        scheduler = sched.scheduler(time.time, time.sleep)

        def job(just_schedule: bool = False) -> None:
            if not just_schedule:
                result = scrape_liquidpedia_and_replace_result()
                only_print_result(result)
            next_run = next_run_time(schedule)
            print(
                f"Next run scheduled at {datetime.fromtimestamp(next_run)}", flush=True
            )
            scheduler.enterabs(next_run, 1, job)

        job(just_schedule=True)
        scheduler.run()


def schedule_time(schedule: str) -> tuple[int, int, int]:
    res = datetime.strptime(schedule, "%w-%H-%M")
    return int(schedule.split("-")[0]), res.hour, res.minute


def next_run_time(schedule: tuple[int, int, int]) -> float:
    weekday, hour, minute = schedule
    now = datetime.fromtimestamp(time.time())
    next_run = now.replace(hour=hour, minute=minute)
    if now.weekday() == weekday and now.time() < next_run.time():
        return next_run.timestamp()
    days_ahead = weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_run += timedelta(days=days_ahead)
    return next_run.timestamp()
