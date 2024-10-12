import pytest

from cs_wayback_machine.bank.account import Account
from cs_wayback_machine.bank.user import User


@pytest.fixture()
def make_user() -> type[User]:
    return User


@pytest.fixture()
def user(make_user):
    return make_user(
        name="John Doe",
    )


@pytest.fixture()
def account():
    return Account(name="default")
