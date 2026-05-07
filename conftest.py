import os
import pytest

# pytest-playwright installs an asyncio event loop early in the session.
# Without this, Django refuses to make sync DB calls from within that loop.
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', '1')


@pytest.fixture
def user(db):
    from accounts.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def other_user(db):
    from accounts.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def logged_in_client(client, user):
    client.force_login(user)
    return client
