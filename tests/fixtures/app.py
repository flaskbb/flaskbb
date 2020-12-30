import pytest

from flaskbb import create_app
from flaskbb.configs.testing import TestingConfig as Config
from flaskbb.extensions import db
from flaskbb.utils.populate import create_default_groups, create_default_settings


@pytest.fixture(autouse=True)
def application():
    """application with context."""
    app = create_app(Config)

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


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

    db.drop_all()
