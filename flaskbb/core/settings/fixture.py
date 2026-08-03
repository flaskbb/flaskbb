"""
flaskbb.core.settings.fixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This modules holds the actual setting definitions (fixtures) for FlaskBB.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from pluggy import HookimplMarker

from flaskbb.utils.helpers import get_available_languages, get_available_themes

from .definitions import (
    BoolSetting,
    IntSetting,
    SelectMultipleSetting,
    SelectSetting,
    SettingGroup,
    StringSetting,
)

impl = HookimplMarker("flaskbb")


def _avatar_type_choices() -> list[tuple[str, str]]:
    return [("PNG", "PNG"), ("JPEG", "JPG"), ("GIF", "GIF")]


general_group = SettingGroup(
    key="general",
    name="General Settings",
    description="General settings for your FlaskBB forum.",
    settings=(
        StringSetting(
            key="PROJECT_TITLE",
            value="FlaskBB",
            name="Project title",
            description="The title of your forum.",
        ),
        StringSetting(
            key="PROJECT_SUBTITLE",
            value="A lightweight forum software in Flask",
            name="Project Subtitle",
            description="The subtitle of your forum.",
        ),
        StringSetting(
            key="PROJECT_COPYRIGHT",
            value="",
            name="Copyright",
            description=(
                "Copyright notice of the Project like '&copy; 2018 FlaskBB'. "
                "Leave blank to ignore."
            ),
        ),
        IntSetting(
            key="POSTS_PER_PAGE",
            value=10,
            min=5,
            name="Posts per page",
            description="Number of posts displayed per page.",
        ),
        IntSetting(
            key="TOPICS_PER_PAGE",
            value=10,
            min=5,
            name="Topics per page",
            description="Number of topics displayed per page.",
        ),
        IntSetting(
            key="USERS_PER_PAGE",
            value=10,
            min=5,
            name="Users per page",
            description="Number of users displayed per page.",
        ),
        BoolSetting(
            key="MEMBERLIST_ENABLED",
            value=True,
            name="Enable Memberlist",
            description=(
                "Show the memberlist. If disabled, the memberlist is no longer "
                "reachable."
            ),
        ),
        BoolSetting(
            key="OPEN_LINKS_IN_NEW_TAB",
            value=False,
            name="Open external links in a new tab",
            description=(
                "Open links to external websites within posts in a new "
                "browser tab. Users can override this in their own "
                "settings."
            ),
        ),
    ),
)


auth_group = SettingGroup(
    key="auth",
    name="Authentication Settings",
    description="Configurations for the Login and Register process.",
    settings=(
        BoolSetting(
            key="REGISTRATION_ENABLED",
            value=True,
            name="Enable Registration",
            description="Enable or disable the registration",
        ),
        BoolSetting(
            key="ACTIVATE_ACCOUNT",
            value=True,
            name="Enable Account Activation",
            description=(
                "Enable to let the user activate their account by sending "
                "a email with an activation link."
            ),
        ),
        IntSetting(
            key="AUTH_USERNAME_MIN_LENGTH",
            value=3,
            min=0,
            name="Username Minimum Length",
            description=(
                "The minimum length of the username. Changing this will "
                "only affect new registrations."
            ),
        ),
        IntSetting(
            key="AUTH_USERNAME_MAX_LENGTH",
            value=20,
            min=0,
            name="Username Maximum Length",
            description=(
                "The Maximum length of the username. Changing this will "
                "only affect new registrations."
            ),
        ),
        StringSetting(
            key="AUTH_USERNAME_BLACKLIST",
            value="me,administrator,moderator",
            name="Username Blacklist",
            description="A comma seperated list with forbidden usernames.",
        ),
        BoolSetting(
            key="AUTH_RATELIMIT_ENABLED",
            value=True,
            name="Enable Auth Rate Limiting",
            description=(
                "Enable rate limiting on 'auth' routes. This will limit "
                "the amount of requests per minute to a given amount and "
                "time."
            ),
        ),
        IntSetting(
            key="AUTH_REQUESTS",
            value=20,
            min=1,
            name="Auth Requests",
            description=(
                "Number of requests on each 'auth' route before the user "
                "has to wait a given timeout until he can access the "
                "resource again."
            ),
        ),
        IntSetting(
            key="AUTH_TIMEOUT",
            value=15,
            min=0,
            name="Auth Timeout",
            description=(
                "The timeout for how long the user has to wait until he "
                "can access the resource again (in minutes)."
            ),
        ),
        IntSetting(
            key="LOGIN_RECAPTCHA",
            value=5,
            min=0,
            name="Login reCAPTCHA",
            description=(
                "Use a CAPTCHA after a specified amount of failed login attempts."
            ),
        ),
        BoolSetting(
            key="RECAPTCHA_ENABLED",
            value=False,
            name="Enable reCAPTCHA",
            description=(
                "Helps to prevent bots from creating accounts. "
                "RECAPTCHA_PUBLIC_KEY (Site Key) and RECAPTCHA_PRIVATE_KEY "
                "(Secret Key) must be set via environment variables or in "
                "'flaskbb.cfg'."
            ),
        ),
    ),
)


misc_group = SettingGroup(
    key="misc",
    name="Misc Settings",
    description="Miscellaneous settings.",
    settings=(
        IntSetting(
            key="ONLINE_LAST_MINUTES",
            value=15,
            min=0,
            name="Online last minutes",
            description=(
                "How long a user can be inactive before he is marked as "
                "offline. 0 to disable it."
            ),
        ),
        IntSetting(
            key="TITLE_LENGTH",
            value=15,
            min=0,
            name="Topic title length",
            description="The length of the topic title shown on the index.",
        ),
        IntSetting(
            key="TRACKER_LENGTH",
            value=7,
            min=0,
            name="Tracker length",
            description=(
                "The days for how long the forum should deal with unread "
                "topics. 0 to disable it."
            ),
        ),
        IntSetting(
            key="SEARCH_SNIPPET_LENGTH",
            value=320,
            min=0,
            name="Search snippet length",
            description=(
                "The number of characters shown around a search match in "
                "the global search results. 0 to show the full content."
            ),
        ),
        IntSetting(
            key="AVATAR_HEIGHT",
            value=150,
            min=0,
            name="Avatar Height",
            description="The allowed height of an avatar in pixels.",
        ),
        IntSetting(
            key="AVATAR_WIDTH",
            value=150,
            min=0,
            name="Avatar Width",
            description="The allowed width of an avatar in pixels.",
        ),
        IntSetting(
            key="AVATAR_SIZE",
            value=200,
            min=0,
            name="Avatar Size",
            description="The allowed size of the avatar in kilobytes.",
        ),
        SelectMultipleSetting(
            key="AVATAR_TYPES",
            value=["PNG", "JPEG", "GIF"],
            choices=_avatar_type_choices,
            coerce=str,
            name="Avatar Types",
            description="The allowed types of an avatar. Such as JPEG, GIF or PNG.",
        ),
        BoolSetting(
            key="SIGNATURE_ENABLED",
            value=True,
            name="Enable Signatures",
            description="Enable signatures in posts.",
        ),
    ),
)


attachments_group = SettingGroup(
    key="attachments",
    name="Attachment Settings",
    description="Settings for post attachments.",
    settings=(
        BoolSetting(
            key="ATTACHMENTS_ENABLED",
            value=True,
            name="Enable Attachments",
            description="Allow users to attach files to their posts.",
        ),
        BoolSetting(
            key="ATTACHMENT_IMAGE_PREVIEWS",
            value=True,
            name="Enable attachment previews for images",
            description="Show image attachments as inline previews in posts.",
        ),
        IntSetting(
            key="ATTACHMENT_MAX_SIZE",
            value=1024,
            min=0,
            name="Attachment Size",
            description="The allowed size per attachment in kilobytes.",
        ),
        IntSetting(
            key="ATTACHMENTS_PER_POST",
            value=5,
            min=1,
            name="Attachments per Post",
            description="The maximum number of attachments per post.",
        ),
        StringSetting(
            key="ATTACHMENT_TYPES",
            value="png, jpg, jpeg, gif, pdf",
            name="Attachment Types",
            description=(
                "A comma separated list of the allowed file extensions for attachments."
            ),
        ),
    ),
)


appearance_group = SettingGroup(
    key="appearance",
    name="Appearance Settings",
    description="Change the theme and language for your forum.",
    settings=(
        SelectSetting(
            key="DEFAULT_THEME",
            value="aurora",
            choices=get_available_themes,
            coerce=str,
            name="Default Theme",
            description="Change the default theme for your forum.",
        ),
        SelectSetting(
            key="DEFAULT_LANGUAGE",
            value="en",
            choices=get_available_languages,
            coerce=str,
            name="Default Language",
            description="Change the default language for your forum.",
        ),
    ),
)


@impl
def flaskbb_load_internal_setting_groups():
    return [
        general_group,
        auth_group,
        misc_group,
        attachments_group,
        appearance_group,
    ]
