import logging

from flaskbb.extensions import pluggy
from flaskbb.forum.models import Post

import flaskbb_guard


def test_plugin_is_discovered_and_loaded(application):
    """FlaskBB finds the plugin through its 'flaskbb_plugins' entry point."""
    assert pluggy.get_plugin("guard") is flaskbb_guard


def test_plugin_registers_its_settings(application):
    """The settings group is returned to FlaskBB through the hook."""
    groups = pluggy.hook.flaskbb_load_setting_groups()
    assert flaskbb_guard.SETTINGS in groups


def test_settings_key_matches_plugin_name():
    """FlaskBB links settings to a plugin by this key (lesson learned)."""
    assert flaskbb_guard.SETTINGS.key == "guard"


def test_hook_checks_every_saved_post(topic, user, caplog):
    """Saving a post makes FlaskBB call our hook, which scores the post."""
    caplog.set_level(logging.INFO, logger="flaskbb.guard")

    reply = Post(content="Hello from the plugin test")
    reply.save(user=user, topic=topic)

    assert f"post {reply.id} scored" in caplog.text
