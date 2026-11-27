"""ToxicityDetectionService: connects a classifier to FlaskBB.

It decides whether a post should be checked, scores it, and files a
toxicity report for moderators when the score reaches the threshold.
It never hides or deletes a post: a human moderator makes that decision.
"""

import logging
import secrets

import sqlalchemy as sa
from flaskbb.extensions import db
from flaskbb.forum.models import Post, Report
from flaskbb.settings import flaskbb_config
from flaskbb.user.models import GroupRole, User
from flaskbb.utils.populate import create_user

from .classifier import ToxicityClassifier, ToxicityResult

logger = logging.getLogger("flaskbb.guard")

BOT_USERNAME = "ToxicityBot"
BOT_EMAIL = "toxicity-bot@flaskbb-guard.invalid"
REPORT_PREFIX = "Toxicity Detection:"


class ToxicityDetectionService:
    def __init__(self, classifier: ToxicityClassifier, config=None):
        self.classifier = classifier
        # the settings source can be swapped in tests; FlaskBB's settings by default
        self.config = config if config is not None else flaskbb_config

    # ---- settings -------------------------------------------------------
    @property
    def enabled(self) -> bool:
        return bool(self.config.get("GUARD_AUTOMOD_ENABLED", True))

    @property
    def threshold(self) -> float:
        """The admin setting is a whole percentage (80 means 0.80)."""
        return int(self.config.get("GUARD_AUTOMOD_THRESHOLD", 80)) / 100

    @property
    def exempt_staff(self) -> bool:
        return bool(self.config.get("GUARD_AUTOMOD_EXEMPT_STAFF", True))

    # ---- main entry point ----------------------------------------------
    def check_post(self, post: Post) -> ToxicityResult | None:
        """Score ``post`` and report it if needed. Returns None when skipped."""
        if not self.enabled:
            return None
        if self.exempt_staff and self.is_exempt(post.user):
            return None

        result = self.classifier.score(post.content or "")
        logger.info(
            "FlaskBB-Guard: post %s scored %.2f (%s) in %.1f ms",
            post.id, result.score, result.label, result.latency_ms,
        )

        if result.is_toxic(self.threshold) and not self.has_open_report(post):
            self.create_report(post, result)
        return result

    # ---- helpers --------------------------------------------------------
    @staticmethod
    def is_exempt(user: User | None) -> bool:
        """Moderators, super moderators and administrators are not checked."""
        if user is None or user.primary_group is None:
            return False
        return user.primary_group.role.rank >= GroupRole.MODERATOR.rank

    def has_open_report(self, post: Post) -> bool:
        """True if this feature already reported the post and nobody closed it."""
        bot = self.get_bot_user(create=False)
        if bot is None:
            return False
        query = sa.select(Report.id).where(
            Report.post_id == post.id,
            Report.reporter_id == bot.id,
            Report.zapped.is_(None),
        )
        return db.session.execute(query).first() is not None

    def create_report(self, post: Post, result: ToxicityResult) -> Report:
        reason = f"{REPORT_PREFIX} {result.label} ({result.score:.0%}, {self.classifier.name} classifier)"
        report = Report(reason=reason)
        report.save(post=post, user=self.get_bot_user())
        logger.info("FlaskBB-Guard: reported post %s (%s)", post.id, reason)
        return report

    @staticmethod
    def get_bot_user(create: bool = True) -> User | None:
        """The system account shown as the reporter of toxicity reports."""
        bot = db.session.execute(
            sa.select(User).filter_by(username=BOT_USERNAME)
        ).scalar_one_or_none()
        if bot is None and create:
            # random password: nobody can log in as the bot
            bot = create_user(BOT_USERNAME, secrets.token_urlsafe(32), BOT_EMAIL, "member")
        return bot
