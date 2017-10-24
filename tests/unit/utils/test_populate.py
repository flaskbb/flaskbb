import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy_utils.functions import create_database, drop_database

from flaskbb.extensions import alembic, db
from flaskbb.utils.populate import delete_settings_from_fixture, \
    create_settings_from_fixture, update_settings_from_fixture, \
    create_default_groups, create_test_data, insert_bulk_data, \
    create_welcome_forum, create_user
from flaskbb.fixtures.groups import fixture as group_fixture
from flaskbb.fixtures.settings import fixture as settings_fixture
from flaskbb.user.models import Group, User
from flaskbb.forum.models import Category, Topic, Post
from flaskbb.management.models import Setting, SettingsGroup


def test_delete_settings_from_fixture(default_settings):
    groups_count = SettingsGroup.query.count()
    assert len(settings_fixture) == groups_count

    deleted = delete_settings_from_fixture(settings_fixture)

    assert len(settings_fixture) == len(deleted)
    assert not SettingsGroup.query.count()
    assert not Setting.query.count()


def test_create_settings_from_fixture(database):
    assert not SettingsGroup.query.count()
    assert not Setting.query.count()

    created = create_settings_from_fixture(settings_fixture)

    assert len(settings_fixture) == len(created)
    assert SettingsGroup.query.count() == len(created)


def test_update_settings_from_fixture(database):
    # No force-overwrite - the fixtures will be created because
    # do not exist.
    assert not SettingsGroup.query.count()
    assert not Setting.query.count()
    updated = update_settings_from_fixture(settings_fixture)
    assert len(updated) == SettingsGroup.query.count()

    # force-overwrite - the fixtures exist, but they will be overwritten now.
    force_updated = update_settings_from_fixture(settings_fixture,
                                                 overwrite_group=True,
                                                 overwrite_setting=True)
    assert len(force_updated) == SettingsGroup.query.count()

    updated_fixture = (
        ('general', {
            'name': "General Settings",
            'description': "How many items per page are displayed.",
            'settings': (
                ('project_title', {
                    'value': "FlaskBB",
                    'value_type': "string",
                    'name': "Project title",
                    'description': "The title of the project.",
                }),
                ('test_fixture', {
                    'description': 'This is a test fixture',
                    'name': 'Test Fixture',
                    'value': 'FlaskBBTest',
                    'value_type': 'string'
                })
            )
        }),
    )

    updated = update_settings_from_fixture(updated_fixture)
    assert len(updated) == 1


def test_create_user(default_groups):
    user = User.query.filter_by(username="admin").first()
    assert not user

    user = create_user(username="admin", password="test",
                       email="test@example.org", groupname="admin")
    assert user.username == "admin"
    assert user.permissions["admin"]


def test_create_welcome_forum(default_groups):
    assert not create_welcome_forum()

    create_user(username="admin", password="test",
                email="test@example.org", groupname="admin")
    assert create_welcome_forum()


def test_create_test_data(database):
    assert Category.query.count() == 0
    data_created = create_test_data()
    assert Category.query.count() == data_created['categories']


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
        group = Group.query.filter_by(name=key).first()

        for attribute, value in attributes.items():
            assert getattr(group, attribute) == value


def test_migrations_upgrade():
    with pytest.raises(OperationalError):
        User.query.all()

    # ensure that the database is created
    create_database(db.engine.url)

    alembic.upgrade()
    assert len(User.query.all()) == 0

    drop_database(db.engine.url)
