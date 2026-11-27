"""FlaskBB-Guard: AI-based toxicity detection for FlaskBB."""

import logging

from flaskbb.settings import BoolSetting, IntSetting, SettingGroup
from pluggy import HookimplMarker

from .classifier import KeywordClassifier
from .service import ToxicityDetectionService

hookimpl = HookimplMarker("flaskbb")
logger = logging.getLogger("flaskbb.guard")


SETTINGS = SettingGroup(
    key="guard",
    name="FlaskBB-Guard (Toxicity Detection)",
    description="Settings for AI-based toxicity detection.",
    settings=(
        BoolSetting(
            key="AUTOMOD_ENABLED",
            value=True,
            name="Enable toxicity detection",
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
        BoolSetting(
            key="AUTOMOD_EXEMPT_STAFF",
            value=True,
            name="Skip moderators and administrators",
            description="Do not check posts written by moderators and administrators.",
        ),
    ),
)

_service: ToxicityDetectionService | None = None


def get_service() -> ToxicityDetectionService:
    """Create the service once and reuse it (the classifier is loaded once)."""
    global _service
    if _service is None:
        _service = ToxicityDetectionService(KeywordClassifier())
    return _service


@hookimpl
def flaskbb_load_setting_groups():
    """Register FlaskBB-Guard's settings with the admin panel."""
    return SETTINGS


@hookimpl
def flaskbb_event_post_save_after(post, is_new):
    """Called by FlaskBB every time a post is saved (new or edited)."""
    try:
        get_service().check_post(post)
    except Exception:
        # fail-open: the post is already saved; detection must never break posting
        logger.exception("FlaskBB-Guard: toxicity check failed for post %s", getattr(post, "id", None))
