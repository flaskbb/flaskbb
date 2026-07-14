from flaskbb.fixtures.groups import fixture as group_fixture
from flaskbb.forum.models import Category, Post, Topic
from flaskbb.user.models import Group, User
from flaskbb.utils.populate import (
    create_default_groups,
    create_test_data,
    create_user,
    create_welcome_forum,
    insert_bulk_data,
)


def test_create_user(default_groups):
    user = User.get_by(username="admin")
    assert not user

    user = create_user(
        username="admin", password="test", email="test@example.org", groupname="admin"
    )
    assert user.username == "admin"
    assert user.permissions["admin"]


def test_create_welcome_forum(default_groups):
    assert not create_welcome_forum()

    create_user(
        username="admin", password="test", email="test@example.org", groupname="admin"
    )
    assert create_welcome_forum()


def test_create_test_data(database):
    assert Category.query.count() == 0
    data_created = create_test_data()
    assert Category.query.count() == data_created["categories"]


def test_insert_bulk_data(database):
    assert not insert_bulk_data(topic_count=1, post_count=1)

    create_test_data(categories=1, forums=1, topics=0)
    assert Topic.query.count() == 0

    topics, posts = insert_bulk_data(topic_count=1, post_count=1)
    assert Topic.query.count() == topics
    # -1 bc the topic post also counts as post
    assert Post.query.count() - 1 == posts


def test_create_default_groups(database):
    """Test that the default groups are created correctly."""

    assert Group.query.count() == 0

    create_default_groups()

    assert Group.query.count() == len(group_fixture)

    for key, attributes in group_fixture.items():
        group = Group.get_by(name=key)

        for attribute, value in attributes.items():
            assert getattr(group, attribute) == value
