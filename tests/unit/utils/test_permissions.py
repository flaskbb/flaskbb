"""
    This test will use the default permissions found in
    flaskbb.utils.populate
"""
from flaskbb.utils.permissions import *


def test_moderator_permissions_in_forum(
        forum, moderator_user, topic, topic_moderator):
    """Test the moderator permissions in a forum where the user is a
    moderator.
    """

    assert moderator_user in forum.moderators

    assert can_post_reply(moderator_user, topic)
    assert can_post_topic(moderator_user, forum)
    assert can_edit_post(moderator_user, topic.first_post)

    assert can_moderate(moderator_user, forum)
    assert can_delete_post(moderator_user, topic.first_post)
    assert can_delete_topic(moderator_user, topic)


def test_moderator_permissions_without_forum(
        forum, moderator_user, topic, topic_moderator):
    """Test the moderator permissions in a forum where the user is not a
    moderator.
    """
    forum.moderators.remove(moderator_user)

    assert not moderator_user in forum.moderators
    assert not can_moderate(moderator_user, forum)

    assert can_post_reply(moderator_user, topic)
    assert can_post_topic(moderator_user, forum)

    assert not can_edit_post(moderator_user, topic.first_post)
    assert not can_delete_post(moderator_user, topic.first_post)
    assert not can_delete_topic(moderator_user, topic)

    # Test with own topic
    assert can_delete_post(moderator_user, topic_moderator.first_post)
    assert can_delete_topic(moderator_user, topic_moderator)
    assert can_edit_post(moderator_user, topic_moderator.first_post)

    # Test moderator permissions
    assert can_edit_user(moderator_user)
    assert can_ban_user(moderator_user)


def test_normal_permissions(forum, user, topic):
    """Test the permissions for a normal user."""
    assert not can_moderate(user, forum)

    assert can_post_reply(user, topic)
    assert can_post_topic(user, forum)

    assert can_edit_post(user, topic.first_post)
    assert not can_delete_post(user, topic.first_post)
    assert not can_delete_topic(user, topic)

    assert not can_edit_user(user)
    assert not can_ban_user(user)


def test_admin_permissions(forum, admin_user, topic):
    """Test the permissions for a admin user."""
    assert can_moderate(admin_user, forum)

    assert can_post_reply(admin_user, topic)
    assert can_post_topic(admin_user, forum)

    assert can_edit_post(admin_user, topic.first_post)
    assert can_delete_post(admin_user, topic.first_post)
    assert can_delete_topic(admin_user, topic)

    assert can_edit_user(admin_user)
    assert can_ban_user(admin_user)


def test_super_moderator_permissions(forum, super_moderator_user, topic):
    """Test the permissions for a super moderator user."""
    assert can_moderate(super_moderator_user, forum)

    assert can_post_reply(super_moderator_user, topic)
    assert can_post_topic(super_moderator_user, forum)

    assert can_edit_post(super_moderator_user, topic.first_post)
    assert can_delete_post(super_moderator_user, topic.first_post)
    assert can_delete_topic(super_moderator_user, topic)

    assert can_edit_user(super_moderator_user)
    assert can_ban_user(super_moderator_user)


def test_can_moderate_without_permission(moderator_user):
    """Test can moderate for a moderator_user without a permission."""
    assert can_moderate(moderator_user) is False


def test_permissions_locked_topic(topic_locked, user):
    """Test user permission if a topic is locked."""
    assert topic_locked.locked

    post = topic_locked.first_post
    assert not can_edit_post(user, post)
    assert not can_post_reply(user, topic_locked)


def test_permissions_locked_forum(topic_in_locked_forum, user):
    """Test user permission if forum is locked."""
    topic = topic_in_locked_forum
    post = topic.first_post

    assert not topic.locked
    assert topic.forum.locked

    assert not can_edit_post(user, post)
    assert not can_post_reply(user, topic)
