# -*- coding: utf-8 -*-
import datetime as dt

from flaskbb.forum.models import Forum
from flaskbb.utils.helpers import (
    check_image, crop_title, format_quote, forum_is_unread, get_image_info,
    is_online, slugify, time_utcnow, topic_is_unread)
from flaskbb.utils.settings import flaskbb_config


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

    # lets mark the forum as read
    # but before we have to add an read entry in forumsread and topicsread
    topic.update_read(user, topic.forum, forumsread)

    time_read = dt.datetime.utcnow() - dt.timedelta(hours=1)
    forumsread.cleared = time_read  # lets cheat here a bit :P
    forumsread.last_read = dt.datetime.utcnow()
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
    forum = Forum.query.filter_by(id=forum.id).first()
    flaskbb_config["TRACKER_LENGTH"] = 1  # activate the tracker again
    assert forum.topic_count == 0
    assert not forum_is_unread(forum, None, user)


def test_topic_is_unread(guest, user, forum, topic, topicsread, forumsread):
    # test guest
    assert not topic_is_unread(None, None, guest)

    # compare topicsread.last_read with topic.last_post.date_created
    assert topic_is_unread(topic, topicsread, user, forumsread)

    # TopicsRead is none and the forum has never been marked as read
    assert topic_is_unread(
        topic, topicsread=None, user=user, forumsread=forumsread
    )

    # lets mark the forum as read
    forumsread.cleared = time_utcnow()
    forumsread.last_read = time_utcnow()
    forumsread.save()
    assert not topic_is_unread(
        topic, topicsread=None, user=user, forumsread=forumsread
    )

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
    expected_markdown = "**[test_normal](http://localhost:5000/user/test_normal) wrote:**\n> Test Content Normal\n"  # noqa
    actual = format_quote(topic.first_post.username, topic.first_post.content)
    assert actual == expected_markdown


def test_get_image_info():
    # some random jpg/gif/png images from my imgur account
    jpg = "http://i.imgur.com/NgVIeRG.jpg"
    gif = "http://i.imgur.com/l3Vmp4m.gif"
    png = "http://i.imgur.com/JXzKxNs.png"

    # Issue #207 Image - This works now
    # issue_img = "http://b.reich.io/gtlbjc.jpg"
    # issue_img = get_image_info(issue_img)
    # assert issue_img["content_type"] == "JPEG"

    jpg_img = get_image_info(jpg)
    assert jpg_img["content_type"] == "JPEG"
    assert jpg_img["height"] == 1024
    assert jpg_img["width"] == 1280
    assert jpg_img["size"] == 209.06

    gif_img = get_image_info(gif)
    assert gif_img["content_type"] == "GIF"
    assert gif_img["height"] == 168
    assert gif_img["width"] == 400
    assert gif_img["size"] == 576.138

    png_img = get_image_info(png)
    assert png_img["content_type"] == "PNG"
    assert png_img["height"] == 1080
    assert png_img["width"] == 1920
    assert png_img["size"] == 269.409


def test_check_image(default_settings):
    # test200_100.png
    img_width = "http://i.imgur.com/4dAWAZI.png"
    # test100_200.png
    img_height = "http://i.imgur.com/I7GwF3D.png"
    # test100_100.png
    img_ok = "http://i.imgur.com/CYV6NzT.png"
    # random too big image
    img_size = "http://i.imgur.com/l3Vmp4m.gif"
    # random image wrong type
    img_type = "https://flaskbb.org/static/imgs/flask.svg"

    data = check_image(img_width)
    assert "wide" in data[0]
    assert not data[1]

    data = check_image(img_height)
    assert "high" in data[0]
    assert not data[1]

    data = check_image(img_type)
    assert "type" in data[0]
    assert not data[1]

    data = check_image(img_ok)
    assert data[0] is None
    assert data[1]

    flaskbb_config["AVATAR_WIDTH"] = 1000
    flaskbb_config["AVATAR_HEIGHT"] = 1000
    data = check_image(img_size)
    assert "big" in data[0]
    assert not data[1]
