import pytest
from tests.fixtures.app import *  # noqa: F403
from tests.fixtures.forum import *  # noqa: F403
from tests.fixtures.user import *  # noqa: F403

import flaskbb_guard


def pytest_configure(config):
    # FlaskBB runs pytest with --strict-markers, so custom markers must be registered
    config.addinivalue_line("markers", "real_model: downloads and runs the real AI model (slow)")


@pytest.fixture(scope="package")
def tested_plugins():
    """Tell FlaskBB's test app to load our plugin."""
    return ["guard"]


@pytest.fixture(autouse=True)
def no_real_ai_model(request, monkeypatch):
    """Normal tests use the keyword classifier, so they never download the AI model."""
    if "real_model" in request.keywords:
        return
    monkeypatch.setattr(flaskbb_guard, "ai_available", lambda: False)
    monkeypatch.setattr(flaskbb_guard, "_service", None)
