from flask_login import login_user
from flaskbb.management import views
from flask import get_flashed_messages


def test_overview_not_authorized(application, default_settings):
    view = views.ManagementOverview.as_view('overview')
    with application.test_request_context():
        result = view()
        messages = get_flashed_messages(with_categories=True)

    expected = (
        'danger',
        'You are not allowed to access the management panel'
    )
    assert result.status_code == 302
    assert messages[0] == expected


def test_overview_with_authorized(admin_user, application, default_settings):
    view = views.ManagementOverview.as_view('overview')
    with application.test_request_context():
        login_user(admin_user)
        resp = view()
        assert 'Overview' in resp


def test_overview_with_supermod(super_moderator_user, application, default_settings):  # noqa
    view = views.ManagementOverview.as_view('overview')
    with application.test_request_context():
        login_user(super_moderator_user)
        resp = view()
        assert 'Overview' in resp


def test_overview_with_mod(moderator_user, application, default_settings):
    view = views.ManagementOverview.as_view('overview')
    with application.test_request_context():
        login_user(moderator_user)
        resp = view()
        assert 'Overview' in resp
