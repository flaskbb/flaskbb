import pytest

from flaskbb_guard.classifier import (
    KeywordClassifier,
    ToxicityClassifier,
    ToxicityResult,
)


# ---------- ToxicityResult ----------

def test_result_is_toxic_when_score_equals_threshold():
    assert ToxicityResult(score=0.8, label="insult").is_toxic(0.8)


def test_result_is_not_toxic_just_below_threshold():
    assert not ToxicityResult(score=0.79, label="insult").is_toxic(0.8)


@pytest.mark.parametrize("bad_score", [-0.1, 1.5])
def test_result_rejects_scores_outside_0_to_1(bad_score):
    with pytest.raises(ValueError):
        ToxicityResult(score=bad_score, label="insult")


# ---------- ToxicityClassifier (interface) ----------

def test_classifier_interface_cannot_be_used_directly():
    with pytest.raises(TypeError):
        ToxicityClassifier()


# ---------- KeywordClassifier ----------

@pytest.fixture
def clf():
    return KeywordClassifier()


def test_clean_text_scores_zero(clf):
    result = clf.score("Thanks for setting this up, really helpful!")
    assert result.score == 0.0
    assert result.label == "none"
    assert result.categories == {}


def test_single_insult_is_detected(clf):
    result = clf.score("You are an idiot.")
    assert result.label == "insult"
    assert result.score == pytest.approx(0.6)


def test_two_insults_give_a_higher_score(clf):
    result = clf.score("This is a stupid idea and you are an idiot.")
    assert result.score == pytest.approx(0.84)
    assert result.is_toxic(0.8)


def test_threat_is_detected_with_high_score(clf):
    result = clf.score("I will hurt you.")
    assert result.label == "threat"
    assert result.is_toxic(0.8)


def test_matching_ignores_upper_and_lower_case(clf):
    assert clf.score("IDIOT").score == clf.score("idiot").score


def test_words_inside_other_words_are_not_matched(clf):
    assert clf.score("I bought a new dumbbell for the gym").score == 0.0


def test_disagreement_is_not_toxic(clf):
    result = clf.score("I disagree with your point, but I see where you are coming from.")
    assert not result.is_toxic(0.8)


def test_empty_text_is_safe(clf):
    assert clf.score("").score == 0.0


def test_custom_word_list_can_be_used():
    clf = KeywordClassifier({"banana": "insult"})
    assert clf.score("you banana").label == "insult"


def test_latency_is_recorded(clf):
    assert clf.score("hello").latency_ms >= 0.0