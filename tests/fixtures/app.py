import pytest
from flask import g
from flaskbb import create_app
from flaskbb.configs.testing import TestingConfig as Config
from flaskbb.extensions import alembic, cache, db, pluggy
from flaskbb.permissions import permission_manager
from flaskbb.utils.database import drop_all
from flaskbb.utils.populate import create_default_groups, create_default_settings


@pytest.fixture(scope="package")
def tested_plugins():
    """Entry point names of the plugins the test app loads.

    The app is created before its database, so like 'flaskbb install' it
    blocks every plugin. A plugin's test suite overrides this with its own
    name in its conftest.
    """
    return []


@pytest.fixture(scope="package", autouse=True)
def application(tested_plugins):
    """application with context."""
    set_blocked = pluggy.set_blocked

    def block_untested(name):
        if name not in tested_plugins:
            set_blocked(name)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pluggy, "set_blocked", block_untested)
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
    """Drops the cache and the per-request permission state between tests.

    The permissions and memberships a request resolves live on ``g`` by user
    id. Fixture ids repeat across tests, and ``g`` lives on the
    package-scoped app context, so an entry from one test would otherwise
    be served to the next one - with whatever groups the earlier test
    happened to assign.
    """
    yield
    cache.clear()
    permission_manager.forget()


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


@pytest.fixture(autouse=True)
def release_alembic_connections(application):
    """Returns the connections Flask-Alembic holds until its app context ends.

    ``alembic.stamp()``, ``alembic.upgrade()`` and the plugin migration checks
    keep a connection in a per-app cache that Flask-Alembic invalidates when
    the app context is torn down. The package-scoped context never is, so the
    connection would leak into the following tests, and the next nested app
    context to end would invalidate it there. Invalidating closes the one
    connection of the in-memory database, under every other session as well.
    """
    yield
    alembic_cache = alembic._get_cache()
    for context in (alembic_cache.contexts or {}).values():
        if context.connection is not None:
            context.connection.close()
    alembic_cache.contexts = None
    alembic_cache.ops = None


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
