#-*- coding: utf-8 -*-
from flask_login import login_user
from flaskbb.utils.helpers import slugify, forum_is_unread


def test_slugify():
    """Test the slugify helper method."""
    assert slugify(u'Hello world') == u'hello-world'

    assert slugify(u'¿Cómo está?') == u'como-esta'


def test_forum_is_unread(guest, user, forum, topic, forumsread):
    """Test the forum is unread function for a a not logged in user."""
    assert forum_is_unread(None, None, guest) == False

    assert forum_is_unread(forum, None, user) == True

    assert forum_is_unread(forum, forumsread, user) == True

    topic.delete()

    assert forum_is_unread(forum, None, user) == False
