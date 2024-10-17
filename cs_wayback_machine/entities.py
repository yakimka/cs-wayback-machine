from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cs_wayback_machine.date_util import DateRange

if TYPE_CHECKING:
    from datetime import date


@dataclass(frozen=True)
class RosterPlayer:
    team_id: str
    nickname: str
    name: str
    liquipedia_url: str | None
    is_captain: bool
    is_coach: bool
    flag_name: str | None
    flag_url: str | None
    join_date: date
    inactive_date: date | None
    leave_date: date | None

    @property
    def active_period(self) -> DateRange:
        return DateRange.create(
            start=self.join_date,
            end=self.inactive_date or self.leave_date,
        )


@dataclass
class Roster:
    players: list[RosterPlayer]
    active_period: DateRange
