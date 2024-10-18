from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined
from markupsafe import Markup

jinja_env = Environment(
    loader=PackageLoader(__name__, "templates"),
    undefined=StrictUndefined,
    autoescape=True,
)


def player_date(date_val: str, raw_val: str | None) -> Markup | str:
    if not raw_val:
        return date_val
    return Markup(f'<em data-tooltip="Original value: {raw_val}">{date_val}</em>')


jinja_env.globals.update(player_date=player_date)


def render_html(template_name: str, data: Any = None) -> str:
    return jinja_env.get_template(template_name).render(data=data)


def render_404() -> str:
    return render_html("404_not_found.jinja2")
