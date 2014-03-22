"""
    This test will use the default permissions found in
    flaskbb.utils.populate
"""
import pytest

from flaskbb.user.models import User
from flaskbb.forum.models import Forum, Category, Topic, Post
from flaskbb.utils.permissions import *


@pytest.fixture
def category(database):
    category = Category(title="Test Category")
    category.save()
    return category


@pytest.fixture
def forum(category):
    forum = Forum(title="Test Forum", category_id=category.id)
    forum.save()
    return forum


@pytest.fixture
def moderator_user(forum, default_groups):
    """Creates a test user for whom the permissions should be checked"""

    # This should be moved to own fixture which you then use to link the user
    # to the forum
    user = User(username="test_mod", email="test_mod@example.org",
                password="test", primary_group_id=default_groups[2].id)
    user.save()

    forum.moderators.append(user)
    forum.save()
    return user


@pytest.fixture
def normal_user(default_groups):
    """Creates a user with normal permissions"""
    user = User(username="test_normal", email="test_normal@example.org",
                password="test", primary_group_id=default_groups[3].id)
    user.save()
    return user


@pytest.fixture
def admin_user(default_groups):
    """Creates a admin user"""
    user = User(username="test_admin", email="test_admin@example.org",
                password="test", primary_group_id=default_groups[0].id)
    user.save()
    return user


@pytest.fixture
def super_moderator_user(default_groups):
    """Creates a super moderator user"""
    user = User(username="test_super_mod", email="test_super@example.org",
                password="test", primary_group_id=default_groups[1].id)
    user.save()
    return user


@pytest.fixture
def topic_moderator(forum, moderator_user):
    topic = Topic(title="Test Topic Moderator")
    post = Post(content="Test Content Moderator")
    return topic.save(forum=forum, user=moderator_user, post=post)


@pytest.fixture
def topic_normal(forum, normal_user):
    topic = Topic(title="Test Topic Normal")
    post = Post(content="Test Content Normal")
    return topic.save(forum=forum, user=normal_user, post=post)


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
