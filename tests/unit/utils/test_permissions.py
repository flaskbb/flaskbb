"""
    This test will use the default permissions found in
    flaskbb.utils.populate
"""
import pytest

from flaskbb.forum.models import Topic, Post
from flaskbb.utils.permissions import *


def test_moderator_permissions_in_forum(
        forum, moderator_user, topic_normal, topic_moderator):
    """Test that the default groups are created correctly."""

    moderator_user.permissions = moderator_user.get_permissions()

    assert moderator_user in forum.moderators

    assert can_post_reply(moderator_user, forum)
    assert can_post_topic(moderator_user, forum)
    assert can_edit_post(moderator_user, topic_normal.user_id, forum)

    assert can_moderate(moderator_user, forum)
    assert can_delete_post(moderator_user, topic_normal.user_id, forum)
    assert can_delete_topic(moderator_user, topic_normal.user_id, forum)

    assert can_lock_topic(moderator_user, forum)
    assert can_merge_topic(moderator_user, forum)
    assert can_move_topic(moderator_user, forum)


def test_moderator_permissions_without_forum(
        forum, moderator_user, topic_normal, topic_moderator):
    forum.moderators.remove(moderator_user)
    moderator_user.permissions = moderator_user.get_permissions()

    assert not moderator_user in forum.moderators
    assert not can_moderate(moderator_user, forum)

    assert can_post_reply(moderator_user, forum)
    assert can_post_topic(moderator_user, forum)

    assert not can_edit_post(moderator_user, topic_normal.user_id, forum)
    assert not can_delete_post(moderator_user, topic_normal.user_id, forum)
    assert not can_delete_topic(moderator_user, topic_normal.user_id, forum)

    assert not can_lock_topic(moderator_user, forum)
    assert not can_merge_topic(moderator_user, forum)
    assert not can_move_topic(moderator_user, forum)

    # Test with own topic
    assert can_delete_post(moderator_user, topic_moderator.user_id, forum)
    assert can_delete_topic(moderator_user, topic_moderator.user_id, forum)
    assert can_edit_post(moderator_user, topic_moderator.user_id, forum)


def test_normal_permissions(forum, normal_user, topic_normal):

    normal_user.permissions = normal_user.get_permissions()

    assert not can_moderate(normal_user, forum)

    assert can_post_reply(normal_user, forum)
    assert can_post_topic(normal_user, forum)

    assert can_edit_post(normal_user, topic_normal.user_id, forum)
    assert not can_delete_post(normal_user, topic_normal.user_id, forum)
    assert not can_delete_topic(normal_user, topic_normal.user_id, forum)

    assert not can_lock_topic(normal_user, forum)
    assert not can_merge_topic(normal_user, forum)
    assert not can_move_topic(normal_user, forum)


def test_admin_permissions(forum, admin_user, topic_normal):
    admin_user.permissions = admin_user.get_permissions()

    assert can_moderate(admin_user, forum)

    assert can_post_reply(admin_user, forum)
    assert can_post_topic(admin_user, forum)

    assert can_edit_post(admin_user, topic_normal.user_id, forum)
    assert can_delete_post(admin_user, topic_normal.user_id, forum)
    assert can_delete_topic(admin_user, topic_normal.user_id, forum)

    assert can_lock_topic(admin_user, forum)
    assert can_merge_topic(admin_user, forum)
    assert can_move_topic(admin_user, forum)


def test_super_moderator_permissions(forum, super_moderator_user, topic_normal):
    super_moderator_user.permissions = super_moderator_user.get_permissions()

    assert can_moderate(super_moderator_user, forum)

    assert can_post_reply(super_moderator_user, forum)
    assert can_post_topic(super_moderator_user, forum)

    assert can_edit_post(super_moderator_user, topic_normal.user_id, forum)
    assert can_delete_post(super_moderator_user, topic_normal.user_id, forum)
    assert can_delete_topic(super_moderator_user, topic_normal.user_id, forum)

    assert can_lock_topic(super_moderator_user, forum)
    assert can_merge_topic(super_moderator_user, forum)
    assert can_move_topic(super_moderator_user, forum)
