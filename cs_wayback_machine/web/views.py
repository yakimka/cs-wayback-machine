from __future__ import annotations

from typing import TYPE_CHECKING

from picodi import Provide, inject
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from cs_wayback_machine.web.deps import get_rosters_storage, get_statistics_calculator
from cs_wayback_machine.web.html_render import render_404, render_html
from cs_wayback_machine.web.presenters import (
    MainPagePresenter,
    PlayerPagePresenter,
    TeamRostersPresenter,
    present_available_ids,
)
from cs_wayback_machine.web.slugify import slugify

if TYPE_CHECKING:
    from starlette.requests import Request

    from cs_wayback_machine.statistics import StatisticsCalculator
    from cs_wayback_machine.storage import RosterStorage


@inject
def main_page_view(
    request: Request,  # noqa: U100
    rosters_storage: RosterStorage = Provide(get_rosters_storage),
    statistics_calculator: StatisticsCalculator = Provide(get_statistics_calculator),
) -> Response:
    presenter = MainPagePresenter(
        rosters_storage=rosters_storage, statistics_calculator=statistics_calculator
    )
    result = presenter.present()
    html = render_html("main_page.jinja2", result)
    return HTMLResponse(html)


def goto_view(request: Request) -> Response:
    query = request.query_params.get("q", "")
    if not query:
        return RedirectResponse(url="/")

    url_template = "/teams/{slug}/"
    value = query.removeprefix("team:")
    if query.startswith("player:"):
        url_template = "/players/{slug}/"
        value = query.removeprefix("player:")

    slug = slugify(value)
    return RedirectResponse(url=url_template.format(slug=slug))


@inject
def entities_view(
    request: Request,  # noqa: U100
    rosters_storage: RosterStorage = Provide(get_rosters_storage),
) -> Response:
    result = present_available_ids(rosters_storage)
    return JSONResponse(result)


@inject
def team_detail_view(
    request: Request, rosters_storage: RosterStorage = Provide(get_rosters_storage)
) -> Response:
    team_id = slugify.reverse(request.path_params["team_id"])
    presenter = TeamRostersPresenter(rosters_storage=rosters_storage)
    result = presenter.present(team_id)
    if result is None:
        return HTMLResponse(content=render_404(), status_code=404)
    html = render_html("team_detail.jinja2", result)
    return HTMLResponse(html)


@inject
def player_detail_view(
    request: Request, rosters_storage: RosterStorage = Provide(get_rosters_storage)
) -> Response:
    player_id = slugify.reverse(request.path_params["player_id"])
    presenter = PlayerPagePresenter(rosters_storage=rosters_storage)
    result = presenter.present(player_id)
    if result is None:
        return HTMLResponse(content=render_404(), status_code=404)
    html = render_html("player_detail.jinja2", result)
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
