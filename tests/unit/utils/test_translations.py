from flask import current_app
from flaskbb.utils.translations import FlaskBBDomain


def test_flaskbbdomain_translations():
    domain = FlaskBBDomain(current_app)

    assert domain.get_translations_cache() == {}

    # returns an translation object
    assert domain.get_translations() is not None

    assert len(domain.get_translations_cache()) > 0
