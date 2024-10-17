from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from cs_wayback_machine.roster import create_rosters
from cs_wayback_machine.web.slugify import slugify

if TYPE_CHECKING:
    from cs_wayback_machine.entities import Roster
    from cs_wayback_machine.storage import RosterStorage


@dataclass
class PlayerDTO:
    nickname: str
    name: str
    is_captain: bool
    is_coach: bool
    liquipedia_url: str | None
    flag_url: str
    country: str
    position: str
    join_date: str
    inactive_date: str
    leave_date: str


@dataclass
class RosterDTO:
    game_version: str
    players: list[PlayerDTO]
    period: str


@dataclass
class TeamRostersDTO:
    team_name: str
    rosters: list[RosterDTO]


class TeamRostersPresenter:
    def __init__(self, *, grid_size: int, rosters_storage: RosterStorage):
        self._grid_size = grid_size
        self._rosters_storage = rosters_storage

    def present(self, team_id: str) -> TeamRostersDTO | None:
        team = self._rosters_storage.get_team(team_id)
        if team is None:
            return None
        players = self._rosters_storage.get_players(
            team_id=team_id,
            date_from=date(2000, 1, 1),
            date_to=date(2023, 12, 31),
        )
        if not players:
            return None
        rosters = self._prepare_rosters(create_rosters(players))
        return TeamRostersDTO(team_name=team.name, rosters=rosters)

    def _prepare_rosters(self, rosters: list[Roster]) -> list[RosterDTO]:
        result = []
        for roster in rosters:
            players = []
            game_version: str | None = None
            for player in roster.players:
                if game_version is None and player.game_version:
                    game_version = player.game_version
                positions = []
                if player.is_captain:
                    positions.append("Captain")
                elif player.is_coach:
                    positions.append("Coach")
                players.append(
                    PlayerDTO(
                        nickname=player.nickname,
                        name=player.name,
                        is_captain=player.is_captain,
                        is_coach=player.is_coach,
                        liquipedia_url=player.liquipedia_url,
                        flag_url=f"/img/f/{slugify(player.flag_name or "")}.svg",
                        country=player.flag_name or "-",
                        position=", ".join(positions) if positions else "Player",
                        join_date=_format_date(player.join_date),
                        inactive_date=_format_date(player.inactive_date),
                        leave_date=_format_date(player.leave_date),
                    )
                )
            period_start = _format_date(roster.active_period.start)
            period_end = _format_date(roster.active_period.end)
            result.append(
                RosterDTO(
                    game_version=_format_game_version(game_version),
                    players=players,
                    period=f"{period_start} - {period_end}",
                )
            )

        return result


def _format_date(val: date | None) -> str:
    if not val:
        return "-"
    return val.strftime("%-d %b %Y")


def _format_game_version(val: str | None) -> str:
    if not val:
        return "-"
    val = val.strip()
    val_lower = val.lower()
    if "global" in val_lower:
        return "CS:GO"
    if "source" in val_lower:
        return "CS:S"
    if val_lower == "cs":
        return "CS 1.6"
    if "2" in val_lower:
        return "CS2"
    return val
