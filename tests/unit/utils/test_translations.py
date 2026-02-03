from babel.support import Translations
from flask import current_app


def test_flaskbbdomain_translations(default_settings):
    domain = current_app.extensions.get("babel").domain

    with current_app.test_request_context():
        assert isinstance(domain.get_translations(), Translations)
        assert len(domain.get_translations_cache()) == 1  # 'en'
