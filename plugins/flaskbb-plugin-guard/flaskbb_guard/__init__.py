"""FlaskBB-Guard: AI-based toxicity detection for FlaskBB."""

import logging
import os
import sys
import threading

from flaskbb.settings import BoolSetting, IntSetting, SettingGroup, flaskbb_config
from pluggy import HookimplMarker

from .classifier import KeywordClassifier, TransformerClassifier, ai_available
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
            key="AUTOMOD_USE_AI",
            value=True,
            name="Use the AI model (toxic-bert)",
            description="Use the pre-trained AI model. If it is switched off or not installed, the keyword classifier is used.",
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
    """Create the service once and reuse it, so the AI model is loaded only once.

    The AI classifier is used when the setting is on and the AI libraries are
    installed; otherwise the keyword classifier is the fallback.
    """
    global _service
    use_ai = bool(flaskbb_config.get("GUARD_AUTOMOD_USE_AI", True)) and ai_available()
    wanted = TransformerClassifier.name if use_ai else KeywordClassifier.name

    rebuild = _service is None or (
        getattr(_service, "auto_built", False) and _service.classifier.name != wanted
    )
    if rebuild:
        classifier = TransformerClassifier() if use_ai else KeywordClassifier()
        _service = ToxicityDetectionService(classifier)
        _service.auto_built = True
        logger.info("FlaskBB-Guard: using the %s classifier", classifier.name)
    return _service


def warm_up(app) -> threading.Thread:
    """Load the classifier in the background so the first post is not slow."""

    def run():
        with app.app_context():
            try:
                service = get_service()
                service.classifier.score("warm up")
                logger.info("FlaskBB-Guard: %s classifier ready", service.classifier.name)
            except Exception:
                logger.exception("FlaskBB-Guard: warm-up failed")

    thread = threading.Thread(target=run, name="guard-warm-up", daemon=True)
    thread.start()
    return thread


@hookimpl
def flaskbb_additional_setup(app):
    """Preload the AI model when the web server starts (not in tests or other commands)."""
    starting_server = len(sys.argv) > 1 and sys.argv[1] == "run"
    if app.testing or not ai_available():
        return
    if starting_server or app.config.get("GUARD_PRELOAD_MODEL", False):
        warm_up(app)


@hookimpl
def flaskbb_load_migrations():
    """Tell FlaskBB where this plugin's database migrations are."""
    return os.path.join(os.path.dirname(__file__), "migrations")


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
