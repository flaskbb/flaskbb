# -*- coding: utf-8 -*-
"""
    flaskbb.utils.helpers
    ~~~~~~~~~~~~~~~~~~~~~

    A few helpers that are used by flaskbb

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import re
import time
import itertools
import operator
from datetime import datetime, timedelta
from pytz import UTC
from PIL import ImageFile

import requests
import unidecode
from flask import session, url_for, flash, redirect, request
from jinja2 import Markup
from babel.dates import format_timedelta as babel_format_timedelta
from flask_babelplus import lazy_gettext as _
from flask_themes2 import render_theme_template
from flask_login import current_user

from flaskbb._compat import range_method, text_type
from flaskbb.extensions import redis_store
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.markup import markdown
from flask_allows import Permission

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug.
    Taken from the Flask Snippets page.

   :param text: The text which should be slugified
   :param delim: Default "-". The delimeter for whitespace
    """
    text = unidecode.unidecode(text)
    result = []
    for word in _punct_re.split(text.lower()):
        if word:
            result.append(word)
    return text_type(delim.join(result))


def redirect_or_next(endpoint, **kwargs):
    """Redirects the user back to the page they were viewing or to a specified
    endpoint. Wraps Flasks :func:`Flask.redirect` function.

    :param endpoint: The fallback endpoint.
    """
    return redirect(
        request.args.get('next') or endpoint, **kwargs
    )


def render_template(template, **context):  # pragma: no cover
    """A helper function that uses the `render_theme_template` function
    without needing to edit all the views
    """
    if current_user.is_authenticated and current_user.theme:
        theme = current_user.theme
    else:
        theme = session.get('theme', flaskbb_config['DEFAULT_THEME'])
    return render_theme_template(theme, template, **context)


def do_topic_action(topics, user, action, reverse):
    """Executes a specific action for topics. Returns a list with the modified
    topic objects.

    :param topics: A iterable with ``Topic`` objects.
    :param user: The user object which wants to perform the action.
    :param action: One of the following actions: locked, important and delete.
    :param reverse: If the action should be done in a reversed way.
                    For example, to unlock a topic, ``reverse`` should be
                    set to ``True``.
    """
    from flaskbb.utils.requirements import (IsAtleastModeratorInForum,
                                            CanDeleteTopic)

    from flaskbb.user.models import User
    from flaskbb.forum.models import Post

    if not Permission(IsAtleastModeratorInForum(forum=topics[0].forum)):
        flash(_("You do not have the permissions to execute this "
                "action."), "danger")
        return False

    modified_topics = 0
    if action != "delete":

        for topic in topics:
            if getattr(topic, action) and not reverse:
                continue

            setattr(topic, action, not reverse)
            modified_topics += 1
            topic.save()
    elif action == "delete":
        for topic in topics:
            if not Permission(CanDeleteTopic):
                flash(_("You do not have the permissions to delete this "
                        "topic."), "danger")
                return False

            involved_users = User.query.filter(Post.topic_id == topic.id,
                                               User.id == Post.user_id).all()
            modified_topics += 1
            topic.delete(involved_users)

    return modified_topics


def get_categories_and_forums(query_result, user):
    """Returns a list with categories. Every category has a list for all
    their associated forums.

    The structure looks like this::
        [(<Category 1>,
          [(<Forum 1>, None),
           (<Forum 2>, <flaskbb.forum.models.ForumsRead at 0x38fdb50>)]),
         (<Category 2>,
          [(<Forum 3>, None),
          (<Forum 4>, None)])]

    and to unpack the values you can do this::
        In [110]: for category, forums in x:
           .....:     print category
           .....:     for forum, forumsread in forums:
           .....:         print "\t", forum, forumsread

   This will print something like this:
        <Category 1>
            <Forum 1> None
            <Forum 2> <flaskbb.forum.models.ForumsRead object at 0x38fdb50>
        <Category 2>
            <Forum 3> None
            <Forum 4> None

    :param query_result: A tuple (KeyedTuple) with all categories and forums

    :param user: The user object is needed because a signed out user does not
                 have the ForumsRead relation joined.
    """
    it = itertools.groupby(query_result, operator.itemgetter(0))

    forums = []

    if user.is_authenticated:
        for key, value in it:
            forums.append((key, [(item[1], item[2]) for item in value]))
    else:
        for key, value in it:
            forums.append((key, [(item[1], None) for item in value]))

    return forums


def get_forums(query_result, user):
    """Returns a tuple which contains the category and the forums as list.
    This is the counterpart for get_categories_and_forums and especially
    usefull when you just need the forums for one category.

    For example::
        (<Category 2>,
          [(<Forum 3>, None),
          (<Forum 4>, None)])

    :param query_result: A tuple (KeyedTuple) with all categories and forums

    :param user: The user object is needed because a signed out user does not
                 have the ForumsRead relation joined.
    """
    it = itertools.groupby(query_result, operator.itemgetter(0))

    if user.is_authenticated:
        for key, value in it:
            forums = key, [(item[1], item[2]) for item in value]
    else:
        for key, value in it:
            forums = key, [(item[1], None) for item in value]

    return forums


def forum_is_unread(forum, forumsread, user):
    """Checks if a forum is unread

    :param forum: The forum that should be checked if it is unread

    :param forumsread: The forumsread object for the forum

    :param user: The user who should be checked if he has read the forum
    """
    # If the user is not signed in, every forum is marked as read
    if not user.is_authenticated:
        return False

    read_cutoff = time_utcnow() - timedelta(
        days=flaskbb_config["TRACKER_LENGTH"])

    # disable tracker if TRACKER_LENGTH is set to 0
    if flaskbb_config["TRACKER_LENGTH"] == 0:
        return False

    # If there are no topics in the forum, mark it as read
    if forum and forum.topic_count == 0:
        return False

    # check if the last post is newer than the tracker length
    if forum.last_post_created < read_cutoff:
        return False

    # If the user hasn't visited a topic in the forum - therefore,
    # forumsread is None and we need to check if it is still unread
    if forum and not forumsread:
        return forum.last_post_created > read_cutoff

    try:
        # check if the forum has been cleared and if there is a new post
        # since it have been cleared
        if forum.last_post_created > forumsread.cleared:
            if forum.last_post_created < forumsread.last_read:
                return False
    except TypeError:
        pass

    # else just check if the user has read the last post
    return forum.last_post_created > forumsread.last_read


def topic_is_unread(topic, topicsread, user, forumsread=None):
    """Checks if a topic is unread.

    :param topic: The topic that should be checked if it is unread

    :param topicsread: The topicsread object for the topic

    :param user: The user who should be checked if he has read the last post
                 in the topic

    :param forumsread: The forumsread object in which the topic is. If you
                       also want to check if the user has marked the forum as
                       read, than you will also need to pass an forumsread
                       object.
    """
    if not user.is_authenticated:
        return False

    read_cutoff = time_utcnow() - timedelta(
        days=flaskbb_config["TRACKER_LENGTH"])

    # disable tracker if read_cutoff is set to 0
    if flaskbb_config["TRACKER_LENGTH"] == 0:
        return False

    # check read_cutoff
    if topic.last_post.date_created < read_cutoff:
        return False

    # topicsread is none if the user has marked the forum as read
    # or if he hasn't visited the topic yet
    if topicsread is None:
        # user has cleared the forum - check if there is a new post
        if forumsread and forumsread.cleared is not None:
            return forumsread.cleared < topic.last_post.date_created

        # user hasn't read the topic yet, or there is a new post since the user
        # has marked the forum as read
        return True

    # check if there is a new post since the user's last topic visit
    return topicsread.last_read < topic.last_post.date_created


def mark_online(user_id, guest=False):  # pragma: no cover
    """Marks a user as online

    :param user_id: The id from the user who should be marked as online

    :param guest: If set to True, it will add the user to the guest activity
                  instead of the user activity.

    Ref: http://flask.pocoo.org/snippets/71/
    """
    now = int(time.time())
    expires = now + (flaskbb_config['ONLINE_LAST_MINUTES'] * 60) + 10
    if guest:
        all_users_key = 'online-guests/%d' % (now // 60)
        user_key = 'guest-activity/%s' % user_id
    else:
        all_users_key = 'online-users/%d' % (now // 60)
        user_key = 'user-activity/%s' % user_id
    p = redis_store.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()


def get_online_users(guest=False):  # pragma: no cover
    """Returns all online users within a specified time range

    :param guest: If True, it will return the online guests
    """
    current = int(time.time()) // 60
    minutes = range_method(flaskbb_config['ONLINE_LAST_MINUTES'])
    if guest:
        return redis_store.sunion(['online-guests/%d' % (current - x)
                                   for x in minutes])
    return redis_store.sunion(['online-users/%d' % (current - x)
                               for x in minutes])


def crop_title(title, length=None, suffix="..."):
    """Crops the title to a specified length

    :param title: The title that should be cropped

    :param suffix: The suffix which should be appended at the
                   end of the title.
    """
    length = flaskbb_config['TITLE_LENGTH'] if length is None else length

    if len(title) <= length:
        return title

    return title[:length].rsplit(' ', 1)[0] + suffix


def render_markup(text):
    """Renders the given text as markdown

    :param text: The text that should be rendered as markdown
    """
    return Markup(markdown.render(text))


def is_online(user):
    """A simple check to see if the user was online within a specified
    time range

    :param user: The user who needs to be checked
    """
    return user.lastseen >= time_diff()


def time_utcnow():
    """Returns a timezone aware utc timestamp."""
    return datetime.now(UTC)


def time_diff():
    """Calculates the time difference between now and the ONLINE_LAST_MINUTES
    variable from the configuration.
    """
    now = time_utcnow()
    diff = now - timedelta(minutes=flaskbb_config['ONLINE_LAST_MINUTES'])
    return diff


def format_date(value, format='%Y-%m-%d'):
    """Returns a formatted time string

    :param value: The datetime object that should be formatted

    :param format: How the result should look like. A full list of available
                   directives is here: http://goo.gl/gNxMHE
    """
    return value.strftime(format)


def format_timedelta(delta, **kwargs):
    """Wrapper around babel's format_timedelta to make it user language
    aware.
    """
    locale = flaskbb_config.get("DEFAULT_LANGUAGE", "en")
    if current_user.is_authenticated and current_user.language is not None:
        locale = current_user.language

    return babel_format_timedelta(delta, locale=locale, **kwargs)


def time_since(time):  # pragma: no cover
    """Returns a string representing time since e.g.
    3 days ago, 5 hours ago.

    :param time: A datetime object
    """
    delta = time - time_utcnow()
    return format_timedelta(delta, add_direction=True)


def format_quote(username, content):
    """Returns a formatted quote depending on the markup language.

    :param username: The username of a user.
    :param content: The content of the quote
    """
    profile_url = url_for('user.profile', username=username)
    content = "\n> ".join(content.strip().split('\n'))
    quote = u"**[{username}]({profile_url}) wrote:**\n> {content}\n".\
            format(username=username, profile_url=profile_url, content=content)

    return quote


def get_image_info(url):
    """Returns the content-type, image size (kb), height and width of
    an image without fully downloading it.

    :param url: The URL of the image.
    """
    r = requests.get(url, stream=True)
    image_size = r.headers.get("content-length")
    image_size = float(image_size) / 1000  # in kilobyte
    image_max_size = 10000
    image_data = {
        "content_type": "",
        "size": image_size,
        "width": 0,
        "height": 0
    }

    # lets set a hard limit of 10MB
    if image_size > image_max_size:
        return image_data

    data = None
    parser = ImageFile.Parser()

    while True:
        data = r.raw.read(1024)
        if not data:
            break

        parser.feed(data)
        if parser.image:
            image_data["content_type"] = parser.image.format
            image_data["width"] = parser.image.size[0]
            image_data["height"] = parser.image.size[1]
            break

    return image_data


def check_image(url):
    """A little wrapper for the :func:`get_image_info` function.
    If the image doesn't match the ``flaskbb_config`` settings it will
    return a tuple with a the first value is the custom error message and
    the second value ``False`` for not passing the check.
    If the check is successful, it will return ``None`` for the error message
    and ``True`` for the passed check.

    :param url: The image url to be checked.
    """
    img_info = get_image_info(url)
    error = None

    if img_info["size"] > flaskbb_config["AVATAR_SIZE"]:
        error = "Image is too big! {}kb are allowed.".format(
            flaskbb_config["AVATAR_SIZE"]
        )
        return error, False

    if not img_info["content_type"] in flaskbb_config["AVATAR_TYPES"]:
        error = "Image type {} is not allowed. Allowed types are: {}".format(
            img_info["content_type"],
            ", ".join(flaskbb_config["AVATAR_TYPES"])
        )
        return error, False

    if img_info["width"] > flaskbb_config["AVATAR_WIDTH"]:
        error = "Image is too wide! {}px width is allowed.".format(
            flaskbb_config["AVATAR_WIDTH"]
        )
        return error, False

    if img_info["height"] > flaskbb_config["AVATAR_HEIGHT"]:
        error = "Image is too high! {}px height is allowed.".format(
            flaskbb_config["AVATAR_HEIGHT"]
        )
        return error, False

    return error, True
