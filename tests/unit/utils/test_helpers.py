#-*- coding: utf-8 -*-
from flaskbb.utils.helpers import slugify


def test_slugify():
    """Test the slugify helper method."""

    assert slugify(u'Hello world') == u'hello-world'

    assert slugify(u'¿Cómo está?') == u'como-esta'
