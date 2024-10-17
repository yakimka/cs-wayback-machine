from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined

jinja_env = Environment(
    loader=PackageLoader(__name__, "templates"),
    undefined=StrictUndefined,
    autoescape=True,
)


def render_html(template_name: str, data: Any = None) -> str:
    return jinja_env.get_template(template_name).render(data=data)


def render_404() -> str:
    return render_html("404_not_found.jinja2")
