import types

import pytest
from flask import get_flashed_messages, url_for
from flask_login import login_user
from flaskbb.extensions import pluggy
from flaskbb.plugins import utils
from sqlalchemy.exc import OperationalError

PLUGIN_SOURCE = """
from sqlalchemy.exc import OperationalError

def query():
    raise OperationalError("SELECT 1 FROM plugin_table", {}, Exception("no such table"))
"""


def core_query():
    raise OperationalError("SELECT 1 FROM core_table", {}, Exception("no such table"))


@pytest.fixture
def failing_plugin():
    module = types.ModuleType("failing_plugin")
    exec(PLUGIN_SOURCE, module.__dict__)
    pluggy.register(module, "failing_plugin")

    yield module

    pluggy.unregister(module)


@pytest.fixture
def pending_migrations(monkeypatch):
    monkeypatch.setattr(utils, "plugin_has_pending_migrations", lambda name: True)


@pytest.fixture
def plugin_error(failing_plugin):
    with pytest.raises(OperationalError) as excinfo:
        failing_plugin.query()
    return excinfo.value


def test_plugin_error_is_attributed_to_plugin(plugin_error, pending_migrations):
    assert utils.get_plugins_with_pending_migrations(plugin_error) == ["failing_plugin"]


def test_plugin_error_is_ignored_when_migrations_are_applied(plugin_error, monkeypatch):
    monkeypatch.setattr(utils, "plugin_has_pending_migrations", lambda name: False)

    assert utils.get_plugins_with_pending_migrations(plugin_error) == []


def test_core_error_is_not_attributed_to_plugin(failing_plugin, pending_migrations):
    with pytest.raises(OperationalError) as excinfo:
        core_query()

    assert utils.get_plugins_with_pending_migrations(excinfo.value) == []


def test_admin_is_redirected_to_overview(application, admin_user, plugin_error, pending_migrations):
    with application.test_request_context("/unknown"):
        login_user(admin_user)
        response = application.handle_user_exception(plugin_error)

        assert response.status_code == 302
        assert response.location == url_for("management.overview")
        category, message = get_flashed_messages(with_categories=True)[0]
        assert category == "danger"
        assert "failing_plugin" in message


def test_user_is_redirected_to_index(application, user, plugin_error, pending_migrations):
    with application.test_request_context("/unknown"):
        login_user(user)
        response = application.handle_user_exception(plugin_error)

        assert response.status_code == 302
        assert response.location == url_for("forum.index")
        category, message = get_flashed_messages(with_categories=True)[0]
        assert category == "danger"
        assert "failing_plugin" not in message


def test_failing_redirect_target_is_not_redirected(
    application, user, plugin_error, pending_migrations
):
    with application.test_request_context("/"):
        login_user(user)

        with pytest.raises(OperationalError):
            application.handle_user_exception(plugin_error)


def test_error_without_pending_plugin_migrations_is_reraised(
    application, admin_user, failing_plugin, pending_migrations
):
    with pytest.raises(OperationalError) as excinfo:
        core_query()

    with application.test_request_context("/unknown"):
        login_user(admin_user)

        with pytest.raises(OperationalError):
            application.handle_user_exception(excinfo.value)
