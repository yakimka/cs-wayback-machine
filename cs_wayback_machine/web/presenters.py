from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from cs_wayback_machine.roster import create_rosters
from cs_wayback_machine.web.slugify import slugify

if TYPE_CHECKING:
    from cs_wayback_machine.entities import Roster, RosterPlayer
    from cs_wayback_machine.storage import RosterStorage


@dataclass
class PlayerDTO:
    nickname: str
    name: str
    is_captain: bool
    is_coach: bool
    player_page_url: str
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
    liquipedia_url: str
    rosters: list[RosterDTO]


class TeamRostersPresenter:
    def __init__(self, *, rosters_storage: RosterStorage):
        self._skip_if_period_less_than = 7
        self._rosters_storage = rosters_storage

    def present(self, team_id: str) -> TeamRostersDTO | None:
        team = self._rosters_storage.get_team(team_id)
        if team is None:
            return None
        players = self._rosters_storage.get_players(
            team_id=team_id,
            date_from=date(2000, 11, 9),
            date_to=date(2025, 12, 31),
        )
        if not players:
            return None
        rosters = self._prepare_rosters(create_rosters(players))
        return TeamRostersDTO(
            team_name=team.name, liquipedia_url=team.liquipedia_url, rosters=rosters
        )

    def _prepare_rosters(self, rosters: list[Roster]) -> list[RosterDTO]:
        result = []
        for roster in rosters:
            players = []
            game_versions = []
            for player in roster.players:
                game_versions.append(player.game_version)
                position = _format_player_position(player)
                players.append(
                    PlayerDTO(
                        nickname=player.nickname,
                        name=player.name,
                        is_captain=player.is_captain,
                        is_coach="Coach" in position,
                        player_page_url=f"/players/{slugify(player.player_id)}/",
                        liquipedia_url=player.liquipedia_url,
                        flag_url=_format_flag_url(player.flag_name),
                        country=player.flag_name or "-",
                        position=position,
                        join_date=_format_date(player.join_date),
                        inactive_date=_format_date(player.inactive_date),
                        leave_date=_format_date(player.leave_date),
                    )
                )
            period_start = roster.active_period.start
            period_end = roster.active_period.end
            if (period_end - period_start).days < self._skip_if_period_less_than:
                continue
            result.append(
                RosterDTO(
                    game_version=_choose_game_version(game_versions),
                    players=sorted(players, key=lambda x: x.nickname),
                    period=f"{_format_date(period_start)} - {_format_date(period_end)}",
                )
            )

        return result


def _format_date(val: date | None) -> str:
    if not val:
        return "-"
    return val.strftime("%-d %b %Y")


def _format_player_position(player: RosterPlayer) -> str:
    positions = []
    position_field = (player.position or "").lower()
    if player.is_captain:
        positions.append("Captain")
    if "coach" in position_field:
        positions.append("Coach")
    return ", ".join(positions) if positions else "Player"


def _choose_game_version(game_versions: list[str]) -> str:
    game_versions = [_format_game_version(item) for item in game_versions]
    if not game_versions:
        return "-"
    priority = ["-", "CS1.6", "CS:S", "CS:GO", "CS2"]
    for item in priority:
        if item in game_versions:
            return item
    return "-"


def _format_game_version(val: str | None) -> str:
    if not val:
        return "-"
    val = val.strip()
    val_lower = val.lower()
    if "source" in val_lower:
        return "CS:S"
    if val_lower == "cs":
        return "CS1.6"
    # Due to the data representation inconsistency
    #   we can't be sure about the exact game version
    #   so show only old versions
    if "2" in val_lower or "go" in val_lower:
        return "-"
    return val


def _format_flag_url(flag_name: str | None) -> str:
    if not flag_name:
        return "-"
    return f"/img/f/{slugify(flag_name)}.svg"


@dataclass
class MainPageDTO:
    search_items: list[str]


class MainPagePresenter:
    def __init__(self, *, rosters_storage: RosterStorage) -> None:
        self._rosters_storage = rosters_storage

    def present(self) -> MainPageDTO:
        team_names = self._rosters_storage.get_team_names()
        return MainPageDTO(search_items=sorted(team_names))


@dataclass
class PlayerTeamDTO:
    team_id: str
    position: str
    join_date: str
    inactive_date: str
    leave_date: str
    team_page_url: str


@dataclass
class PlayerPageDTO:
    player_nickname: str
    country: str
    flag_url: str
    liquipedia_url: str | None
    teams: list[PlayerTeamDTO]


class PlayerPagePresenter:
    def __init__(self, *, rosters_storage: RosterStorage) -> None:
        self._rosters_storage = rosters_storage

    def present(self, player_id: str) -> PlayerPageDTO | None:
        player = self._rosters_storage.get_player(player_id)
        if not player:
            return None

        return PlayerPageDTO(
            player_nickname=player[-1].nickname,
            country=player[-1].flag_name or "-",
            flag_url=_format_flag_url(player[-1].flag_name),
            liquipedia_url=player[-1].liquipedia_url,
            teams=self._prepare_teams(player),
        )

    def _prepare_teams(self, player: list[RosterPlayer]) -> list[PlayerTeamDTO]:
        teams = []
        player.sort(key=lambda x: x.join_date)
        for item in player:
            teams.append(
                PlayerTeamDTO(
                    team_id=item.team_id,
                    position=_format_player_position(item),
                    join_date=_format_date(item.join_date),
                    inactive_date=_format_date(item.inactive_date),
                    leave_date=_format_date(item.leave_date),
                    team_page_url=f"/teams/{slugify(item.team_id)}/",
                )
            )
        return teams
