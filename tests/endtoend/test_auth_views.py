from flask_login import login_user
from flaskbb.management import views
from flaskbb.exceptions import AuthorizationRequired
import pytest


def test_overview_not_authorized(application, default_settings):
    with application.test_request_context(), pytest.raises(AuthorizationRequired) as excinfo:
        views.overview()

    assert "Authorization is required to access this area." == excinfo.value.description


def test_overview_with_authorized(admin_user, application, default_settings):
    with application.test_request_context():
        login_user(admin_user)
        resp = views.overview()
        assert 'Overview' in resp


def test_overview_with_supermod(super_moderator_user, application, default_settings):
    with application.test_request_context():
        login_user(super_moderator_user)
        resp = views.overview()
        assert 'Overview' in resp


def test_overview_with_mod(moderator_user, application, default_settings):
    with application.test_request_context():
        login_user(moderator_user)
        resp = views.overview()
        assert 'Overview' in resp
