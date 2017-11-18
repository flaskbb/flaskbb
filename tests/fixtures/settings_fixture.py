import pytest
from flaskbb.utils.forms import SettingValueType


@pytest.fixture
def updated_fixture():
    return (
        # a group where we change a lot
        ('general', {
            'name': "General Settings",
            'description': "This description is wrong.",
            'settings': (
                # change value
                ('project_title', {
                    'value': "FlaskBB is cool!",
                    'value_type': SettingValueType.string,
                    'name': "Project title",
                    'description': "The title of the project.",
                }),
                # add
                ('test_fixture', {
                    'description': 'This is a test fixture',
                    'name': 'Test Fixture',
                    'value': 'FlaskBBTest',
                    'value_type': SettingValueType.string
                }),
            )
        }),
        # a group where we change nothing
        ('auth', {
            'name': 'Authentication Settings',
            'description': 'Settings for the Login and Register process.',
            # the same as in flaskbb/settings/fixtures/settings.py
            'settings': (
                ('registration_enabled', {
                    'value': True,
                    'value_type': SettingValueType.boolean,
                    'name': "Enable Registration",
                    'description': "Enable or disable the registration",
                }),
            )
        }),
        # a wholly new group
        ('testgroup', {
            'name': "Important settings",
            'description': "Some settings without the world would not work.",
            'settings': (
                # change value
                ('monty_python', {
                    'value': "And now for something completely different...",
                    'value_type': SettingValueType.string,
                    'name': "Monty Python",
                    'description': "A random quote from Monty Python.",
                }),
            )
        })
    )
