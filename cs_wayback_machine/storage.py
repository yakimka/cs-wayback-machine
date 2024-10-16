from __future__ import annotations

from typing import TYPE_CHECKING

import duckdb

from cs_wayback_machine.entities import RosterPlayer, Team

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path


class RosterStorage:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_team(self, team_id: str) -> Team | None:
        query = """
        SELECT name, full_name, liquipedia_url
        FROM teams
        WHERE full_name = $team_id;
        """
        statement = self._conn.execute(query, parameters={"team_id": team_id})
        row = statement.fetchone()
        if row is None:
            return None
        return Team(*row)

    def get_players(
        self, team_id: str, date_from: date, date_to: date
    ) -> list[RosterPlayer]:
        query = """
        SELECT player_full_id, team_id, game_version, player_id, name, liquipedia_url,
            is_captain, position, flag_name, flag_url, join_date, inactive_date,
            leave_date, join_date_raw, inactive_date_raw, leave_date_raw
        FROM rosters
        WHERE team_id = $team_id
        AND join_date <= $end_date
        AND (leave_date >= $start_date OR leave_date IS NULL)
        AND (inactive_date >= $start_date OR inactive_date IS NULL);
        """

        statement = self._conn.execute(
            query,
            parameters={
                "team_id": team_id,
                "start_date": date_from,
                "end_date": date_to,
            },
        )
        players = []
        for row in statement.fetchall():
            players.append(RosterPlayer(*row))
        return players

    def get_player(self, player_id: str) -> list[RosterPlayer]:
        query = """
        SELECT player_full_id, team_id, game_version, player_id, name, liquipedia_url,
            is_captain, position, flag_name, flag_url, join_date, inactive_date,
            leave_date, join_date_raw, inactive_date_raw, leave_date_raw
        FROM rosters
        WHERE player_full_id = $player_id;
        """
        statement = self._conn.execute(query, parameters={"player_id": player_id})
        players = []
        for row in statement.fetchall():
            players.append(RosterPlayer(*row))
        return players

    def get_team_names(self) -> list[str]:
        query = """
        SELECT full_name
        FROM teams;
        """
        statement = self._conn.execute(query)
        return [row[0] for row in statement.fetchall()]

    def get_player_names(self) -> list[str]:
        query = """
        SELECT DISTINCT player_full_id
        FROM rosters;
        """
        statement = self._conn.execute(query)
        return [row[0] for row in statement.fetchall()]


def load_duck_db_database(parsed_rosters: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE teams (
            full_name TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            liquipedia_url TEXT NOT NULL,
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE rosters (
            player_full_id TEXT,
            team_id TEXT REFERENCES teams(full_name),
            game_version TEXT,
            player_id TEXT NOT NULL,
            name TEXT,
            liquipedia_url TEXT,
            is_captain BOOLEAN NOT NULL,
            position TEXT,
            flag_name TEXT,
            flag_url TEXT,
            join_date DATE,
            inactive_date DATE,
            leave_date DATE,
            join_date_raw TEXT,
            inactive_date_raw TEXT,
            leave_date_raw TEXT
        )
    """
    )

    rosters_rel = conn.read_json(str(parsed_rosters))  # noqa: F841
    conn.execute(
        """
    INSERT INTO teams (full_name, name, liquipedia_url)
    SELECT DISTINCT ON (team_full_name) team_full_name, team_name, team_url
    FROM rosters_rel
    """
    )
    conn.execute(
        """
    INSERT INTO rosters (
        player_full_id, team_id, game_version, player_id, name, liquipedia_url,
        is_captain, position, flag_name, flag_url, join_date, inactive_date, leave_date,
        join_date_raw, inactive_date_raw, leave_date_raw
    )
    SELECT player_full_id, team_full_name, game_version, player_id, full_name,
        player_url, is_captain, position, flag_name, flag_url, join_date, inactive_date,
        leave_date, join_date_raw, inactive_date_raw, leave_date_raw
    FROM rosters_rel
    """
    )
    return conn


class StatisticsCalculator:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def players_with_most_days_in_current_team(
        self, *, limit: int
    ) -> list[tuple[str, str, int]]:
        query = """
        SELECT
            player_full_id,
            team_id,
            SUM(CURRENT_DATE - join_date) AS total_days
        FROM rosters
        WHERE join_date IS NOT NULL AND inactive_date IS NULL and leave_date IS NULL
            AND (join_date_raw IS NULL OR join_date_raw = '')
            AND (leave_date_raw IS NULL OR leave_date_raw = '')
            AND (inactive_date_raw IS NULL OR inactive_date_raw = '')
        GROUP BY player_full_id, team_id
        ORDER BY total_days DESC
        LIMIT $limit;
        """
        statement = self._conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()

    def players_with_most_teams(self, *, limit: int) -> list[tuple[str, int]]:
        query = """
        SELECT
            player_full_id,
            COUNT(DISTINCT team_id) AS total_teams
        FROM rosters
        WHERE join_date IS NOT NULL
        GROUP BY player_full_id
        ORDER BY total_teams DESC
        LIMIT $limit;
        """
        statement = self._conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()

    def active_players_by_country(self, *, limit: int) -> list[tuple[str, int]]:
        query = """
        SELECT
            flag_name,
            COUNT(DISTINCT player_full_id) AS total_players
        FROM rosters
        WHERE join_date IS NOT NULL AND leave_date IS NULL
            AND (join_date_raw IS NULL OR join_date_raw = '')
            AND (leave_date_raw IS NULL OR leave_date_raw = '')
            AND (inactive_date_raw IS NULL OR inactive_date_raw = '')
        GROUP BY flag_name
        ORDER BY total_players DESC
        LIMIT $limit;
        """
        statement = self._conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()

    def teams_with_most_players(self, *, limit: int) -> list[tuple[str, int]]:
        query = """
        SELECT
            team_id,
            COUNT(DISTINCT player_full_id) AS total_players
        FROM rosters
        WHERE join_date IS NOT NULL
        GROUP BY team_id
        ORDER BY total_players DESC
        LIMIT $limit;
        """
        statement = self._conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()
