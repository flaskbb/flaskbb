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


@pytest.mark.parametrize(
    "view_cls",
    [
        views.DeleteTopic,
        views.LockTopic,
        views.UnlockTopic,
        views.HighlightTopic,
        views.TrivializeTopic,
    ],
)
@pytest.mark.parametrize(
    "headers, expected",
    [
        ({"Referer": "/forum/1?page=2"}, "/forum/1?page=2"),
        (
            {"Referer": "http://localhost:5000/forum/1?page=2"},
            "http://localhost:5000/forum/1?page=2",
        ),
        ({"Referer": "https://evil.example/"}, None),
        ({}, None),
        (
            {"HX-Request": "true", "HX-Current-URL": "http://localhost/forum/1?page=2"},
            "/forum/1?page=2",
        ),
    ],
)
def test_denied_topic_action_returns_to_safe_origin(
    application, user, topic_moderator, view_cls, headers, expected, monkeypatch
):
    monkeypatch.setitem(application.config, "ALLOWED_HOSTS", ["localhost:5000"])
    topic = topic_moderator
    with application.test_request_context(method="POST", headers=headers):
        g.forum = topic.forum
        g.topic = topic
        login_user(user)
        response = view_cls.as_view("action")(topic_id=topic.id)
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    assert response.status_code == 302
    assert response.headers["Location"] == (expected or _topic_path(topic))
    assert len(messages) == 1
    assert messages[0][0] == "danger"
    assert db.session.get(views.Topic, topic.id) is topic
    assert not topic.locked
    assert not topic.important


def _bulk_post(application, actor, forum, data):
    with application.test_request_context(method="POST", data=data):
        g.forum = forum
        g.topic = None
        login_user(actor)
        response = views.ManageForum.as_view("manage")(forum_id=forum.id)
        messages = get_flashed_messages(with_categories=True)
        logout_user()
    return response, messages


@pytest.mark.parametrize(
    "action, attribute, value, verb",
    [
        ("lock", "locked", True, "locked"),
        ("unlock", "locked", False, "unlocked"),
        ("highlight", "important", True, "highlighted"),
        ("trivialize", "important", False, "trivialized"),
        ("hide", "hidden", True, "hidden"),
        ("unhide", "hidden", False, "unhidden"),
    ],
)
def test_bulk_action_counts_only_changed_topics(
    application, admin_user, topic, topic_moderator, action, attribute, value, verb
):
    if action == "unhide":
        topic.hide(admin_user)
    elif attribute != "hidden":
        setattr(topic, attribute, not value)
        topic.save()

    if action == "hide":
        topic_moderator.hide(admin_user)
    elif attribute != "hidden":
        setattr(topic_moderator, attribute, value)
        topic_moderator.save()

    data = {"rowid": [str(topic.id), str(topic_moderator.id)], action: ""}
    response, messages = _bulk_post(application, admin_user, topic.forum, data)
    db.session.refresh(topic)

    assert response.status_code == 302
    assert response.headers["Location"] == f"/forum/{topic.forum.id}-{topic.forum.slug}/edit"
    assert getattr(topic, attribute) is value
    assert messages == [("success", f"1 topics {verb}.")]
    if action == "hide":
        assert topic.hidden_by == admin_user
        assert topic.first_post.hidden
    elif action == "unhide":
        assert not topic.first_post.hidden

    _response, messages = _bulk_post(application, admin_user, topic.forum, data)
    assert messages == [("success", f"0 topics {verb}.")]


def test_bulk_delete(application, moderator_user, topic):
    topic_id = topic.id
    response, messages = _bulk_post(
        application, moderator_user, topic.forum, {"rowid": [str(topic_id)], "delete": ""}
    )

    assert response.status_code == 302
    assert db.session.get(views.Topic, topic_id) is None
    assert messages == [("success", "1 topics deleted.")]


@pytest.mark.parametrize("action", ["delete", "hide", "unhide"])
def test_denied_bulk_action_does_not_flash_success(application, moderator_user, topic, action):
    moderator_user.primary_group.deletetopic = False
    moderator_user.primary_group.save()
    if action == "unhide":
        topic.hide(moderator_user)
    hidden = topic.hidden
    response, messages = _bulk_post(
        application, moderator_user, topic.forum, {"rowid": [str(topic.id)], action: ""}
    )

    assert response.status_code == 302
    assert db.session.get(views.Topic, topic.id) is topic
    assert topic.hidden == hidden
    assert len(messages) == 1
    assert messages[0][0] == "danger"


@pytest.mark.parametrize("action", ["lock", "delete", "hide", "move"])
def test_bulk_action_rejects_topics_outside_requested_forum(application, admin_user, topic, action):
    other_forum = views.Forum(title="Other forum", category=topic.forum.category).save()
    response, messages = _bulk_post(
        application,
        admin_user,
        other_forum,
        {"rowid": [str(topic.id)], action: "", "forum": str(other_forum.id)},
    )

    assert response.status_code == 302
    assert messages == [("danger", "Please modify topics in only one forum at a time.")]
    assert db.session.get(views.Topic, topic.id) is topic
    assert topic.forum != other_forum
    assert not topic.locked
    assert not topic.hidden


def test_bulk_move(application, admin_user, topic):
    other_forum = views.Forum(title="Other forum", category=topic.forum.category).save()
    response, messages = _bulk_post(
        application,
        admin_user,
        topic.forum,
        {"rowid": [str(topic.id)], "move": "", "forum": str(other_forum.id)},
    )
    db.session.refresh(topic)

    assert response.status_code == 302
    assert messages == [("success", "Topics moved.")]
    assert topic.forum == other_forum


def test_topic_action_uses_supplied_user(application, admin_user, user, topic):
    with application.test_request_context():
        login_user(admin_user)
        changed = views.do_topic_action([topic], user, "locked", False)
        logout_user()

    assert changed is False
    assert not topic.locked
