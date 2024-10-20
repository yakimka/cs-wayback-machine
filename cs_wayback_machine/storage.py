from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

import duckdb

from cs_wayback_machine.date_util import DateRange
from cs_wayback_machine.entities import RosterPlayer, Team

if TYPE_CHECKING:
    from pathlib import Path


logger = logging.getLogger(__name__)


class RosterStorage:
    def __init__(self, manager: DuckDbConnectionManager) -> None:
        self._manager = manager

    def get_db_updated_date(self) -> date | None:
        query = """
        SELECT rosters_updated_date
        FROM meta;
        """
        statement = self._manager.conn.execute(query)
        row = statement.fetchone()
        if row is None:
            return None
        return row[0]

    def get_team(self, team_id: str) -> Team | None:
        query = """
        SELECT name, full_name, liquipedia_url
        FROM teams
        WHERE full_name = $team_id;
        """
        statement = self._manager.conn.execute(query, parameters={"team_id": team_id})
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

        statement = self._manager.conn.execute(
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
        statement = self._manager.conn.execute(
            query, parameters={"player_id": player_id}
        )
        players = []
        for row in statement.fetchall():
            players.append(RosterPlayer(*row))
        return players

    def get_teammates(self, player_id: str) -> list[tuple[RosterPlayer, DateRange]]:
        query = """
        SELECT tm.player_full_id, tm.team_id, tm.game_version, tm.player_id, tm.name,
            tm.liquipedia_url, tm.is_captain, tm.position, tm.flag_name, tm.flag_url,
            tm.join_date, tm.inactive_date, tm.leave_date, tm.join_date_raw,
            tm.inactive_date_raw, tm.leave_date_raw,
            GREATEST(tm.join_date, player.join_date) AS overlap_start,
            LEAST(
                COALESCE(tm.inactive_date, CURRENT_DATE),
                COALESCE(player.inactive_date, CURRENT_DATE),
                COALESCE(tm.leave_date, CURRENT_DATE),
                COALESCE(player.leave_date, CURRENT_DATE)
            ) AS overlap_end
        FROM rosters AS player
        JOIN rosters AS tm
            ON player.team_id = tm.team_id
            AND player.player_full_id <> tm.player_full_id
            AND GREATEST(tm.join_date, player.join_date) < LEAST(
                    COALESCE(tm.inactive_date, CURRENT_DATE),
                    COALESCE(player.inactive_date, CURRENT_DATE),
                    COALESCE(tm.leave_date, CURRENT_DATE),
                    COALESCE(player.leave_date, CURRENT_DATE)
                )
        WHERE player.player_full_id = $player_id
            AND player.join_date IS NOT NULL
            AND (player.join_date_raw IS NULL OR player.join_date_raw = '')
            AND (player.leave_date_raw IS NULL OR player.leave_date_raw = '')
            AND (player.inactive_date_raw IS NULL OR player.inactive_date_raw = '')
            AND tm.join_date IS NOT NULL
            AND (tm.join_date_raw IS NULL OR tm.join_date_raw = '')
            AND (tm.leave_date_raw IS NULL OR tm.leave_date_raw = '')
            AND (tm.inactive_date_raw IS NULL OR tm.inactive_date_raw = '')
        ORDER BY overlap_start;
        """
        statement = self._manager.conn.execute(
            query, parameters={"player_id": player_id}
        )
        results = []
        for row in statement.fetchall():
            *player_data, start, end = row
            results.append((RosterPlayer(*player_data), DateRange(start, end)))
        return results

    def get_team_names(self) -> list[str]:
        query = """
        SELECT full_name
        FROM teams;
        """
        statement = self._manager.conn.execute(query)
        return [row[0] for row in statement.fetchall()]

    def get_player_names(self) -> list[str]:
        query = """
        SELECT DISTINCT player_full_id
        FROM rosters;
        """
        statement = self._manager.conn.execute(query)
        return [row[0] for row in statement.fetchall()]


class DuckDbConnectionManager:
    def __init__(self, parsed_rosters: Path, updated_file: Path | None = None) -> None:
        self._parsed_rosters = parsed_rosters
        self._updated_file = updated_file
        self._conn: duckdb.DuckDBPyConnection | None = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = self._create_new_connection()
        new_version = self._parser_results_version()
        if new_version and new_version > self.db_version():
            logger.info("New version of parser results detected, updating database")
            self._conn = self._create_new_connection()
        return self._conn

    def db_version(self) -> date:
        assert self._conn is not None
        query = """
        SELECT rosters_updated_date
        FROM meta;
        """
        statement = self._conn.execute(query)
        row = statement.fetchone()
        assert row is not None
        return row[0]

    def _parser_results_version(self) -> date | None:
        if self._updated_file is not None and self._updated_file.exists():
            with open(self._updated_file) as file:
                updated_date = date.fromisoformat(file.read().strip())
            return updated_date
        return None

    def _create_new_connection(self) -> duckdb.DuckDBPyConnection:
        conn = duckdb.connect(":memory:")
        conn.execute(
            """
            CREATE TABLE meta (
                rosters_updated_date DATE,
            )
        """
        )
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

        rosters_rel = conn.read_json(str(self._parsed_rosters))  # noqa: F841
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
            is_captain, position, flag_name, flag_url, join_date, inactive_date,
            leave_date, join_date_raw, inactive_date_raw, leave_date_raw
        )
        SELECT player_full_id, team_full_name, game_version, player_id, full_name,
            player_url, is_captain, position, flag_name, flag_url, join_date,
            inactive_date, leave_date, join_date_raw, inactive_date_raw, leave_date_raw
        FROM rosters_rel
        """
        )
        if version := self._parser_results_version():
            conn.execute(
                """
                INSERT INTO meta (rosters_updated_date)
                VALUES ($updated_date)
                """,
                parameters={"updated_date": version},
            )

        return conn


class StatisticsCalculator:
    def __init__(self, manager: DuckDbConnectionManager) -> None:
        self._manager = manager

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
        statement = self._manager.conn.execute(query, parameters={"limit": limit})
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
        statement = self._manager.conn.execute(query, parameters={"limit": limit})
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
        statement = self._manager.conn.execute(query, parameters={"limit": limit})
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
        statement = self._manager.conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()

    def players_with_most_teammates(self, *, limit: int) -> list[tuple[str, int]]:
        query = """
        WITH teammate_counts AS (
            SELECT
                player.player_full_id AS player_id,
                COUNT(DISTINCT tm.player_full_id) AS teammate_count
            FROM rosters AS player
            JOIN rosters AS tm
                ON player.team_id = tm.team_id
                AND player.player_full_id <> tm.player_full_id
                AND GREATEST(tm.join_date, player.join_date) < LEAST(
                        COALESCE(tm.inactive_date, CURRENT_DATE),
                        COALESCE(player.inactive_date, CURRENT_DATE),
                        COALESCE(tm.leave_date, CURRENT_DATE),
                        COALESCE(player.leave_date, CURRENT_DATE)
                    )
            WHERE player.join_date IS NOT NULL
                AND (player.join_date_raw IS NULL OR player.join_date_raw = '')
                AND (player.leave_date_raw IS NULL OR player.leave_date_raw = '')
                AND (player.inactive_date_raw IS NULL OR player.inactive_date_raw = '')
                AND tm.join_date IS NOT NULL
                AND (tm.join_date_raw IS NULL OR tm.join_date_raw = '')
                AND (tm.leave_date_raw IS NULL OR tm.leave_date_raw = '')
                AND (tm.inactive_date_raw IS NULL OR tm.inactive_date_raw = '')
            GROUP BY player.player_full_id
        )
        SELECT player_id, teammate_count
        FROM teammate_counts
        ORDER BY teammate_count DESC
        LIMIT $limit;
        """
        statement = self._manager.conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()
