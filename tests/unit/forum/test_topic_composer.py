import pytest
import sqlalchemy as sa
from flask import g
from flask_login.test_client import FlaskLoginClient
from flaskbb.extensions import db
from flaskbb.forum.models import Topic


@pytest.fixture(autouse=True)
def disable_csrf(application):
    previous = application.config["WTF_CSRF_ENABLED"]
    application.config["WTF_CSRF_ENABLED"] = False
    for name in ("post", "topic", "forum", "category"):
        g.pop(name, None)
    yield
    for name in ("post", "topic", "forum", "category"):
        g.pop(name, None)
    application.config["WTF_CSRF_ENABLED"] = previous


def client_for(application, user):
    application.test_client_class = FlaskLoginClient
    return application.test_client(user=user)


def test_composer_places_attachments_before_options(application, user, forum):
    response = client_for(application, user).get(f"/{forum.id}/topic/new")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.index("attachment-section") < html.index("topic-options")
    assert "Track this topic" in html
    assert "Highlight topic" not in html
    assert "Lock topic" not in html
    assert "Hide topic" not in html


def test_moderator_sees_topic_state_options(application, moderator_user, forum):
    response = client_for(application, moderator_user).get(f"/{forum.id}/topic/new")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Highlight topic" in html
    assert "Lock topic" in html
    assert "Hide topic" not in html


def test_admin_sees_hidden_topic_option(application, admin_user, forum):
    response = client_for(application, admin_user).get(f"/{forum.id}/topic/new")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Highlight topic" in html
    assert "Lock topic" in html
    assert "Hide topic" in html


def test_new_post_uses_topic_composer_layout(application, user, topic):
    response = client_for(application, user).get(f"/topic/{topic.id}/post/new")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "topic-composer-heading" in html
    assert "editor-mode-tabs" in html
    assert html.index("attachment-section") < html.index("post-options")
    assert "topic-composer-actions" in html


def test_member_cannot_set_moderation_options(application, user, forum):
    client_for(application, user).post(
        f"/{forum.id}/topic/new",
        data={
            "title": "Forged options",
            "content": "Topic content",
            "important": "y",
            "locked": "y",
            "hidden": "y",
        },
    )
    topic = db.session.execute(sa.select(Topic).where(Topic.title == "Forged options")).scalar_one()

    assert not topic.important
    assert not topic.locked
    assert not topic.hidden


def test_moderator_can_create_highlighted_locked_topic(application, moderator_user, forum):
    client_for(application, moderator_user).post(
        f"/{forum.id}/topic/new",
        data={
            "title": "Moderated topic",
            "content": "Topic content",
            "important": "y",
            "locked": "y",
            "hidden": "y",
        },
    )
    topic = db.session.execute(
        sa.select(Topic).where(Topic.title == "Moderated topic")
    ).scalar_one()

    assert topic.important
    assert topic.locked
    assert not topic.hidden


def test_admin_can_create_hidden_topic(application, admin_user, forum):
    client_for(application, admin_user).post(
        f"/{forum.id}/topic/new",
        data={
            "title": "Hidden topic",
            "content": "Topic content",
            "hidden": "y",
        },
    )
    topic = db.session.execute(sa.select(Topic).where(Topic.title == "Hidden topic")).scalar_one()

    assert topic.hidden
    assert topic.first_post.hidden
    assert topic.hidden_by == admin_user


def test_edit_topic_updates_topic_and_first_post(application, user, topic):
    post = topic.first_post

    response = client_for(application, user).post(
        f"/topic/{topic.id}/edit",
        data={"title": "Updated title", "content": "Updated content"},
    )
    db.session.refresh(topic)
    db.session.refresh(post)

    assert response.status_code == 302
    assert topic.title == "Updated title"
    assert post.content == "Updated content"


def test_member_cannot_change_moderation_options(application, user, topic):
    topic.important = True
    topic.save()

    client_for(application, user).post(
        f"/topic/{topic.id}/edit",
        data={
            "title": topic.title,
            "content": topic.first_post.content,
            "locked": "y",
            "hidden": "y",
        },
    )
    db.session.refresh(topic)

    assert topic.important
    assert not topic.locked
    assert not topic.hidden


def test_admin_can_change_moderation_options(application, admin_user, topic):
    client_for(application, admin_user).post(
        f"/topic/{topic.id}/edit",
        data={
            "title": topic.title,
            "content": topic.first_post.content,
            "important": "y",
            "locked": "y",
            "hidden": "y",
        },
    )
    db.session.refresh(topic)

    assert topic.important
    assert topic.locked
    assert topic.hidden
    assert topic.first_post.hidden
