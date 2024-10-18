from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cs_wayback_machine.date_util import DateRange

if TYPE_CHECKING:
    from datetime import date


@dataclass(frozen=True)
class RosterPlayer:
    player_id: str
    team_id: str
    game_version: str
    nickname: str
    name: str
    liquipedia_url: str | None
    is_captain: bool
    position: str | None
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


@dataclass
class Team:
    name: str
    full_name: str
    liquipedia_url: str
