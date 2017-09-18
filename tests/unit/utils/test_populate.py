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
    def individual_settings(update_result):
        """helper that returns the number of settings that were updated"""
        return sum(len(settings_in_a_group) for settings_in_a_group in update_result.values())

    settings_fixture_group_count = len(settings_fixture)
    settings_fixture_setting_count = sum(
        len(settings_fixture[k][1]['settings']) for k in range(len(settings_fixture))
    )


    assert not SettingsGroup.query.count()
    assert not Setting.query.count()

    # No force-overwrite - the fixtures will be created because they do not exist.
    updated_1 = update_settings_from_fixture(settings_fixture)
    assert settings_fixture_group_count == len(updated_1)
    assert settings_fixture_group_count == SettingsGroup.query.count()
    assert settings_fixture_setting_count == individual_settings(updated_1)
    assert settings_fixture_setting_count == Setting.query.count()

    # force-overwrite - nothing changed so nothing should happen here
    force_updated_1 = update_settings_from_fixture(settings_fixture,
                                                   overwrite_group=True,
                                                   overwrite_setting=True)

    assert len(force_updated_1) == 0
    assert individual_settings(force_updated_1) == 0
    assert settings_fixture_group_count == SettingsGroup.query.count()
    assert settings_fixture_setting_count == Setting.query.count()

    fixture_to_update_with = (
        # a group where we change a lot
        ('general', {
            'name': "General Settings",
            'description': "This description is wrong.",
            'settings': (
                # change value
                ('project_title', {
                    'value': "FlaskBB is cool!",
                    'value_type': "string",
                    'name': "Project title",
                    'description': "The title of the project.",
                }),
                # change name
                ('project_subtitle', {
                    'value':        "A lightweight forum software in Flask",
                    'value_type':   "string",
                    'name':         "Subtitle of the project",
                    'description':  "A short description of the project.",
                }),
                # change options (extra)
                ('posts_per_page', {
                    'value':        10,
                    'value_type':   "integer",
                    'extra':        {'min': 1},
                    'name':         "Posts per page",
                    'description':  "Number of posts displayed per page.",
                }),
                # change description
                ('topics_per_page', {
                    'value':        10,
                    'value_type':   "integer",
                    'extra':        {'min': 5},
                    'name':         "Topics per page",
                    'description':  "The number of topics to be displayed per page.",
                }),
                # add
                ('test_fixture', {
                    'description': 'This is a test fixture',
                    'name': 'Test Fixture',
                    'value': 'FlaskBBTest',
                    'value_type': 'string'
                }),
            )
        }),
        # a group where we change nothing
        ('auth', {
            'name': 'Authentication Settings',
            'description': 'Configurations for the Login and Register process!',
            # the same as in flaskbb/settings/fixtures/settings.py
            'settings': (
                ('registration_enabled', {
                    'value':        True,
                    'value_type':   "boolean",
                    'name':         "Enable Registration",
                    'description':  "Enable or disable the registration",
                }),
            )
        }),
        # a wholly new group
        ('testgroup', {
            'name': "Important settings",
            'description': "Some settings without which the world would not work.",
            'settings': (
                # change value
                ('monty_python', {
                    'value': "And now for something completely different...",
                    'value_type': "string",
                    'name': "Monty Python",
                    'description': "A random quote from Monty Python.",
                }),
            )
        })
    )

    # should add groups: testgroup
    # should add testgroup/monty_python, general/test_fixture
    updated_2 = update_settings_from_fixture(fixture_to_update_with)
    assert len(updated_2) == 2
    assert individual_settings(updated_2) == 2
    assert settings_fixture_group_count + 1 == SettingsGroup.query.count()
    assert settings_fixture_setting_count + 2 == Setting.query.count()

    fixture_to_update_with[2][1]['settings'][0][1]['description'] = "Something meaningless."

    # should update groups: general
    # should update settings: 4 in general, 1 in testgroup
    force_updated_2 = update_settings_from_fixture(fixture_to_update_with,
                                                   overwrite_group=True,
                                                   overwrite_setting=True)
    assert len(force_updated_2) == 2
    assert individual_settings(force_updated_2) == 5
    assert settings_fixture_group_count + 1 == SettingsGroup.query.count()
    assert settings_fixture_setting_count + 2 == Setting.query.count()

    modified_settings_fixture = [item for item in settings_fixture]
    modified_settings_fixture.append(
        # another wholly new group
        ('testgroup2', {
            'name': "Important settings",
            'description': "Some settings without which the world would not work.",
            'settings': (
                # change value
                ('monty_python_reborn', {
                    'value': "And now for something completely different...",
                    'value_type': "string",
                    'name': "Monty Python",
                    'description': "A random quote from Monty Python.",
                }),
            )
        })
    )

    # should revert 4 in general
    # should add testgroup2 and one subitem
    force_updated_3 = update_settings_from_fixture(modified_settings_fixture,
                                                   overwrite_group=True,
                                                   overwrite_setting=True)

    assert len(force_updated_3) == 2
    assert individual_settings(force_updated_3) == 5
    assert settings_fixture_group_count + 2 == SettingsGroup.query.count()
    assert settings_fixture_setting_count + 3 == Setting.query.count()


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
