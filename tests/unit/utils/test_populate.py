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


def _individual_settings(update_result):
    """Helper that returns the number of settings that were updated."""
    return sum(
        len(settings_in_a_group)
        for settings_in_a_group in update_result.values()
    )


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
    settings_fixture_group_count = len(settings_fixture)
    settings_fixture_setting_count = sum(
        len(settings_fixture[k][1]['settings'])
        for k in range(len(settings_fixture))
    )

    assert not SettingsGroup.query.count()
    assert not Setting.query.count()

    # No force-overwrite - the fixtures will be created because they
    # do not exist.
    updated = update_settings_from_fixture(settings_fixture)
    assert settings_fixture_group_count == len(updated)
    assert settings_fixture_group_count == SettingsGroup.query.count()
    assert settings_fixture_setting_count == _individual_settings(updated)
    assert settings_fixture_setting_count == Setting.query.count()


def test_update_settings_from_fixture_overwrite(database, default_settings,
                                                updated_fixture):
    # should add groups: testgroup
    # should add testgroup/monty_python, general/test_fixture
    pre_update_group_count = SettingsGroup.query.count()
    pre_update_setting_count = Setting.query.count()
    updated = update_settings_from_fixture(updated_fixture)
    assert len(updated) == 2
    assert _individual_settings(updated) == 2
    assert pre_update_group_count + 1 == SettingsGroup.query.count()
    assert pre_update_setting_count + 2 == Setting.query.count()


def test_update_settings_from_fixture_force(database, default_settings,
                                            updated_fixture):
    # force-overwrite - nothing changed so nothing should happen here
    pre_update_group_count = SettingsGroup.query.count()
    pre_update_setting_count = Setting.query.count()
    force_updated = update_settings_from_fixture(settings_fixture,
                                                 overwrite_group=True,
                                                 overwrite_setting=True)

    assert len(force_updated) == 0
    assert _individual_settings(force_updated) == 0
    assert pre_update_group_count == SettingsGroup.query.count()
    assert pre_update_setting_count == Setting.query.count()

    # should update groups: general
    # should update settings: 2 in general, 1 in testgroup
    force_updated_1 = update_settings_from_fixture(updated_fixture,
                                                   overwrite_group=True,
                                                   overwrite_setting=True)
    assert len(force_updated_1) == 2
    assert _individual_settings(force_updated_1) == 3
    assert pre_update_group_count + 1 == SettingsGroup.query.count()
    assert pre_update_setting_count + 2 == Setting.query.count()


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
