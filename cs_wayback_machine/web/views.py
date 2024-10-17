from __future__ import annotations

from typing import TYPE_CHECKING

from picodi import Provide, inject
from starlette.responses import HTMLResponse, Response

from cs_wayback_machine.web.deps import get_rosters_storage
from cs_wayback_machine.web.html_render import render_html
from cs_wayback_machine.web.presenters import TeamRostersPresenter

if TYPE_CHECKING:
    from starlette.requests import Request

    from cs_wayback_machine.storage import RosterStorage


@inject
def team_detail_view(
    request: Request, rosters_storage: RosterStorage = Provide(get_rosters_storage)
) -> Response:
    team_id = request.path_params["team_id"]
    presenter = TeamRostersPresenter(grid_size=4, rosters_storage=rosters_storage)
    result = presenter.present(team_id)
    html = render_html("team_detail.jinja2", result)
    return HTMLResponse(html)
