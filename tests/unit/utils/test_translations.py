from babel.support import Translations
from flask import current_app
from flaskbb.utils.translations import translations_are_compiled


def test_flaskbbdomain_translations(default_settings):
    domain = current_app.extensions.get("babel").domain

    with current_app.test_request_context():
        assert isinstance(domain.get_translations(), Translations)
        assert len(domain.get_translations_cache()) == 1  # 'en'


def test_translations_are_compiled(application, tmp_path, monkeypatch):
    monkeypatch.setattr(application, "root_path", str(tmp_path))
    for locale in ("de", "fr"):
        messages = tmp_path / "translations" / locale / "LC_MESSAGES"
        messages.mkdir(parents=True)
        (messages / "messages.po").touch()
    (tmp_path / "translations" / "de" / "LC_MESSAGES" / "messages.mo").touch()

    assert not translations_are_compiled()

    (tmp_path / "translations" / "fr" / "LC_MESSAGES" / "messages.mo").touch()
    assert translations_are_compiled()
