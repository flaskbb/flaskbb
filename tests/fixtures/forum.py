"""Fixtures for the forum models."""
import datetime
import pytest

from flaskbb.forum.models import Forum, Category, Topic, Post, ForumsRead, \
    TopicsRead


@pytest.fixture
def category(database):
    """A single category."""
    category = Category(title="Test Category")
    category.save()
    return category


@pytest.fixture
def forum(category, default_settings, default_groups):
    """A single forum in a category."""
    forum = Forum(title="Test Forum", category_id=category.id)
    forum.groups = default_groups
    forum.save()
    return forum


@pytest.fixture
def forum_locked(category, default_settings):
    """A single locked forum in a category."""
    forum = Forum(title="Test Forum", category_id=category.id)
    forum.locked = True
    forum.save()
    return forum


@pytest.fixture
def topic(forum, user):
    """A topic by a normal user without any extra permissions."""
    topic = Topic(title="Test Topic Normal")
    post = Post(content="Test Content Normal")
    return topic.save(forum=forum, user=user, post=post)


@pytest.fixture
def topic_moderator(forum, moderator_user):
    """A topic by a user with moderator permissions."""
    topic = Topic(title="Test Topic Moderator")
    post = Post(content="Test Content Moderator")
    return topic.save(forum=forum, user=moderator_user, post=post)


@pytest.fixture
def topic_locked(forum, user):
    """A locked topic by a user with normal permissions."""
    topic = Topic(title="Test Topic Locked")
    topic.locked = True
    post = Post(content="Test Content Locked")
    return topic.save(forum=forum, user=user, post=post)


@pytest.fixture
def topic_in_locked_forum(forum_locked, user):
    """A locked topic by a user with normal permissions."""
    topic = Topic(title="Test Topic Forum Locked")
    post = Post(content="Test Content Forum Locked")
    return topic.save(forum=forum_locked, user=user, post=post)


@pytest.fixture
def last_read():
    """The datetime of the formsread last_read."""
    return datetime.datetime.utcnow() - datetime.timedelta(hours=1)


@pytest.fixture
def forumsread(user, forum, last_read):
    """Create a forumsread object for the user and a forum."""
    forumsread = ForumsRead()
    forumsread.user_id = user.id
    forumsread.forum_id = forum.id
    forumsread.last_read = last_read
    forumsread.save()
    return forumsread


@pytest.fixture
def topicsread(user, topic, last_read):
    """Create a topicsread object for the user and a topic."""
    topicsread = TopicsRead()
    topicsread.user_id = user.id
    topicsread.topic_id = topic.id
    topicsread.forum_id = topic.forum_id
    topicsread.last_read = last_read
    topicsread.save()
    return topicsread
