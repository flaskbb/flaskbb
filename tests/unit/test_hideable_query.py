from flask_login import login_user

from flaskbb.forum.models import Topic


def test_guest_user_cannot_see_hidden_posts(guest, topic, user,
                                            request_context):
    topic.hide(user)
    login_user(guest)
    assert Topic.query.filter(Topic.id == topic.id).first() is None


def test_regular_user_cannot_see_hidden_posts(topic, user, request_context):
    topic.hide(user)
    login_user(user)
    assert Topic.query.filter(Topic.id == topic.id).first() is None


def test_moderator_user_can_see_hidden_posts(topic, moderator_user,
                                             request_context):
    topic.hide(moderator_user)
    login_user(moderator_user)
    assert Topic.query.filter(Topic.id == topic.id).first() is not None


def test_super_moderator_user_can_see_hidden_posts(topic, super_moderator_user,
                                                   request_context):
    topic.hide(super_moderator_user)
    login_user(super_moderator_user)
    assert Topic.query.filter(Topic.id == topic.id).first() is not None


def test_admin_user_can_see_hidden_posts(topic, admin_user, request_context):
    topic.hide(admin_user)
    login_user(admin_user)
    assert Topic.query.filter(Topic.id == topic.id).first() is not None
