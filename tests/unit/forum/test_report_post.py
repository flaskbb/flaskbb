import pytest
from flask_login import login_user, logout_user
from flaskbb.forum import views
from flaskbb.forum.models import Report


@pytest.fixture
def no_csrf(application):
    previous = application.config.get("WTF_CSRF_ENABLED", True)
    application.config["WTF_CSRF_ENABLED"] = False
    yield
    application.config["WTF_CSRF_ENABLED"] = previous


def _report(actor, post, data=None):
    method = "GET" if data is None else "POST"

    with views.current_app.test_request_context(method=method, data=data):
        login_user(actor)
        response = views.ReportView.as_view("report_post")(post_id=post.id)
        logout_user()

    return response


def test_report_form_posts_back_into_itself(default_settings, user, topic):
    response = _report(user, topic.first_post)

    assert 'id="report-form"' in response
    assert f'hx-post="/post/{topic.first_post.id}/report"' in response


def test_report_replaces_the_form_with_thanks(default_settings, no_csrf, user, topic):
    response = _report(user, topic.first_post, data={"reason": "spam"})

    assert "Thanks for reporting." in response
    assert 'name="reason"' not in response
    assert Report.count() == 1


def test_invalid_report_keeps_the_form(default_settings, no_csrf, user, topic):
    response = _report(user, topic.first_post, data={"reason": ""})

    assert 'name="reason"' in response
    assert Report.count() == 0
