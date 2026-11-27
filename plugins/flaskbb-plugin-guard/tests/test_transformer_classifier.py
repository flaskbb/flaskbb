import os

import pytest

from flaskbb_guard.classifier import TransformerClassifier, ai_available


def fake_factory(output, calls):
    """Builds a fake Hugging Face pipeline that returns ``output``."""

    def factory(task, model, top_k):
        calls.append((task, model, top_k))

        def pipe(text, truncation):
            return output

        return pipe

    return factory


TOXIC_OUTPUT = [
    {"label": "toxic", "score": 0.97},
    {"label": "insult", "score": 0.91},
    {"label": "obscene", "score": 0.12},
    {"label": "threat", "score": 0.01},
]


def test_highest_category_becomes_score_and_label():
    clf = TransformerClassifier(pipeline_factory=fake_factory(TOXIC_OUTPUT, []))
    result = clf.score("some rude text")
    assert result.score == pytest.approx(0.97)
    assert result.label == "toxic"
    assert result.categories["insult"] == pytest.approx(0.91)


def test_nested_pipeline_output_is_handled():
    clf = TransformerClassifier(pipeline_factory=fake_factory([TOXIC_OUTPUT], []))
    assert clf.score("some rude text").label == "toxic"


def test_model_is_loaded_only_once():
    calls = []
    clf = TransformerClassifier(pipeline_factory=fake_factory(TOXIC_OUTPUT, calls))
    clf.score("first post")
    clf.score("second post")
    assert len(calls) == 1
    assert calls[0] == ("text-classification", "unitary/toxic-bert", None)


def test_empty_text_is_safe_and_does_not_load_the_model():
    calls = []
    clf = TransformerClassifier(pipeline_factory=fake_factory(TOXIC_OUTPUT, calls))
    assert clf.score("   ").score == 0.0
    assert calls == []


def test_label_is_none_when_every_category_is_low():
    safe_output = [{"label": "toxic", "score": 0.0006}, {"label": "insult", "score": 0.0002}]
    result = TransformerClassifier(pipeline_factory=fake_factory(safe_output, [])).score("thanks!")
    assert result.label == "none"
    assert result.score == pytest.approx(0.0006)


def test_latency_is_recorded():
    clf = TransformerClassifier(pipeline_factory=fake_factory(TOXIC_OUTPUT, []))
    assert clf.score("text").latency_ms >= 0.0


# ---------- real model (slow: downloads ~440 MB the first time) ----------

@pytest.mark.real_model
@pytest.mark.skipif(
    not (ai_available() and os.environ.get("RUN_AI_TESTS") == "1"),
    reason="set RUN_AI_TESTS=1 and install the AI libraries to run",
)
@pytest.mark.parametrize(
    "text, toxic",
    [
        ("Thanks for setting this up, really helpful!", False),
        ("I disagree with your point, but I see where you are coming from.", False),
        ("Can someone help me reset my password?", False),
        ("This is a stupid idea and you are an idiot.", True),
        ("Shut up, nobody cares what you think.", True),
    ],
)
def test_real_model_on_forum_examples(text, toxic):
    result = TransformerClassifier().score(text)
    assert result.is_toxic(0.8) is toxic, f"{text!r} scored {result.score:.2f} ({result.label})"
