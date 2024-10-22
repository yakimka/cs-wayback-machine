from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cs_wayback_machine.storage import DuckDbConnectionManager


class StatisticsCalculator:
    def __init__(self, manager: DuckDbConnectionManager) -> None:
        self._manager = manager

    def players_with_most_days_in_current_team(
        self, *, limit: int
    ) -> list[tuple[str, str, int]]:
        query = """
        WITH active_periods AS (
            SELECT
                player_full_id,
                team_id,
                join_date,
                COALESCE(inactive_date, leave_date, CURRENT_DATE) AS end_date
            FROM rosters
            WHERE join_date IS NOT NULL
                AND inactive_date IS NULL
                AND leave_date IS NULL
                AND (join_date_raw IS NULL OR join_date_raw = '')
                AND (leave_date_raw IS NULL OR leave_date_raw = '')
                AND (inactive_date_raw IS NULL OR inactive_date_raw = '')
        ),
        merged_periods AS (
            SELECT
                player_full_id,
                team_id,
                join_date,
                end_date,
                LAG(end_date) OVER(
                    PARTITION BY player_full_id, team_id ORDER BY join_date
                ) AS prev_end_date
            FROM active_periods
        ),
        final_periods AS (
            SELECT
                player_full_id,
                team_id,
                join_date,
                end_date,
                CASE
                    WHEN prev_end_date IS NULL
                        OR join_date > prev_end_date THEN end_date - join_date
                    ELSE end_date - GREATEST(prev_end_date, join_date)
                END AS period_days
            FROM merged_periods
        )
        SELECT
            player_full_id,
            team_id,
            SUM(period_days) AS total_days
        FROM final_periods
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

    def get_teammate_pair_with_most_time(
        self, *, limit: int
    ) -> list[tuple[str, str, int]]:
        query = """
        WITH teammate_pairs AS (
            SELECT
                LEAST(player.player_full_id, tm.player_full_id) AS player1,
                GREATEST(player.player_full_id, tm.player_full_id) AS player2,
                GREATEST(player.join_date, tm.join_date) AS overlap_start,
                LEAST(
                    COALESCE(tm.inactive_date, CURRENT_DATE),
                    COALESCE(player.inactive_date, CURRENT_DATE),
                    COALESCE(player.leave_date, CURRENT_DATE),
                    COALESCE(tm.leave_date, CURRENT_DATE)
                ) AS overlap_end
            FROM rosters AS player
            JOIN rosters AS tm
                ON player.team_id = tm.team_id
                AND player.player_full_id <> tm.player_full_id
                AND GREATEST(player.join_date, tm.join_date) <= LEAST(
                    COALESCE(tm.inactive_date, CURRENT_DATE),
                    COALESCE(player.inactive_date, CURRENT_DATE),
                    COALESCE(player.leave_date, CURRENT_DATE),
                    COALESCE(tm.leave_date, CURRENT_DATE)
                )
            WHERE player.join_date IS NOT NULL
                AND (player.join_date_raw IS NULL OR player.join_date_raw = '')
                AND (player.leave_date_raw IS NULL OR player.leave_date_raw = '')
                AND (player.inactive_date_raw IS NULL OR player.inactive_date_raw = '')
                AND tm.join_date IS NOT NULL
                AND (tm.join_date_raw IS NULL OR tm.join_date_raw = '')
                AND (tm.leave_date_raw IS NULL OR tm.leave_date_raw = '')
                AND (tm.inactive_date_raw IS NULL OR tm.inactive_date_raw = '')
        ),
        merged_pairs AS (
            SELECT player1, player2, overlap_start, overlap_end,
                LAG(overlap_end) OVER (
                    PARTITION BY player1, player2 ORDER BY overlap_start
                ) AS prev_overlap_end
            FROM teammate_pairs
        ),
        final_pairs AS (
            SELECT player1, player2, overlap_start, overlap_end,
                   CASE
                       WHEN prev_overlap_end IS NULL
                        OR overlap_start > prev_overlap_end
                   THEN overlap_end - overlap_start
                   ELSE overlap_end - GREATEST(prev_overlap_end, overlap_start)
                   END AS overlap_days
            FROM merged_pairs
        )
        SELECT player1, player2, SUM(overlap_days) AS total_overlap_days
        FROM final_pairs
        GROUP BY player1, player2
        ORDER BY total_overlap_days DESC
        LIMIT $limit;
        """

        statement = self._manager.conn.execute(query, parameters={"limit": limit})
        return statement.fetchall()
