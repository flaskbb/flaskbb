import os

import babel

from flask_babelex import Domain, get_locale
from flask_plugins import get_plugins_list

from flaskbb._compat import PY2


class FlaskBBDomain(Domain):
    def __init__(self, app):
        self.app = app
        super(FlaskBBDomain, self).__init__()

        self.plugins_folder = os.path.join(
            os.path.join(self.app.root_path, "plugins")
        )

        # FlaskBB's translations
        self.flaskbb_translations = os.path.join(
            self.app.root_path, "translations"
        )

        # Plugin translations
        with self.app.app_context():
            self.plugin_translations = [
                os.path.join(plugin.path, "translations")
                for plugin in get_plugins_list()
            ]

    def get_translations(self):
        """Returns the correct gettext translations that should be used for
        this request.  This will never fail and return a dummy translation
        object if used outside of the request or if a translation cannot be
        found.
        """
        locale = get_locale()
        cache = self.get_translations_cache()

        translations = cache.get(str(locale))
        if translations is None:
            # load flaskbb translations
            translations = babel.support.Translations.load(
                dirname=self.flaskbb_translations,
                locales=locale,
                domain="messages"
            )

            # If no compiled translations are found, return the
            # NullTranslations object.
            if not isinstance(translations, babel.support.Translations):
                return translations

            # Plugin translations are at the moment not supported under
            # Python 3. There is currently a bug in Babel where it is
            # not possible to merge two message catalogs.
            # https://github.com/mitsuhiko/babel/pull/92
            # So instead of adding/merging them, we are just skipping them
            # Better then no python3 support though..
            if not PY2:
                return translations

            # now load and add the plugin translations
            for plugin in self.plugin_translations:
                plugin_translation = babel.support.Translations.load(
                    dirname=plugin,
                    locales=locale,
                    domain="messages"
                )
                translations.add(plugin_translation)

            cache[str(locale)] = translations

        return translations
