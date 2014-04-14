import pytest

from flaskbb.forum.models import Forum, Category, Topic, Post


@pytest.fixture
def category(database):
    """A single category."""
    category = Category(title="Test Category")
    category.save()
    return category


@pytest.fixture
def forum(category):
    """A single forum in a category."""
    forum = Forum(title="Test Forum", category_id=category.id)
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
