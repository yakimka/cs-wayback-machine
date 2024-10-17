from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import picodi
from starlette.applications import Starlette
from starlette.middleware import Middleware

from cs_wayback_machine.web.middleware import ClosingSlashMiddleware
from cs_wayback_machine.web.routes import routes

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:  # noqa: U100
    await picodi.init_dependencies()
    try:
        yield
    finally:
        await picodi.shutdown_dependencies()  # noqa: ASYNC102


middleware = [
    Middleware(ClosingSlashMiddleware),
]

app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
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
