import datetime as dt

from flaskbb.forum.models import Forum
from flaskbb.utils.helpers import (
    crop_title,
    format_quote,
    forum_is_unread,
    is_online,
    slugify,
    time_utcnow,
    topic_is_unread,
)
from flaskbb.utils.settings import flaskbb_config


def test_slugify():
    """Test the slugify helper method."""
    assert slugify("Hello world") == "hello-world"

    assert slugify("¿Cómo está?") == "como-esta"


def test_forum_is_unread(guest, user, forum, topic, forumsread):
    """Test the forum is unread function."""

    # for a guest
    assert not forum_is_unread(None, None, guest)

    # for a logged in user without a forumsread
    assert forum_is_unread(forum, None, user)

    # same, just with forumsread
    assert forum_is_unread(forum, forumsread, user)

    # lets mark the forum as read
    # but before we have to add an read entry in forumsread and topicsread
    topic.update_read(user, topic.forum, forumsread)

    time_read = dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)
    forumsread.cleared = time_read  # lets cheat here a bit :P
    forumsread.last_read = dt.datetime.now(dt.UTC)
    forumsread.save()
    assert not forum_is_unread(forum, forumsread, user)

    # read tracker is disabled
    flaskbb_config["TRACKER_LENGTH"] = 0
    assert not forum_is_unread(forum, forumsread, user)

    # there haven't been a post since TRACKER_LENGTH and thus the forum is read
    flaskbb_config["TRACKER_LENGTH"] = 1
    # this is cheating; don't do this.
    forum.last_post_created = forum.last_post_created - dt.timedelta(hours=48)
    forum.save()
    assert not forum_is_unread(forum, forumsread, user)

    # no topics in this forum
    topic.delete()
    forum = Forum.get_by(id=forum.id)
    flaskbb_config["TRACKER_LENGTH"] = 1  # activate the tracker again
    assert forum.topic_count == 0
    assert not forum_is_unread(forum, None, user)


def test_topic_is_unread(guest, user, forum, topic, topicsread, forumsread):
    # test guest
    assert not topic_is_unread(None, None, guest)

    # compare topicsread.last_read with topic.last_post.date_created
    assert topic_is_unread(topic, topicsread, user, forumsread)

    # TopicsRead is none and the forum has never been marked as read
    assert topic_is_unread(topic, topicsread=None, user=user, forumsread=forumsread)

    # lets mark the forum as read
    forumsread.cleared = time_utcnow()
    forumsread.last_read = time_utcnow()
    forumsread.save()
    assert not topic_is_unread(topic, topicsread=None, user=user, forumsread=forumsread)

    # disabled tracker
    flaskbb_config["TRACKER_LENGTH"] = 0
    assert not topic_is_unread(topic, None, user, None)

    # post is older than tracker length
    time_posted = time_utcnow() - dt.timedelta(days=2)
    flaskbb_config["TRACKER_LENGTH"] = 1
    topic.last_post.date_created = time_posted
    topic.last_updated = time_posted
    topic.save()
    assert not topic_is_unread(topic, None, user, None)


def test_crop_title(default_settings):
    short_title = "Short title"
    long_title = "This is just a test title which is too long."

    assert crop_title(short_title) == short_title
    assert crop_title(long_title) == "This is just a..."


def test_is_online(default_settings, user):
    assert is_online(user)


def test_format_quote(topic):
    expected_markdown = (
        "**[test_normal](http://localhost:5000/user/test_normal) wrote:**\n> Test Content Normal\n"  # noqa
    )
    actual = format_quote(topic.first_post.username, topic.first_post.content)
    assert actual == expected_markdown
