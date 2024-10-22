from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import duckdb

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path


class ParserResultsStorage(Protocol):
    parsed_rosters: Path

    def version(self) -> date | None:
        pass


def create_new_connection_from_parser_results(
    parsed_rosters_storage: ParserResultsStorage,
) -> duckdb.DuckDBPyConnection:
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
            unique_name TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            liquipedia_url TEXT NOT NULL,
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE rosters (
            player_unique_id TEXT,
            team_id TEXT REFERENCES teams(unique_name),
            game_version TEXT,
            player_id TEXT NOT NULL,
            name TEXT,
            liquipedia_url TEXT,
            is_captain BOOLEAN NOT NULL,
            position TEXT,
            flag_name TEXT,
            join_date DATE,
            inactive_date DATE,
            leave_date DATE,
            join_date_raw TEXT,
            inactive_date_raw TEXT,
            leave_date_raw TEXT
        )
    """
    )

    rosters_rel = conn.read_json(  # noqa: F841
        str(parsed_rosters_storage.parsed_rosters)
    )
    conn.execute(
        """
    INSERT INTO teams (unique_name, name, liquipedia_url)
    SELECT DISTINCT ON (team_unique_name) team_unique_name, team_name, team_url
    FROM rosters_rel
    """
    )
    conn.execute(
        """
    INSERT INTO rosters (
        player_unique_id, team_id, game_version, player_id, name, liquipedia_url,
        is_captain, position, flag_name, join_date, inactive_date, leave_date,
        join_date_raw, inactive_date_raw, leave_date_raw
    )
    SELECT player_unique_id, team_unique_name, game_version, player_id, full_name,
        player_url, is_captain, position, flag_name, join_date, inactive_date,
        leave_date, join_date_raw, inactive_date_raw, leave_date_raw
    FROM rosters_rel
    """
    )
    if version := parsed_rosters_storage.version():
        conn.execute(
            """
            INSERT INTO meta (rosters_updated_date)
            VALUES ($updated_date)
            """,
            parameters={"updated_date": version},
        )

    return conn
