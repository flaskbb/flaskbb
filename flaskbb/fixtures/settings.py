# -*- coding: utf-8 -*-
"""
    flaskbb.fixtures.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The fixtures module for our settings.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.utils.forms import SettingValueType
from flaskbb.utils.helpers import get_available_languages as available_languages
from flaskbb.utils.helpers import get_available_themes as available_themes


def available_avatar_types():
    return [("PNG", "PNG"), ("JPEG", "JPG"), ("GIF", "GIF")]


fixture = (
    # Settings Group
    (
        "general",
        {
            "name": "General Settings",
            "description": "How many items per page are displayed.",
            "settings": (
                (
                    "project_title",
                    {
                        "value": "FlaskBB",
                        "value_type": SettingValueType.string,
                        "name": "Project title",
                        "description": "The title of the project.",
                    },
                ),
                (
                    "project_subtitle",
                    {
                        "value": "A lightweight forum software in Flask",
                        "value_type": SettingValueType.string,
                        "name": "Project subtitle",
                        "description": "A short description of the project.",
                    },
                ),
                (
                    "project_copyright",
                    {
                        "value": "",
                        "value_type": SettingValueType.string,
                        "name": "Project Copyright",
                        "description": "Copyright notice of the Project like '&copy; 2018 FlaskBB'. Leave blank to ignore.",  # noqa
                    },
                ),
                (
                    "posts_per_page",
                    {
                        "value": 10,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 5},
                        "name": "Posts per page",
                        "description": "Number of posts displayed per page.",
                    },
                ),
                (
                    "topics_per_page",
                    {
                        "value": 10,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 5},
                        "name": "Topics per page",
                        "description": "Number of topics displayed per page.",
                    },
                ),
                (
                    "users_per_page",
                    {
                        "value": 10,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 5},
                        "name": "Users per page",
                        "description": "Number of users displayed per page.",
                    },
                ),
            ),
        },
    ),
    (
        "auth",
        {
            "name": "Authentication Settings",
            "description": "Configurations for the Login and Register process.",
            "settings": (
                (
                    "registration_enabled",
                    {
                        "value": True,
                        "value_type": SettingValueType.boolean,
                        "name": "Enable Registration",
                        "description": "Enable or disable the registration",
                    },
                ),
                (
                    "activate_account",
                    {
                        "value": True,
                        "value_type": SettingValueType.boolean,
                        "name": "Enable Account Activation",
                        "description": "Enable to let the user activate their account by sending a email with an activation link.",  # noqa
                    },
                ),
                (
                    "auth_username_min_length",
                    {
                        "value": 3,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Username Minimum Length",
                        "description": "The minimum length of the username. Changing this will only affect new registrations.",  # noqa
                    },
                ),
                (
                    "auth_username_max_length",
                    {
                        "value": 20,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Username Maximum Length",
                        "description": "The Maximum length of the username. Changing this will only affect new registrations.",  # noqa
                    },
                ),
                (
                    "auth_username_blacklist",
                    {
                        "value": "me,administrator,moderator",
                        "value_type": SettingValueType.string,
                        "name": "Username Blacklist",
                        "description": "A comma seperated list with forbidden usernames.",  # noqa
                    },
                ),
                (
                    "auth_ratelimit_enabled",
                    {
                        "value": True,
                        "value_type": SettingValueType.boolean,
                        "name": "Enable Auth Rate Limiting",
                        "description": "Enable rate limiting on 'auth' routes. This will limit the amount of requests per minute to a given amount and time.",  # noqa
                    },
                ),
                (
                    "auth_requests",
                    {
                        "value": 20,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 1},
                        "name": "Auth Requests",
                        "description": "Number of requests on each 'auth' route before the user has to wait a given timeout until he can access the resource again.",  # noqa
                    },
                ),
                (
                    "auth_timeout",
                    {
                        "value": 15,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Auth Timeout",
                        "description": "The timeout for how long the user has to wait until he can access the resource again (in minutes).",  # noqa
                    },
                ),
                (
                    "login_recaptcha",
                    {
                        "value": 5,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Login reCAPTCHA",
                        "description": "Use a CAPTCHA after a specified amount of failed login attempts.",  # noqa
                    },
                ),
                (
                    "recaptcha_enabled",
                    {
                        "value": False,
                        "value_type": SettingValueType.boolean,
                        "name": "Enable reCAPTCHA",
                        "description": (
                            "Helps to prevent bots from creating accounts. "
                            "For more information visit this link: <a href=http://www.google.com/recaptcha>http://www.google.com/recaptcha</a>"  # noqa
                        ),
                    },
                ),
                (
                    "recaptcha_public_key",
                    {
                        "value": "",
                        "value_type": SettingValueType.string,
                        "name": "reCAPTCHA Site Key",
                        "description": "Your public recaptcha key ('Site key').",  # noqa
                    },
                ),
                (
                    "recaptcha_private_key",
                    {
                        "value": "",
                        "value_type": SettingValueType.string,
                        "name": "reCAPTCHA Secret Key",
                        "description": "The private key ('Secret key'). Keep this a secret!",  # noqa
                    },
                ),
            ),
        },
    ),
    (
        "misc",
        {
            "name": "Misc Settings",
            "description": "Miscellaneous settings.",
            "settings": (
                (
                    "message_quota",
                    {
                        "value": 50,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Private Message Quota",
                        "description": "The amount of messages a user can have.",  # noqa
                    },
                ),
                (
                    "online_last_minutes",
                    {
                        "value": 15,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Online last minutes",
                        "description": "How long a user can be inactive before he is marked as offline. 0 to disable it.",  # noqa
                    },
                ),
                (
                    "title_length",
                    {
                        "value": 15,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Topic title length",
                        "description": "The length of the topic title shown on the index.",  # noqa
                    },
                ),
                (
                    "tracker_length",
                    {
                        "value": 7,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Tracker length",
                        "description": "The days for how long the forum should deal with unread topics. 0 to disable it.",  # noqa
                    },
                ),
                (
                    "avatar_height",
                    {
                        "value": 150,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Avatar Height",
                        "description": "The allowed height of an avatar in pixels.",  # noqa
                    },
                ),
                (
                    "avatar_width",
                    {
                        "value": 150,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Avatar Width",
                        "description": "The allowed width of an avatar in pixels.",  # noqa
                    },
                ),
                (
                    "avatar_size",
                    {
                        "value": 200,
                        "value_type": SettingValueType.integer,
                        "extra": {"min": 0},
                        "name": "Avatar Size",
                        "description": "The allowed size of the avatar in kilobytes.",  # noqa
                    },
                ),
                (
                    "avatar_types",
                    {
                        "value": ["PNG", "JPEG", "GIF"],
                        "value_type": SettingValueType.selectmultiple,
                        "extra": {"choices": available_avatar_types},
                        "name": "Avatar Types",
                        "description": "The allowed types of an avatar. Such as JPEG, GIF or PNG.",  # noqa
                    },
                ),
                (
                    "signature_enabled",
                    {
                        "value": True,
                        "value_type": SettingValueType.boolean,
                        "extra": {},
                        "name": "Enable Signatures",
                        "description": "Enable signatures in posts.",
                    },
                ),
            ),
        },
    ),
    (
        "appearance",
        {
            "name": "Appearance Settings",
            "description": "Change the theme and language for your forum.",
            "settings": (
                (
                    "default_theme",
                    {
                        "value": "aurora",
                        "value_type": SettingValueType.select,
                        "extra": {"choices": available_themes},
                        "name": "Default Theme",
                        "description": "Change the default theme for your forum.",  # noqa
                    },
                ),
                (
                    "default_language",
                    {
                        "value": "en",
                        "value_type": SettingValueType.select,
                        "extra": {"choices": available_languages},
                        "name": "Default Language",
                        "description": "Change the default language for your forum.",  # noqa
                    },
                ),
            ),
        },
    ),
)
