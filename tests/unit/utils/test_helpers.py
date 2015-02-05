#-*- coding: utf-8 -*-
import datetime
from flaskbb.utils.helpers import slugify, forum_is_unread
from flaskbb.utils.settings import flaskbb_config
from flaskbb.forum.models import Forum


def test_slugify():
    """Test the slugify helper method."""
    assert slugify(u'Hello world') == u'hello-world'

    assert slugify(u'¿Cómo está?') == u'como-esta'


def test_forum_is_unread(guest, user, forum, topic, forumsread):
    """Test the forum is unread function."""

    # for a guest
    assert not forum_is_unread(None, None, guest)

    # for a logged in user without a forumsread
    assert forum_is_unread(forum, None, user)

    # same, just with forumsread
    assert forum_is_unread(forum, forumsread, user)

    # lets clear the forumsread relation
    # but before we have to add an read entry in forumsread and topicsread
    topic.update_read(user, topic.forum, forumsread)

    time_read = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    forumsread.cleared = time_read  # lets cheat here a bit :P
    forumsread.last_read = datetime.datetime.utcnow()
    forumsread.save()
    assert not forum_is_unread(forum, forumsread, user)

    # read tracker is disabled
    flaskbb_config["TRACKER_LENGTH"] = 0
    assert not forum_is_unread(forum, forumsread, user)

    # no topics in this forum
    topic.delete()
    forum = Forum.query.filter_by(id=forum.id).first()
    flaskbb_config["TRACKER_LENGTH"] = 1  # activate the tracker again
    assert forum.topic_count == 0
    assert not forum_is_unread(forum, None, user)
