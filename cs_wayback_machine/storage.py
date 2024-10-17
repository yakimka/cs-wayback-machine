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
        SELECT team_id, game_version, player_id, name, liquipedia_url,
            is_captain, position, flag_name, flag_url, join_date, inactive_date,
            leave_date
        FROM rosters
        WHERE team_id = $team_id
        AND join_date IS NOT NULL  -- TODO delete this line
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
            team_id TEXT REFERENCES teams(full_name),
            game_version TEXT,
            player_id TEXT NOT NULL,
            player_full_id TEXT,
            name TEXT,
            liquipedia_url TEXT,
            is_captain BOOLEAN NOT NULL,
            position TEXT,
            flag_name TEXT,
            flag_url TEXT,
            join_date DATE NOT NULL,
            inactive_date DATE,
            leave_date DATE
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
        team_id, game_version, player_id, player_full_id, name, liquipedia_url,
        is_captain, position, flag_name, flag_url, join_date, inactive_date, leave_date
    )
    SELECT team_full_name, game_version, player_id, player_full_id, full_name,
        player_url, is_captain, position, flag_name, flag_url, join_date, inactive_date,
        leave_date
    FROM rosters_rel
    WHERE join_date IS NOT NULL -- TODO delete this line
    """
    )
    return conn
