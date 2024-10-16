from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


class ClosingSlashMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not scope["path"].endswith("/"):
            scope["path"] = f"{scope['path']}/"
            scope["raw_path"] = scope["path"].encode("utf-8")
        await self.app(scope, receive, send)
