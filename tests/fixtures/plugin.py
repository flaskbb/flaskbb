import pytest
from flaskbb.plugins.manager import FlaskBBPluginManager
from flaskbb.plugins import spec


@pytest.fixture
def plugin_manager():
    pluggy = FlaskBBPluginManager("flaskbb")
    pluggy.add_hookspecs(spec)
    return pluggy
