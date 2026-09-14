"""Tests for the topic moderation views as the topic page's htmx requests
drive them.

The views are invoked directly rather than over HTTP, which skips the
blueprint's before-request handlers - they are orthogonal to what is tested
here.
"""

import pytest
from flask import g, get_flashed_messages
from flask_login import login_user, logout_user
from flaskbb.extensions import db
from flaskbb.forum import views
from flaskbb.forum.models import Post


@pytest.fixture(autouse=True)
def clean_g():
    """g lives on the package-scoped app context, so whatever a test puts on it
    would otherwise leak into the tests that run after it.
    """
    yield
    for name in ("forum", "topic", "post"):
        g.pop(name, None)


def _htmx_post(view_cls, actor, topic, current_url, post=None, **kwargs):
    headers = {"HX-Request": "true", "HX-Current-URL": f"http://localhost{current_url}"}

    with views.current_app.test_request_context(method="POST", headers=headers):
        # the requirements resolve their subject off of g when it is not in
        # the URL
        g.forum = topic.forum
        g.topic = topic
        g.post = post
        login_user(actor)
        response = view_cls.as_view("action")(**kwargs)
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    return response, messages


def _topic_path(topic):
    return f"/topic/{topic.id}-{topic.slug}"


@pytest.fixture
def replies(topic, user):
    return [Post(content=f"Reply {n}").save(topic=topic, user=user) for n in range(2)]


def test_lock_returns_to_the_page_it_was_sent_from(default_settings, admin_user, topic):
    page = f"{_topic_path(topic)}?page=2"

    response, _messages = _htmx_post(views.LockTopic, admin_user, topic, page, topic_id=topic.id)

    assert response.status_code == 302
    assert response.headers["Location"] == page
    assert topic.locked


def test_delete_post_keeps_the_reader_on_the_page(default_settings, admin_user, topic, replies):
    deleted, next_post = replies

    response, _messages = _htmx_post(
        views.DeletePost,
        admin_user,
        topic,
        _topic_path(topic),
        post=deleted,
        post_id=deleted.id,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == f"{_topic_path(topic)}#pid{next_post.id}"
    assert db.session.get(Post, deleted.id) is None


def test_delete_post_emptying_the_page_loads_the_previous_one(
    default_settings, admin_user, topic, replies, monkeypatch
):
    monkeypatch.setattr(views, "flaskbb_config", {"POSTS_PER_PAGE": 1})
    previous_post, deleted = replies

    response, _messages = _htmx_post(
        views.DeletePost,
        admin_user,
        topic,
        f"{_topic_path(topic)}?page=3",
        post=deleted,
        post_id=deleted.id,
    )

    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == f"{_topic_path(topic)}?page=2#pid{previous_post.id}"


def test_unhiding_a_visible_post_changes_nothing(default_settings, admin_user, topic, replies):
    post = replies[0]

    response, messages = _htmx_post(
        views.UnhidePost, admin_user, topic, _topic_path(topic), post=post, post_id=post.id
    )

    assert response.status_code == 302
    assert ("warning", "Post is already unhidden") in messages
    assert ("success", "Post unhidden") not in messages


def test_topic_page_renders_htmx_moderation(default_settings, admin_user, topic):
    with views.current_app.test_request_context():
        g.forum = topic.forum
        g.topic = topic
        login_user(admin_user)
        response = views.ViewTopic.as_view("view_topic")(topic_id=topic.id)
        logout_user()

    assert 'hx-target="#topic-posts"' in response
    assert 'id="topic-posts"' in response
    assert f'hx-post="{_topic_path(topic)}/lock"' in response
