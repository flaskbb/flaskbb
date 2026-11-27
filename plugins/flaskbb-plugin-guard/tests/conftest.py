import pytest
from tests.fixtures.app import *  # noqa: F403
from tests.fixtures.forum import *  # noqa: F403
from tests.fixtures.user import *  # noqa: F403


@pytest.fixture(scope="package")
def tested_plugins():
    """Tell FlaskBB's test app to load our plugin."""
    return ["guard"]