import os

import babel
from flask_babelex import Domain, get_locale
from flask_plugins import get_plugins_list


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
            self.plugin_translations = [os.path.join(plugin.path, "translations")
                                        for plugin in get_plugins_list()]

    def get_translations_cache(self):
        return self.cache

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
