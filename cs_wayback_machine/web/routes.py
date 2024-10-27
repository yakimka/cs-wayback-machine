from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette_exporter import handle_metrics

from cs_wayback_machine.web import ROOT_DIR
from cs_wayback_machine.web.views import (
    entities_view,
    goto_view,
    main_page_view,
    player_detail_view,
    team_detail_view,
)

routes = [
    Route("/", main_page_view, methods=["get"]),
    Route("/api/entities/", entities_view, methods=["get"]),
    Route("/goto/", goto_view, methods=["get"]),
    Route("/teams/{team_id}/", team_detail_view, methods=["get"]),
    Route("/players/{player_id}/", player_detail_view, methods=["get"]),
    Route("/metrics/", handle_metrics),
    Mount(
        "/",
        app=StaticFiles(directory=ROOT_DIR / "public"),
        name="static",
    ),
]
