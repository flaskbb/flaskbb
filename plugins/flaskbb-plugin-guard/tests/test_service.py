import logging

import sqlalchemy as sa
from flaskbb.extensions import db
from flaskbb.forum.models import Post, Report

import flaskbb_guard
from flaskbb_guard.classifier import ToxicityClassifier, ToxicityResult
from flaskbb_guard.service import BOT_USERNAME, REPORT_PREFIX, ToxicityDetectionService


class FixedClassifier(ToxicityClassifier):
    """Test double: always returns the same score."""

    name = "fixed"

    def __init__(self, score, label="insult"):
        self.value, self.label = score, label

    def score(self, text):
        return ToxicityResult(self.value, self.label)


class BrokenClassifier(ToxicityClassifier):
    name = "broken"

    def score(self, text):
        raise RuntimeError("model failed to load")


def make_service(score, **settings):
    config = {"GUARD_AUTOMOD_ENABLED": True, "GUARD_AUTOMOD_THRESHOLD": 80,
              "GUARD_AUTOMOD_EXEMPT_STAFF": True}
    config.update(settings)
    return ToxicityDetectionService(FixedClassifier(score), config=config)


def reports_for(post):
    return db.session.execute(sa.select(Report).filter_by(post_id=post.id)).scalars().all()


def new_reply(topic, user, text="A normal reply"):
    return Post(content=text).save(user=user, topic=topic)


# ---------- decisions (FR3, threshold edge cases) ----------

def test_toxic_post_is_reported(topic, user):
    post = new_reply(topic, user)
    make_service(0.95).check_post(post)
    reports = reports_for(post)
    assert len(reports) == 1
    assert reports[0].reporter.username == BOT_USERNAME
    assert reports[0].reason.startswith(REPORT_PREFIX)


def test_safe_post_is_not_reported(topic, user):
    post = new_reply(topic, user)
    make_service(0.10).check_post(post)
    assert reports_for(post) == []


def test_score_equal_to_threshold_is_reported(topic, user):
    post = new_reply(topic, user)
    make_service(0.80).check_post(post)
    assert len(reports_for(post)) == 1


def test_score_just_below_threshold_is_not_reported(topic, user):
    post = new_reply(topic, user)
    make_service(0.79).check_post(post)
    assert reports_for(post) == []


def test_threshold_setting_is_used(topic, user):
    post = new_reply(topic, user)
    make_service(0.60, GUARD_AUTOMOD_THRESHOLD=50).check_post(post)
    assert len(reports_for(post)) == 1


# ---------- FR4: no duplicate reports ----------

def test_post_is_not_reported_twice(topic, user):
    post = new_reply(topic, user)
    service = make_service(0.95)
    service.check_post(post)
    service.check_post(post)
    assert len(reports_for(post)) == 1


# ---------- FR5: on/off setting ----------

def test_disabled_detection_does_nothing(topic, user):
    post = new_reply(topic, user)
    assert make_service(0.95, GUARD_AUTOMOD_ENABLED=False).check_post(post) is None
    assert reports_for(post) == []


# ---------- FR9: staff exemption ----------

def test_moderator_posts_are_skipped(topic, moderator_user):
    post = new_reply(topic, moderator_user)
    assert make_service(0.95).check_post(post) is None
    assert reports_for(post) == []


def test_moderator_posts_checked_when_exemption_is_off(topic, moderator_user):
    post = new_reply(topic, moderator_user)
    make_service(0.95, GUARD_AUTOMOD_EXEMPT_STAFF=False).check_post(post)
    assert len(reports_for(post)) == 1


# ---------- end to end through FlaskBB's hook ----------

def test_saving_a_toxic_post_creates_a_report_through_the_hook(topic, user, monkeypatch):
    monkeypatch.setattr(flaskbb_guard, "_service", make_service(0.95))
    post = new_reply(topic, user, "any text")
    assert len(reports_for(post)) == 1


def test_keyword_classifier_reports_a_rude_post_end_to_end(topic, user, monkeypatch):
    monkeypatch.setattr(flaskbb_guard, "_service", None)  # use the real default service
    post = new_reply(topic, user, "This is a stupid idea and you are an idiot.")
    assert len(reports_for(post)) == 1


# ---------- NFR2: fail-open ----------

def test_classifier_failure_never_blocks_posting(topic, user, monkeypatch, caplog):
    broken = ToxicityDetectionService(BrokenClassifier(), config={})
    monkeypatch.setattr(flaskbb_guard, "_service", broken)
    caplog.set_level(logging.ERROR, logger="flaskbb.guard")

    post = new_reply(topic, user, "hello")

    assert post.id is not None  # the post was saved
    assert reports_for(post) == []
    assert "toxicity check failed" in caplog.text


# ---------- FR8: every score is stored ----------

from flaskbb_guard.models import ToxicityScore  # noqa: E402


def scores_for(post):
    return db.session.execute(sa.select(ToxicityScore).filter_by(post_id=post.id)).scalars().all()


def test_safe_post_score_is_stored(topic, user, monkeypatch):
    monkeypatch.setattr(flaskbb_guard, "_service", make_service(0.10))
    post = new_reply(topic, user)
    [score] = scores_for(post)
    assert score.score == 0.10
    assert score.model_name == "fixed"
    assert score.latency_ms >= 0.0


def test_toxic_post_score_is_stored_with_its_label(topic, user, monkeypatch):
    monkeypatch.setattr(flaskbb_guard, "_service", make_service(0.95))
    post = new_reply(topic, user)
    [score] = scores_for(post)
    assert score.label == "insult"


def test_skipped_posts_store_no_score(topic, user, monkeypatch):
    monkeypatch.setattr(flaskbb_guard, "_service", make_service(0.95, GUARD_AUTOMOD_ENABLED=False))
    post = new_reply(topic, user)
    assert scores_for(post) == []


def test_migration_is_labelled_with_the_plugin_name():
    import importlib
    mod = importlib.import_module(
        "flaskbb_guard.migrations.202611271945_3f2a9c1d7b6e_add_toxicity_scores"
    )
    assert mod.branch_labels == ("guard",)
