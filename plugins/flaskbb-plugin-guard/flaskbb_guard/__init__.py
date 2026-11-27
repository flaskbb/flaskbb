"""FlaskBB-Guard: AI-driven automatic content moderation for FlaskBB."""

import logging

from flaskbb.settings import BoolSetting, IntSetting, SettingGroup
from pluggy import HookimplMarker

hookimpl = HookimplMarker("flaskbb")
logger = logging.getLogger("flaskbb.guard")


SETTINGS = SettingGroup(
    key="guard",
    name="FlaskBB-Guard (AutoMod)",
    description="Settings for AI-based automatic content moderation.",
    settings=(
        BoolSetting(
            key="AUTOMOD_ENABLED",
            value=True,
            name="Enable AutoMod",
            description="Automatically check new and edited posts.",
        ),
        IntSetting(
            key="AUTOMOD_THRESHOLD",
            value=80,
            min=0,
            max=100,
            name="Report threshold (%)",
            description="Posts scoring at or above this percentage are reported to moderators.",
        ),
    ),
)


@hookimpl
def flaskbb_load_setting_groups():
    """Register FlaskBB-Guard's settings with the admin panel."""
    return SETTINGS


@hookimpl
def flaskbb_event_post_save_after(post, is_new):
    """Called by FlaskBB every time a post is saved."""
    logger.info("FlaskBB-Guard: post %s saved (new=%s)", post.id, is_new)