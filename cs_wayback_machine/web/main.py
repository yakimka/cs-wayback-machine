from __future__ import annotations

import contextlib
import os
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

import picodi
from jinja2 import Environment, PackageLoader, StrictUndefined
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from cs_wayback_machine.roster import create_rosters
from cs_wayback_machine.storage import RosterStorage, load_duck_db_database
from cs_wayback_machine.web.middleware import ClosingSlashMiddleware

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from starlette.requests import Request

CURRENT_DIR = Path(__file__).parent
jinja_env = Environment(
    loader=PackageLoader("main", "templates"),
    undefined=StrictUndefined,
    autoescape=True,
)


def render_html(template_name: str, data: Any) -> str:
    return jinja_env.get_template(template_name).render(data=data)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:  # noqa: U100
    await picodi.init_dependencies()
    try:
        yield
    finally:
        await picodi.shutdown_dependencies()  # noqa: ASYNC102


middleware = [
    Middleware(ClosingSlashMiddleware),
]

parser_result_file = Path(
    os.getenv("PARSER_RESULT_FILE", CURRENT_DIR / "../rosters.jsonlines")
)
duckdb_conn = load_duck_db_database(parser_result_file)


def team_detail_view(request: Request) -> Response:
    team_id = request.path_params["team_id"]
    storage = RosterStorage(duckdb_conn)
    players = storage.get_players(
        team_full_name=team_id, date_from=date(2000, 1, 1), date_to=date(2023, 12, 31)
    )
    rosters = create_rosters(players)
    html = render_html("team_detail.jinja2", rosters)

    return HTMLResponse(html)


app = Starlette(
    routes=[
        Route("/teams/{team_id}/", team_detail_view, methods=["get"]),
    ],
    middleware=middleware,
    lifespan=lifespan,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "cs_wayback_machine.web.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        lifespan="on",
        reload=True,
        reload_dirs=["/opt/project/cs_wayback_machine/"],
    )
