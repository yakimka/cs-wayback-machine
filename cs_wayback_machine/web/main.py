from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import picodi
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette_exporter import PrometheusMiddleware

from cs_wayback_machine.deps import get_settings
from cs_wayback_machine.web.middleware import ClosingSlashMiddleware
from cs_wayback_machine.web.routes import routes
from cs_wayback_machine.web.views import not_found_view, server_error_view

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None]:  # noqa: U100
    await picodi.init_dependencies()
    try:
        yield
    finally:
        await picodi.shutdown_dependencies()  # noqa: ASYNC102


middleware = [
    Middleware(ClosingSlashMiddleware),
    Middleware(PrometheusMiddleware, app_name="cs_wayback_machine_web"),
]

exception_handlers = {
    404: not_found_view,
    500: server_error_view,
}

app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
    exception_handlers=exception_handlers,
)

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.3,
        profiles_sample_rate=0.3,
        integrations=[StarletteIntegration()],
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
