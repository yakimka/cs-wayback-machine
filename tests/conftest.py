import pytest

from cs_wayback_machine.settings import settings

pytest_plugins = [
    "picodi.integrations._pytest",
    "picodi.integrations._pytest_asyncio",
]


@pytest.fixture(scope="session", autouse=True)
def _set_test_settings():
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")
