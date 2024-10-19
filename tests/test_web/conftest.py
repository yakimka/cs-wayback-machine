import pytest
from httpx import AsyncClient

from cs_wayback_machine.web.main import app


@pytest.fixture()
def asgi_app():
    return app


@pytest.fixture()
async def client(asgi_app) -> AsyncClient:
    async with AsyncClient(
        app=asgi_app, base_url="http://testserver", timeout=2
    ) as client:
        yield client
