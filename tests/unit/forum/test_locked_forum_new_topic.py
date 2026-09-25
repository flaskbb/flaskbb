import pytest
from flask import g
from flask_login.test_client import FlaskLoginClient


@pytest.fixture(autouse=True)
def clear_current_objects():
    # g lives on the package-scoped app context, so other tests leave their topic/forum behind
    for name in ("post", "topic", "forum", "category"):
        g.pop(name, None)
    yield
    for name in ("post", "topic", "forum", "category"):
        g.pop(name, None)


def client_for(application, user):
    application.test_client_class = FlaskLoginClient
    return application.test_client(user=user)


def test_admin_sees_new_topic_button_in_locked_forum(application, admin_user, forum_locked):
    response = client_for(application, admin_user).get(f"/forum/{forum_locked.id}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f"/{forum_locked.id}-{forum_locked.slug}/topic/new" in html


def test_member_does_not_see_new_topic_button_in_locked_forum(application, user, forum_locked):
    response = client_for(application, user).get(f"/forum/{forum_locked.id}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f"/{forum_locked.id}-{forum_locked.slug}/topic/new" not in html


def test_admin_can_create_topic_in_locked_forum(application, admin_user, forum_locked):
    client = client_for(application, admin_user)
    url = f"/{forum_locked.id}-{forum_locked.slug}/topic/new"

    assert client.get(url).status_code == 200


def test_member_cannot_open_new_topic_form_in_locked_forum(application, user, forum_locked):
    client = client_for(application, user)
    url = f"/{forum_locked.id}-{forum_locked.slug}/topic/new"

    assert client.get(url).status_code == 302


def test_super_moderator_cannot_create_topic_in_locked_forum(
    application, super_moderator_user, forum_locked
):
    client = client_for(application, super_moderator_user)
    url = f"/{forum_locked.id}-{forum_locked.slug}/topic/new"

    assert client.get(url).status_code == 302
    assert url not in client.get(f"/forum/{forum_locked.id}").get_data(as_text=True)


def test_forum_moderator_cannot_create_topic_in_locked_forum(application, moderator_user, forum):
    forum.locked = True
    forum.save()
    client = client_for(application, moderator_user)
    url = f"/{forum.id}-{forum.slug}/topic/new"

    assert client.get(url).status_code == 302
    assert url not in client.get(f"/forum/{forum.id}").get_data(as_text=True)


def test_super_moderator_can_still_edit_topic_in_locked_forum(
    application, super_moderator_user, topic_in_locked_forum
):
    client = client_for(application, super_moderator_user)

    assert client.get(f"/topic/{topic_in_locked_forum.id}/edit").status_code == 200
