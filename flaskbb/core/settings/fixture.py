from pluggy import HookimplMarker

from .definitions import IntSetting, SettingGroup, StringSetting

impl = HookimplMarker("flaskbb")

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
    ),
)


@impl
def flaskbb_load_setting_groups():
    return general_group
