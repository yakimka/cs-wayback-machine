from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from cs_wayback_machine.date_util import DateRange, days_human_readable
from cs_wayback_machine.roster import create_rosters
from cs_wayback_machine.web.slugify import slugify

if TYPE_CHECKING:
    from cs_wayback_machine.entities import Roster, RosterPlayer
    from cs_wayback_machine.statistics import StatisticsCalculator
    from cs_wayback_machine.storage import RosterStorage


@dataclass
class PlayerDTO:
    player_id: str
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
    join_date_raw: str
    inactive_date_raw: str
    leave_date_raw: str


@dataclass
class RosterDTO:
    game_version: str
    players: list[PlayerDTO]
    period: str


@dataclass
class TeamRostersDTO:
    team_name: str
    liquipedia_url: str
    reset_filters_url: str | None
    rosters: list[RosterDTO]


class TeamRostersPresenter:
    def __init__(self, *, rosters_storage: RosterStorage):
        self._skip_if_period_less_than = 3
        self._rosters_storage = rosters_storage

    def present(
        self, team_id: str, date_from: date | None = None, date_to: date | None = None
    ) -> TeamRostersDTO | None:
        has_filters = date_from or date_to
        if date_from is None:
            date_from = date(2000, 11, 9)
        if date_to is None:
            date_to = date.today() + timedelta(days=1)

        team = self._rosters_storage.get_team(team_id)
        if team is None:
            return None
        players = self._rosters_storage.get_players(
            team_id=team_id,
            date_from=date_from,
            date_to=date_to,
        )
        if not players:
            return None
        rosters = self._prepare_rosters(
            create_rosters(players), date_from=date_from, date_to=date_to
        )
        return TeamRostersDTO(
            team_name=team.name,
            liquipedia_url=team.liquipedia_url,
            reset_filters_url=team_link(team_id) if has_filters else None,
            rosters=rosters,
        )

    def _prepare_rosters(
        self, rosters: list[Roster], date_from: date, date_to: date
    ) -> list[RosterDTO]:
        result = []
        for roster in rosters:
            if not roster.players:
                continue
            players = []
            game_versions = []
            for player in roster.players:
                game_versions.append(player.game_version)
                position = _format_player_position(player)
                players.append(
                    PlayerDTO(
                        player_id=player.player_id,
                        nickname=player.nickname,
                        name=player.name,
                        is_captain=player.is_captain,
                        is_coach="Coach" in position,
                        liquipedia_url=player.liquipedia_url,
                        flag_url=_format_flag_url(player.flag_name),
                        country=player.flag_name or "-",
                        position=position,
                        join_date=_format_date(player.join_date),
                        inactive_date=_format_date(player.inactive_date),
                        leave_date=_format_date(player.leave_date),
                        join_date_raw=player.join_date_raw or "",
                        inactive_date_raw=player.inactive_date_raw or "",
                        leave_date_raw=player.leave_date_raw or "",
                    )
                )
            if roster.active_period == DateRange.never():
                result.append(
                    RosterDTO(
                        period="Entries with invalid dates",
                        game_version="-",
                        players=players,
                    )
                )
                continue

            period_start = roster.active_period.start
            period_end = roster.active_period.end

            if date_from >= period_end or date_to < period_start:
                continue

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
    if val == date.min:
        return "Unknown"
    if val in (date.max, date.today()):
        return "Present"
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
class RowValueDTO:
    value: str
    description: str | None = None
    is_team_id: bool = False
    is_player_id: bool = False


@dataclass
class TableDTO:
    title: str
    headers: list[str]
    rows: list[list[RowValueDTO]]


@dataclass
class MainPageDTO:
    search_items: list[str]
    statistics: list[TableDTO]


def present_available_ids(rosters_storage: RosterStorage) -> list[str]:
    team_names = sorted(rosters_storage.get_team_names())
    player_names = sorted(rosters_storage.get_player_names())
    return [f"team:{item}" for item in team_names if item] + [
        f"player:{item}" for item in player_names if item
    ]


class MainPagePresenter:
    def __init__(
        self,
        *,
        rosters_storage: RosterStorage,
        statistics_calculator: StatisticsCalculator,
    ) -> None:
        self._rosters_storage = rosters_storage
        self._statistics_calculator = statistics_calculator

    def present(self) -> MainPageDTO:
        return MainPageDTO(
            search_items=present_available_ids(self._rosters_storage),
            statistics=self._build_statistics(),
        )

    def _build_statistics(self) -> list[TableDTO]:
        calc = self._statistics_calculator

        def format_days_description(days: int) -> str | None:
            if days <= 31:
                return None
            return f"{days} days"

        return [
            TableDTO(
                title="TOP5 Players with most time in current team (without breaks)",
                headers=["Player", "Team", "Period"],
                rows=[
                    [
                        RowValueDTO(item[0], is_player_id=True),
                        RowValueDTO(item[1], is_team_id=True),
                        RowValueDTO(
                            days_human_readable(item[2]),
                            description=format_days_description(item[2]),
                        ),
                    ]
                    for item in calc.players_with_most_days_in_current_team(limit=5)
                ],
            ),
            TableDTO(
                title="TOP5 Players with most teams",
                headers=["Player", "Number of teams"],
                rows=[
                    [
                        RowValueDTO(item[0], is_player_id=True),
                        RowValueDTO(str(item[1])),
                    ]
                    for item in calc.players_with_most_teams(limit=5)
                ],
            ),
            TableDTO(
                title="TOP10 Players with most teammates",
                headers=["Player", "Number of teammates"],
                rows=[
                    [
                        RowValueDTO(item[0], is_player_id=True),
                        RowValueDTO(str(item[1])),
                    ]
                    for item in calc.players_with_most_teammates(limit=10)
                ],
            ),
            TableDTO(
                title="TOP10 Teammates with most time together",
                headers=["Player1", "Player2", "Total time"],
                rows=[
                    [
                        RowValueDTO(item[0], is_player_id=True),
                        RowValueDTO(item[1], is_player_id=True),
                        RowValueDTO(
                            days_human_readable(item[2]),
                            description=format_days_description(item[2]),
                        ),
                    ]
                    for item in calc.get_teammate_pair_with_most_time(limit=10)
                ],
            ),
            TableDTO(
                title="TOP10 Teams with most players in history",
                headers=["Team name", "Number of players"],
                rows=[
                    [
                        RowValueDTO(item[0], is_team_id=True),
                        RowValueDTO(str(item[1])),
                    ]
                    for item in calc.teams_with_most_players(limit=10)
                ],
            ),
            TableDTO(
                title="TOP10 Countries by active players",
                headers=["Country", "Number of active players"],
                rows=[
                    [
                        RowValueDTO(item[0]),
                        RowValueDTO(str(item[1])),
                    ]
                    for item in calc.active_players_by_country(limit=10)
                ],
            ),
        ]


@dataclass
class PlayerTeamDTO:
    team_id: str
    position: str
    join_date: str
    inactive_date: str
    leave_date: str
    join_date_raw: str
    inactive_date_raw: str
    leave_date_raw: str


@dataclass
class TeammateDTO:
    player_id: str
    nickname: str
    team_ids: list[str]
    periods: list[str]
    total_days: int


@dataclass
class PlayerPageDTO:
    player_nickname: str
    country: str
    flag_url: str
    liquipedia_url: str | None
    teams: list[PlayerTeamDTO]
    teammates: list[TeammateDTO]


class PlayerPagePresenter:
    def __init__(self, *, rosters_storage: RosterStorage) -> None:
        self._rosters_storage = rosters_storage

    def present(self, player_id: str) -> PlayerPageDTO | None:
        player = self._rosters_storage.get_player(player_id)
        if not player:
            return None

        latest_player = max(player, key=lambda x: x.active_period.start)
        teammates = self._rosters_storage.get_teammates(latest_player.player_id)
        return PlayerPageDTO(
            player_nickname=latest_player.nickname,
            country=latest_player.flag_name or "-",
            flag_url=_format_flag_url(latest_player.flag_name),
            liquipedia_url=latest_player.liquipedia_url,
            teams=self._prepare_teams(player),
            teammates=self._prepare_teammates(teammates),
        )

    def _prepare_teams(self, player: list[RosterPlayer]) -> list[PlayerTeamDTO]:
        teams = []
        player.sort(key=lambda x: x.active_period.start)
        for item in player:
            team = PlayerTeamDTO(
                team_id=item.team_id,
                position=_format_player_position(item),
                join_date=_format_date(item.join_date),
                inactive_date=_format_date(item.inactive_date),
                leave_date=_format_date(item.leave_date),
                join_date_raw=item.join_date_raw or "",
                inactive_date_raw=item.inactive_date_raw or "",
                leave_date_raw=item.leave_date_raw or "",
            )
            if team not in teams:
                teams.append(team)
        return teams

    def _prepare_teammates(
        self, teammates: list[tuple[RosterPlayer, DateRange]]
    ) -> list[TeammateDTO]:
        teammates.sort(key=lambda x: x[1].start)
        teammate_id_map: dict[str, list[tuple[RosterPlayer, DateRange]]] = {}
        teammate_id_to_nicknames = {}
        for mate, period in teammates:
            if period.days < 3:
                continue
            teammate_id_map.setdefault(mate.player_id, []).append((mate, period))
            teammate_id_to_nicknames[mate.player_id] = mate.nickname

        results = []
        for mate_id, items in teammate_id_map.items():
            team_ids = []
            periods = []
            total_days = 0
            for mate, period in items:
                team_ids.append(mate.team_id)
                periods.append(
                    f"{_format_date(period.start)} - {_format_date(period.end)} "
                    f"({period.days} days)"
                )
                total_days += period.days
            results.append(
                TeammateDTO(
                    player_id=mate_id,
                    nickname=teammate_id_to_nicknames[mate_id],
                    team_ids=team_ids,
                    periods=periods,
                    total_days=total_days,
                )
            )
        results.sort(key=lambda x: x.total_days, reverse=True)
        return results


@dataclass
class GlobalDataDTO:
    db_last_updated_date: str | None = None


def present_global_data(rosters_storage: RosterStorage) -> GlobalDataDTO:
    updated_date = rosters_storage.get_db_updated_date()
    return GlobalDataDTO(
        db_last_updated_date=updated_date.isoformat() if updated_date else None
    )


def player_link(player_id: str) -> str:
    return f"/players/{slugify(player_id)}/"


def team_link(team_id: str) -> str:
    return f"/teams/{slugify(team_id)}/"
