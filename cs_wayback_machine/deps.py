from __future__ import annotations

from typing import TYPE_CHECKING

from picodi import Provide, SingletonScope, dependency, inject

from cs_wayback_machine.settings import Settings
from cs_wayback_machine.statistics import StatisticsCalculator
from cs_wayback_machine.storage import (
    DuckDbConnectionManager,
    ParserResultsStorage,
    RosterStorage,
)

if TYPE_CHECKING:
    from pathlib import Path


@dependency(scope_class=SingletonScope, use_init_hook=True)
def get_settings() -> Settings:
    return Settings.create_from_config()


@inject
def get_parser_result_file_path(settings: Settings = Provide(get_settings)) -> Path:
    return settings.parser_result_file_path


@inject
def get_parser_result_updated_date_file_path(
    settings: Settings = Provide(get_settings),
) -> Path:
    return settings.parser_result_updated_date_file_path


@inject
def get_parser_results_storage(
    parser_result_file: Path = Provide(get_parser_result_file_path),
    parser_result_updated_date_file_path: Path = Provide(
        get_parser_result_updated_date_file_path
    ),
) -> ParserResultsStorage:
    return ParserResultsStorage(
        parsed_rosters=parser_result_file,
        updated_file=parser_result_updated_date_file_path,
    )


@dependency(scope_class=SingletonScope, use_init_hook=True)
@inject
def get_duckdb_connection_manager(
    parser_results_storage: ParserResultsStorage = Provide(get_parser_results_storage),
) -> DuckDbConnectionManager:
    return DuckDbConnectionManager(parser_results_storage)


@inject
def get_rosters_storage(
    duckdb_conn_manager: DuckDbConnectionManager = Provide(
        get_duckdb_connection_manager
    ),
) -> RosterStorage:
    return RosterStorage(duckdb_conn_manager)


@inject
def get_statistics_calculator(
    duckdb_conn_manager: DuckDbConnectionManager = Provide(
        get_duckdb_connection_manager
    ),
) -> StatisticsCalculator:
    return StatisticsCalculator(duckdb_conn_manager)
