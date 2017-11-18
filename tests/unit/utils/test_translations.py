import subprocess
import os
from flask import current_app
from babel.support import Translations, NullTranslations
from flaskbb.utils.translations import FlaskBBDomain
import pytest


def _remove_compiled_translations():
    translations_folder = os.path.join(current_app.root_path, "translations")

    # walks through the translations folder and deletes all files
    # ending with .mo
    for root, dirs, files in os.walk(translations_folder):
        for name in files:
            if name.endswith(".mo"):
                os.unlink(os.path.join(root, name))


def _compile_translations():
    PLUGINS_FOLDER = os.path.join(current_app.root_path, "plugins")
    translations_folder = os.path.join(current_app.root_path, "translations")

    subprocess.call(["pybabel", "compile", "-d", translations_folder])

    for plugin in plugin_manager.all_plugins:
        plugin_folder = os.path.join(PLUGINS_FOLDER, plugin)
        translations_folder = os.path.join(plugin_folder, "translations")
        subprocess.call(["pybabel", "compile", "-d", translations_folder])


@pytest.mark.skip(reason="Plugin transition")
def test_flaskbbdomain_translations(default_settings):
    domain = FlaskBBDomain(current_app)

    with current_app.test_request_context():
        assert domain.get_translations_cache() == {}

        # just to be on the safe side that there are really no compiled
        # translations available
        _remove_compiled_translations()
        # no compiled translations are available
        assert isinstance(domain.get_translations(), NullTranslations)

        # lets compile them and test again
        _compile_translations()

        # now there should be translations :)
        assert isinstance(domain.get_translations(), Translations)
