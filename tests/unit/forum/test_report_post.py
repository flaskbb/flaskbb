import pytest
from flask import g
from flask_login import login_user, logout_user
from flaskbb.forum import views
from flaskbb.forum.models import Forum, Post, Report, Topic


@pytest.fixture(autouse=True)
def clear_current_objects():
    # g lives on the package-scoped app context, so other tests leave their topic/forum behind
    for name in ("post", "topic", "forum", "category"):
        g.pop(name, None)
    yield
    for name in ("post", "topic", "forum", "category"):
        g.pop(name, None)


@pytest.fixture
def no_csrf(application):
    previous = application.config.get("WTF_CSRF_ENABLED", True)
    application.config["WTF_CSRF_ENABLED"] = False
    yield
    application.config["WTF_CSRF_ENABLED"] = previous


def _report(actor, post, data=None):
    method = "GET" if data is None else "POST"

    with views.current_app.test_request_context(
        f"/post/{post.id}/report", method=method, data=data
    ):
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


@pytest.fixture
def private_topic(category, default_groups, admin_user):
    forum = Forum(title="Staff Forum", category_id=category.id)
    forum.save(groups=[admin_user.primary_group])
    topic = Topic(title="Staff Topic")
    return topic.save(forum=forum, user=admin_user, post=Post(content="Staff Content"))


def test_report_form_refuses_restricted_forum(default_settings, user, private_topic):
    response = _report(user, private_topic.first_post)

    assert response.status_code == 302


def test_report_refuses_restricted_forum(default_settings, no_csrf, user, private_topic):
    response = _report(user, private_topic.first_post, data={"reason": "probing"})

    assert response.status_code == 302
    assert Report.count() == 0


def test_report_accepts_restricted_forum_from_its_group(
    default_settings, no_csrf, admin_user, private_topic
):
    response = _report(admin_user, private_topic.first_post, data={"reason": "spam"})

    assert "Thanks for reporting." in response
    assert Report.count() == 1
