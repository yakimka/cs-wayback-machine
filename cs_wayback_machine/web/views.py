from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from picodi import Provide, inject
from starlette.responses import HTMLResponse, Response

from cs_wayback_machine.roster import create_rosters
from cs_wayback_machine.web.deps import get_rosters_storage
from cs_wayback_machine.web.html_render import render_html

if TYPE_CHECKING:
    from starlette.requests import Request

    from cs_wayback_machine.storage import RosterStorage


@inject
def team_detail_view(
    request: Request, rosters_storage: RosterStorage = Provide(get_rosters_storage)
) -> Response:
    team_id = request.path_params["team_id"]
    players = rosters_storage.get_players(
        team_full_name=team_id, date_from=date(2000, 1, 1), date_to=date(2023, 12, 31)
    )
    rosters = create_rosters(players)
    html = render_html("team_detail.jinja2", rosters)

    return HTMLResponse(html)
