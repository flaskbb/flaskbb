import pytest
from flaskbb.plugins.manager import FlaskBBPluginManager


@pytest.fixture
def plugin_manager():
    return FlaskBBPluginManager("flaskbb")
