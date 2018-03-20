from flask import current_app
from babel.support import Translations


def test_flaskbbdomain_translations(default_settings):
    domain = current_app.extensions.get("babel").domain

    with current_app.test_request_context():
        # no translations accessed and thus the cache is empty
        assert domain.get_translations_cache() == {}
        # load translations into cache
        assert isinstance(domain.get_translations(), Translations)
        assert len(domain.get_translations_cache()) == 1  # 'en'
