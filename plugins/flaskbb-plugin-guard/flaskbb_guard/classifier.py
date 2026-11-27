"""Toxicity classifiers for FlaskBB-Guard.

This module has no FlaskBB imports on purpose: the classifiers only turn
text into a ToxicityResult, so they can be developed and tested on their own.
"""

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToxicityResult:
    """The outcome of scoring one piece of text."""

    score: float
    label: str
    categories: dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be between 0.0 and 1.0, got {self.score}")

    def is_toxic(self, threshold: float) -> bool:
        """True when the score reaches the threshold (inclusive)."""
        return self.score >= threshold


class ToxicityClassifier(ABC):
    """Interface every classifier must follow (Strategy pattern)."""

    name: str = "base"

    @abstractmethod
    def score(self, text: str) -> ToxicityResult:
        """Return a ToxicityResult for ``text``."""


# Each category has a weight: how strongly one match suggests toxicity.
CATEGORY_WEIGHTS = {
    "insult": 0.6,
    "threat": 0.9,
    "obscene": 0.5,
}

# A small, mild example list. Real deployments would use a curated list.
DEFAULT_TOXIC_WORDS = {
    "idiot": "insult",
    "stupid": "insult",
    "moron": "insult",
    "loser": "insult",
    "dumb": "insult",
    "shut up": "insult",
    "kill you": "threat",
    "hurt you": "threat",
    "damn": "obscene",
    "crap": "obscene",
}


class KeywordClassifier(ToxicityClassifier):
    """Baseline classifier that looks for known toxic words and phrases.

    It is fast and needs no model, so it is used in tests and as the
    baseline that the AI classifier is compared against.
    """

    name = "keyword"

    def __init__(self, toxic_words: dict[str, str] | None = None):
        self.toxic_words = dict(toxic_words or DEFAULT_TOXIC_WORDS)
        # \b = word boundary, so "dumb" does not match inside "dumbbell"
        self._patterns = {
            word: re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            for word in self.toxic_words
        }

    def score(self, text: str) -> ToxicityResult:
        start = time.perf_counter()

        matches: dict[str, int] = {}
        for word, pattern in self._patterns.items():
            found = len(pattern.findall(text or ""))
            if found:
                category = self.toxic_words[word]
                matches[category] = matches.get(category, 0) + found

        categories = {
            category: self._combine(CATEGORY_WEIGHTS.get(category, 0.5), count)
            for category, count in matches.items()
        }

        if categories:
            label = max(categories, key=categories.get)
            score = self._combine_scores(categories.values())
        else:
            label, score = "none", 0.0

        latency_ms = (time.perf_counter() - start) * 1000
        return ToxicityResult(round(score, 4), label, categories, latency_ms)

    @staticmethod
    def _combine(weight: float, count: int) -> float:
        """Each extra match makes toxicity more likely: 1 - (1 - w) ** n."""
        return round(1 - (1 - weight) ** count, 4)

    @staticmethod
    def _combine_scores(scores) -> float:
        remaining = 1.0
        for s in scores:
            remaining *= 1 - s
        return 1 - remaining