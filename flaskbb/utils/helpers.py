# -*- coding: utf-8 -*-
"""
    flaskbb.utils.helpers
    ~~~~~~~~~~~~~~~~~~~~

    A few helpers that are used by flaskbb

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import re
import time
import itertools
import operator
from unicodedata import normalize
from datetime import datetime, timedelta

from flask import current_app, session
from flask.ext.themes2 import render_theme_template
from flask.ext.login import current_user

from postmarkup import render_bbcode

from flaskbb.extensions import redis
from flaskbb.utils.settings import flaskbb_config

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug.
    Taken from the Flask Snippets page.

   :param text: The text which should be slugified
   :param delim: Default "-". The delimeter for whitespace
    """
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))


def render_template(template, **context):
    """A helper function that uses the `render_theme_template` function
    without needing to edit all the views
    """
    if current_user.is_authenticated() and current_user.theme:
        theme = current_user.theme
    else:
        theme = session.get('theme', flaskbb_config['DEFAULT_THEME'])
    return render_theme_template(theme, template, **context)


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

   This will print something this:
        <Category 1>
            <Forum 1> None
            <Forum 2> <flaskbb.forum.models.ForumsRead object at 0x38fdb50>
        <Category 2>
            <Forum 3> None
            <Forum 4> None

    :param result: A tuple (KeyedTuple) with all categories and forums

    :param user: The user object is needed because a signed out user does not
                 have the ForumsRead relation joined.
    """
    it = itertools.groupby(query_result, operator.itemgetter(0))

    forums = []

    if user.is_authenticated():
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

    :param result: A tuple (KeyedTuple) with all categories and forums

    :param user: The user object is needed because a signed out user does not
                 have the ForumsRead relation joined.
    """
    it = itertools.groupby(query_result, operator.itemgetter(0))

    if user.is_authenticated():
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
    if not user.is_authenticated():
        return False

    read_cutoff = datetime.utcnow() - timedelta(
        days=flaskbb_config["TRACKER_LENGTH"])

    # If there are no topics in the forum, mark it as read
    if forum and forum.topic_count == 0:
        return False

    # If the user hasn't visited a topic in the forum - therefore,
    # forumsread is None and we need to check if it is still unread
    if forum and not forumsread:
        return forum.last_post.date_created > read_cutoff

    # the user has visited a topic in this forum, check if there is a new post
    return forumsread.last_read < forum.last_post.date_created


def topic_is_unread(topic, topicsread, user, forumsread=None):
    """Checks if a topic is unread

    :param topic: The topic that should be checked if it is unread

    :param topicsread: The topicsread object for the topic

    :param user: The user who should be checked if he has read the last post
                 in the topic

    :param forumsread: The forumsread object in which the topic is. If you
                       also want to check if the user has marked the forum as
                       read, than you will also need to pass an forumsread
                       object.
    """
    if not user.is_authenticated():
        return False

    read_cutoff = datetime.utcnow() - timedelta(
        days=flaskbb_config["TRACKER_LENGTH"])

    # topicsread is none if the user has marked the forum as read
    # or if he hasn't visited yet
    if topic and not topicsread and topic.last_post.date_created > read_cutoff:

        # user has cleared the forum sometime ago - check if there is a new post
        if forumsread and forumsread.cleared is not None:
            return forumsread.cleared < topic.last_post.date_created

        # user hasn't read the topic yet, or it has been cleared
        return True

    return topicsread.last_read < topic.last_post.date_created


def mark_online(user_id, guest=False):
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
    p = redis.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()


def get_last_user_activity(user_id, guest=False):
    """Returns the last active time from a given user_id

    :param user_id: The user id for whom you want to know the latest activity

    :param guest: If the user is a guest (not signed in)
    """
    if guest:
        last_active = redis.get('guest-activity/%s' % user_id)
    else:
        last_active = redis.get('user-activity/%s' % user_id)

    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))


def get_online_users(guest=False):
    """Returns all online users within a specified time range

    :param guest: If True, it will return the online guests
    """
    current = int(time.time()) // 60
    minutes = xrange(flaskbb_config['ONLINE_LAST_MINUTES'])
    if guest:
        return redis.sunion(['online-guests/%d' % (current - x)
                             for x in minutes])
    return redis.sunion(['online-users/%d' % (current - x)
                         for x in minutes])


def crop_title(title):
    """Crops the title to a specified length

    :param title: The title that should be cropped
    """
    length = flaskbb_config['TITLE_LENGTH']
    if len(title) > length:
        return title[:length] + "..."
    return title


def render_markup(text):
    """Renders the given text as bbcode

    :param text: The text that should be rendered as bbcode
    """
    return render_bbcode(text)


def is_online(user):
    """A simple check to see if the user was online within a specified
    time range

    :param user: The user who needs to be checked
    """
    return user.lastseen >= time_diff()


def time_diff():
    """Calculates the time difference between now and the ONLINE_LAST_MINUTES
    variable from the configuration.
    """
    now = datetime.utcnow()
    diff = now - timedelta(minutes=flaskbb_config['ONLINE_LAST_MINUTES'])
    return diff


def format_date(value, format='%Y-%m-%d'):
    """Returns a formatted time string

    :param value: The datetime object that should be formatted

    :param format: How the result should look like. A full list of available
                   directives is here: http://goo.gl/gNxMHE
    """
    return value.strftime(format)


def time_since(value):
    """Just a interface for `time_delta_format`"""
    return time_delta_format(value)


def time_delta_format(dt, default=None):
    """Returns a string representing time since e.g. 3 days ago, 5 hours ago.
    ref: https://bitbucket.org/danjac/newsmeme/src/a281babb9ca3/newsmeme/
    note: when Babel1.0 is released, use format_timedelta/timedeltaformat
          instead
    """

    if default is None:
        default = 'just now'

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, 'year', 'years'),
        (diff.days / 30, 'month', 'months'),
        (diff.days / 7, 'week', 'weeks'),
        (diff.days, 'day', 'days'),
        (diff.seconds / 3600, 'hour', 'hours'),
        (diff.seconds / 60, 'minute', 'minutes'),
        (diff.seconds, 'second', 'seconds'),
    )

    for period, singular, plural in periods:

        if not period:
            continue

        if period == 1:
            return u'%d %s ago' % (period, singular)
        else:
            return u'%d %s ago' % (period, plural)

    return default
