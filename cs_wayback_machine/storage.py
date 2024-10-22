from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

import duckdb

from cs_wayback_machine.date_util import DateRange
from cs_wayback_machine.duck import create_new_connection_from_parser_results
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
        WITH teammate_periods AS (
            SELECT
                tm.player_full_id,
                tm.team_id,
                tm.game_version,
                tm.player_id,
                tm.name,
                tm.liquipedia_url,
                tm.is_captain,
                tm.position,
                tm.flag_name,
                tm.flag_url,
                tm.join_date,
                tm.inactive_date,
                tm.leave_date,
                tm.join_date_raw,
                tm.inactive_date_raw,
                tm.leave_date_raw,
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
        ),
        merged_periods AS (
            SELECT
                player_full_id,
                team_id,
                game_version,
                player_id,
                name,
                liquipedia_url,
                is_captain,
                position,
                flag_name,
                flag_url,
                join_date,
                inactive_date,
                leave_date,
                join_date_raw,
                inactive_date_raw,
                leave_date_raw,
                overlap_start,
                overlap_end,
                LAG(overlap_end) OVER
                (PARTITION BY player_full_id ORDER BY overlap_start) AS prev_overlap_end
            FROM teammate_periods
        ),
        final_periods AS (
            SELECT
                player_full_id,
                team_id,
                game_version,
                player_id,
                name,
                liquipedia_url,
                is_captain,
                position,
                flag_name,
                flag_url,
                join_date,
                inactive_date,
                leave_date,
                join_date_raw,
                inactive_date_raw,
                leave_date_raw,
                overlap_start,
                overlap_end,
                CASE
                    WHEN prev_overlap_end IS NULL
                        OR overlap_start > prev_overlap_end THEN overlap_start
                    ELSE prev_overlap_end
                END AS merged_start,
                CASE
                    WHEN prev_overlap_end IS NULL
                        OR overlap_start > prev_overlap_end THEN overlap_end
                    ELSE GREATEST(overlap_end, prev_overlap_end)
                END AS merged_end
            FROM merged_periods
        )
        SELECT
            player_full_id,
            team_id,
            game_version,
            player_id,
            name,
            liquipedia_url,
            is_captain,
            position,
            flag_name,
            flag_url,
            join_date,
            inactive_date,
            leave_date,
            join_date_raw,
            inactive_date_raw,
            leave_date_raw,
            merged_start AS overlap_start,
            merged_end AS overlap_end
        FROM final_periods
        GROUP BY player_full_id, team_id, game_version, player_id, name, liquipedia_url,
            is_captain, position, flag_name, flag_url, join_date, inactive_date,
            leave_date, join_date_raw, inactive_date_raw, leave_date_raw, merged_start,
            merged_end
        ORDER BY merged_start;
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
    def __init__(self, parser_results_storage: ParserResultsStorage) -> None:
        self._parser_results_storage = parser_results_storage
        self._conn: duckdb.DuckDBPyConnection | None = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = create_new_connection_from_parser_results(
                self._parser_results_storage
            )
        current_version = self.version()
        new_version = self._parser_results_storage.version()
        if new_version and (current_version is None or new_version > current_version):
            logger.info("New version of parser results detected, updating database")
            self._conn.close()
            self._conn = create_new_connection_from_parser_results(
                self._parser_results_storage
            )
        return self._conn

    def version(self) -> date | None:
        assert self._conn is not None
        query = """
        SELECT rosters_updated_date
        FROM meta;
        """
        statement = self._conn.execute(query)
        row = statement.fetchone()
        return row[0] if row else None


class ParserResultsStorage:
    def __init__(self, parsed_rosters: Path, updated_file: Path | None = None):
        self.parsed_rosters = parsed_rosters
        self._updated_file = updated_file

    def version(self) -> date | None:
        if self._updated_file is not None and self._updated_file.exists():
            return date.fromisoformat(self._updated_file.read_text().strip())
        return None
