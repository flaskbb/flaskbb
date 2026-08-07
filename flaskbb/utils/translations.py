"""
flaskbb.utils.translations
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the translation Domain used by FlaskBB.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import os
import subprocess
from typing import override

import babel
import babel.support
from flask import current_app, Flask
from flask_babelplus import Domain, get_locale
from flask_babelplus.utils import get_state

from flaskbb.extensions import pluggy

logger = logging.getLogger(__name__)


class FlaskBBDomain(Domain):
    def __init__(self, app: Flask):
        self.app = app
        super().__init__()

        # Plugin translations
        with self.app.app_context():
            self.plugin_translations = pluggy.hook.flaskbb_load_translations()

    @override
    def get_translations(self):
        """Returns the correct gettext translations that should be used for
        this request.  This will never fail and return a dummy translation
        object if used outside of the request or if a translation cannot be
        found.
        """
        state = get_state(silent=True)

        if state is None:
            return babel.support.NullTranslations()

        locale = get_locale()
        cache = self.get_translations_cache()
        translations = cache.get(str(locale))

        # load them into the cache
        if translations is None:
            dirname = self.get_translations_path(state.app)
            translations = babel.support.Translations.load(dirname, locale, domain=self.domain)
            # now load and add the plugin translations - only a real
            # Translations catalog can merge others into itself
            if isinstance(translations, babel.support.Translations):
                for plugin in self.plugin_translations:
                    logger.debug(f"Loading plugin translation from: {plugin}")
                    plugin_translation = babel.support.Translations.load(
                        dirname=plugin, locales=locale, domain="messages"
                    )

                    if isinstance(plugin_translation, babel.support.Translations):
                        translations.add(plugin_translation)

            self.cache[str(locale)] = translations

        return translations


def update_translations(include_plugins: bool = False):
    """Updates all translations.

    :param include_plugins: If set to `True` it will also update the
                            translations for all plugins.
    """
    translations_folder = os.path.join(current_app.root_path, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(
        [
            "pybabel",
            "extract",
            "-F",
            "babel.cfg",
            "-k",
            "lazy_gettext",
            "-o",
            source_file,
            ".",
        ]
    )
    subprocess.call(["pybabel", "update", "-i", source_file, "-d", translations_folder])

    if include_plugins:
        for plugin in pluggy.list_name():
            update_plugin_translations(plugin)


def add_translations(translation: str):
    """Adds a new language to the translations.

    :param translation: The short name of the translation
                        like ``en`` or ``de_AT``.
    """
    translations_folder = os.path.join(current_app.root_path, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(
        [
            "pybabel",
            "extract",
            "-F",
            "babel.cfg",
            "-k",
            "lazy_gettext",
            "-o",
            source_file,
            ".",
        ]
    )
    subprocess.call(
        [
            "pybabel",
            "init",
            "-i",
            source_file,
            "-d",
            translations_folder,
            "-l",
            translation,
        ]
    )


def compile_translations(include_plugins: bool = False):
    """Compiles all translations.

    :param include_plugins: If set to `True` it will also compile the
                            translations for all plugins.
    """
    translations_folder = os.path.join(current_app.root_path, "translations")
    subprocess.call(["pybabel", "compile", "-d", translations_folder])

    if include_plugins:
        for plugin in pluggy.list_name():
            compile_plugin_translations(plugin)


def add_plugin_translations(plugin: str, translation: str):
    """Adds a new language to the plugin translations.

    :param plugin: The plugins identifier.
    :param translation: The short name of the translation
                        like ``en`` or ``de_AT``.
    """
    translations_folder = os.path.join(pluggy.get_plugin_path(plugin), "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(
        [
            "pybabel",
            "extract",
            "-F",
            "babel.cfg",
            "-k",
            "lazy_gettext",
            "-o",
            source_file,
            pluggy.get_plugin_path(plugin),
        ]
    )
    subprocess.call(
        [
            "pybabel",
            "init",
            "-i",
            source_file,
            "-d",
            translations_folder,
            "-l",
            translation,
        ]
    )


def update_plugin_translations(plugin: str):
    """Updates the plugin translations.
    Returns ``False`` if no translations for this plugin exists.

    :param plugin: The plugins identifier
    """
    translations_folder = os.path.join(pluggy.get_plugin_path(plugin), "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    if not os.path.exists(source_file):
        return False

    subprocess.call(
        [
            "pybabel",
            "extract",
            "-F",
            "babel.cfg",
            "-k",
            "lazy_gettext",
            "-o",
            source_file,
            pluggy.get_plugin_path(plugin),
        ]
    )
    subprocess.call(["pybabel", "update", "-i", source_file, "-d", translations_folder])


def compile_plugin_translations(plugin: str):
    """Compile the plugin translations.
    Returns ``False`` if no translations for this plugin exists.

    :param plugin: The plugins identifier
    """
    translations_folder = os.path.join(pluggy.get_plugin_path(plugin), "translations")

    if not os.path.exists(translations_folder):
        return False

    subprocess.call(["pybabel", "compile", "-d", translations_folder])
