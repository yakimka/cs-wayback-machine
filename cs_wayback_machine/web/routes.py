from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from cs_wayback_machine.web import ROOT_DIR
from cs_wayback_machine.web.views import team_detail_view

routes = [
    Route("/teams/{team_id}/", team_detail_view, methods=["get"]),
    Mount(
        "/",
        app=StaticFiles(directory=ROOT_DIR / "public"),
        name="static",
    ),
]
