import pytest
from flaskbb import create_app
from flaskbb.configs.testing import TestingConfig as Config
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
    """Drops the cache between tests.

    ``User.get_permissions`` and ``get_groups`` are memoized on the user's
    repr, which is just ``<User username>``. Fixture usernames repeat across
    tests, so a cached entry from one test would otherwise be served to the
    next one - with whatever groups the earlier test happened to assign.
    """
    yield
    cache.clear()


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
