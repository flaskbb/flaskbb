import pytest
from flask import g
from flaskbb import create_app
from flaskbb.configs.testing import TestingConfig as Config
from flaskbb.core.auth.permissions import forget_permissions
from flaskbb.extensions import cache, db
from flaskbb.utils.database import drop_all
from flaskbb.utils.populate import create_default_groups, create_default_settings


@pytest.fixture(scope="package", autouse=True)
def application():
    """application with context."""
    app = create_app(Config)
    app.config.update(
        {
            "TESTING": True,
        }
    )
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture(autouse=True)
def clear_cache(application):
    """Drops the cache and the per-request permission snapshots between tests.

    The groups and permissions of a user are memoized on the user's repr,
    which is just ``<User username>``, and snapshotted on ``g`` by user id.
    Fixture usernames and ids repeat across tests, and ``g`` lives on the
    package-scoped app context, so an entry from one test would otherwise
    be served to the next one - with whatever groups the earlier test
    happened to assign.
    """
    yield
    cache.clear()
    forget_permissions()


@pytest.fixture(autouse=True)
def clear_logged_in_user(application):
    """Forgets the logged in user between tests.

    Request contexts reuse the package-scoped app context and with it ``g``,
    where ``login_user`` caches the user. Without this, a user logged in by
    one test is still ``current_user`` in the next one, detached from the
    session the earlier test closed.
    """
    yield
    g.pop("_login_user", None)


@pytest.fixture()
def request_context(application):
    with application.test_request_context():
        yield


@pytest.fixture()
def post_request_context(application):
    with application.test_request_context(method="POST"):
        yield


@pytest.fixture()
def default_groups(database):
    """Creates the default groups"""
    return create_default_groups()


@pytest.fixture()
def default_settings(database):
    """Creates the default settings"""
    return create_default_settings()


@pytest.fixture()
def database():
    """database setup."""
    db.create_all()  # Maybe use migration instead?

    yield db

    drop_all()
    db.session.close()
