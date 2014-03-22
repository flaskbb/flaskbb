import pytest

from flaskbb import create_app
from flaskbb.extensions import db
from flaskbb.configs.testing import TestingConfig as Config
from flaskbb.utils.populate import create_default_groups


@pytest.yield_fixture(autouse=True)
def application():
    """application with context."""
    app = create_app(Config)

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture()
def default_groups():
    """Creates the default groups"""
    return create_default_groups()


@pytest.yield_fixture()
def database():
    """database setup."""
    db.create_all()  # Maybe use migration instead?

    yield db

    db.drop_all()
