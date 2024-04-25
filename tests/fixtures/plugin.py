import pytest

from flaskbb.plugins import spec
from flaskbb.plugins.manager import FlaskBBPluginManager


@pytest.fixture
def plugin_manager():
    pluggy = FlaskBBPluginManager("flaskbb")
    pluggy.add_hookspecs(spec)
    return pluggy
