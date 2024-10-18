from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from cs_wayback_machine.web import ROOT_DIR
from cs_wayback_machine.web.views import (
    goto_view,
    main_page_view,
    player_detail_view,
    team_detail_view,
)

routes = [
    Route("/", main_page_view, methods=["get"]),
    Route("/goto/", goto_view, methods=["get"]),
    Route("/teams/{team_id}/", team_detail_view, methods=["get"]),
    Route("/players/{player_id}/", player_detail_view, methods=["get"]),
    Mount(
        "/",
        app=StaticFiles(directory=ROOT_DIR / "public"),
        name="static",
    ),
]
