from __future__ import annotations

from typing import TYPE_CHECKING

from picodi import Provide, SingletonScope, dependency, inject

from cs_wayback_machine.settings import Settings
from cs_wayback_machine.storage import (
    RosterStorage,
    StatisticsCalculator,
    load_duck_db_database,
)

if TYPE_CHECKING:
    from pathlib import Path

    import duckdb


@dependency(scope_class=SingletonScope, use_init_hook=True)
def get_settings() -> Settings:
    return Settings.create_from_config()


@inject
def get_parser_result_file_path(settings: Settings = Provide(get_settings)) -> Path:
    return settings.parser_results_path / "rosters.jsonlines"


@dependency(scope_class=SingletonScope, use_init_hook=True)
@inject
def get_duckdb_connection(
    parser_result_file: Path = Provide(get_parser_result_file_path),
) -> duckdb.DuckDBPyConnection:
    return load_duck_db_database(parser_result_file)


@inject
def get_rosters_storage(
    duckdb_conn: duckdb.DuckDBPyConnection = Provide(get_duckdb_connection),
) -> RosterStorage:
    return RosterStorage(duckdb_conn)


@inject
def get_statistics_calculator(
    duckdb_conn: duckdb.DuckDBPyConnection = Provide(get_duckdb_connection),
) -> StatisticsCalculator:
    return StatisticsCalculator(duckdb_conn)
