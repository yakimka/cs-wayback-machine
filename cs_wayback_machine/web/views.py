from __future__ import annotations

from typing import TYPE_CHECKING

from picodi import Provide, inject
from starlette.responses import HTMLResponse, Response

from cs_wayback_machine.web.deps import get_rosters_storage
from cs_wayback_machine.web.html_render import render_404, render_html
from cs_wayback_machine.web.presenters import TeamRostersPresenter
from cs_wayback_machine.web.slugify import slugify

if TYPE_CHECKING:
    from starlette.requests import Request

    from cs_wayback_machine.storage import RosterStorage


@inject
def team_detail_view(
    request: Request, rosters_storage: RosterStorage = Provide(get_rosters_storage)
) -> Response:
    team_id = slugify.reverse(request.path_params["team_id"])
    presenter = TeamRostersPresenter(grid_size=4, rosters_storage=rosters_storage)
    result = presenter.present(team_id)
    if result is None:
        return HTMLResponse(content=render_404(), status_code=404)
    html = render_html("team_detail.jinja2", result)
    return HTMLResponse(html)


async def not_found_view(
    request: Request, exc: Exception  # noqa: U100
) -> HTMLResponse:
    html = render_404()
    return HTMLResponse(content=html, status_code=404)


async def server_error_view(
    request: Request, exc: Exception  # noqa: U100
) -> HTMLResponse:
    html = render_html("500_server_error.jinja2")
    return HTMLResponse(content=html, status_code=500)
