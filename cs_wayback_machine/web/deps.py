import os
from pathlib import Path

import duckdb
from picodi import Provide, SingletonScope, dependency, inject

from cs_wayback_machine.storage import RosterStorage, load_duck_db_database
from cs_wayback_machine.web import ROOT_DIR


def get_parser_result_file_path() -> Path:
    return Path(os.getenv("PARSER_RESULT_FILE", ROOT_DIR / "../rosters.jsonlines"))


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
