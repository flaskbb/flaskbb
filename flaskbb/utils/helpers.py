# -*- coding: utf-8 -*-
"""
    flaskbb.utils.helpers
    ~~~~~~~~~~~~~~~~~~~~

    A few helpers that are used by flaskbb

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import time
from datetime import datetime, timedelta

from flask import current_app
from postmarkup import render_bbcode

from flaskbb.extensions import redis


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
        days=current_app.config["TRACKER_LENGTH"])

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

    :param user: The user who should be checked if he has read the topic

    :param forumsread: The forumsread object in which the topic is. You do
                       not have to pass this - only if you want to include the
                       cleared attribute from the ForumsRead object.
                       This will also check if the forum is marked as clear.
    """
    if not user.is_authenticated():
        return False

    read_cutoff = datetime.utcnow() - timedelta(
        days=current_app.config["TRACKER_LENGTH"])

    # topicsread is none if the user has marked the forum as read
    # or if he hasn't visited yet
    if topic and not topicsread and topic.last_post.date_created > read_cutoff:

        # user has cleared the forum sometime ago - check if there is a new post
        if forumsread and forumsread.cleared > topic.last_post.date_created:
            return False

        # user hasn't read the topic yet, or it has been cleared
        return True

    current_app.logger.debug("User has read it. check if there is a new post")
    return topicsread.last_read < topic.last_post.date_created


def mark_online(user_id, guest=False):
    """
    Source: http://flask.pocoo.org/snippets/71/
    """
    now = int(time.time())
    expires = now + (current_app.config['ONLINE_LAST_MINUTES'] * 60) + 10
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
    """
    Returns the last active time from a given `user_id`.
    """
    if guest:
        last_active = redis.get('guest-activity/%s' % user_id)
    else:
        last_active = redis.get('user-activity/%s' % user_id)

    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))


def get_online_users(guest=False):
    """
    Returns all online users within a specified time range
    """
    current = int(time.time()) // 60
    minutes = xrange(current_app.config['ONLINE_LAST_MINUTES'])
    if guest:
        return redis.sunion(['online-guests/%d' % (current - x)
                             for x in minutes])
    return redis.sunion(['online-users/%d' % (current - x)
                         for x in minutes])


def check_perm(user, perm, forum, post_user_id=None):
    """
    Checks if the `user` has a specified `perm` in the `forum`
    If post_user_id is provided, it will also check if the user
    has created the post
    """
    if can_moderate(user, forum):
        return True
    if post_user_id and user.is_authenticated():
        return user.permissions[perm] and user.id == post_user_id
    return user.permissions[perm]


def can_moderate(user, forum):
    """
    Checks if a user can moderate a forum
    He needs to be super moderator or a moderator of the
    specified `forum`
    """
    if user.permissions['mod'] and user.id in forum.moderators:
        return True
    return user.permissions['super_mod'] or user.permissions['admin']


def can_edit_post(user, post_user_id, forum):
    """
    Check if the post can be edited by the user
    """
    return check_perm(user=user, perm='editpost', forum=forum,
                      post_user_id=post_user_id)


def can_delete_post(user, post_user_id, forum):
    """
    Check if the post can be deleted by the user
    """
    return check_perm(user=user, perm='deletepost', forum=forum,
                      post_user_id=post_user_id)


def can_delete_topic(user, post_user_id, forum):
    """
    Check if the topic can be deleted by the user
    """
    return check_perm(user=user, perm='deletetopic', forum=forum,
                      post_user_id=post_user_id)


def can_lock_topic(user, forum):
    """
    Check if the user is allowed to lock a topic in the forum
    """
    return check_perm(user=user, perm='locktopic', forum=forum)


def can_move_topic(user, forum):
    """
    Check if the user is allowed to lock a topic in the forum
    """
    return check_perm(user=user, perm='movetopic', forum=forum)


def can_post_reply(user, forum):
    """
    Check if the user is allowed to post in the forum
    """
    return check_perm(user=user, perm='postreply', forum=forum)


def can_post_topic(user, forum):
    """
    Check if the user is allowed to create a new topic in the forum
    """
    return check_perm(user=user, perm='posttopic', forum=forum)


def crop_title(title):
    """
    Crops the title to a specified length
    """
    length = current_app.config['TITLE_LENGTH']
    if len(title) > length:
        return title[:length] + "..."
    return title


def render_markup(text):
    """
    Renders the given text as bbcode
    """
    return render_bbcode(text)


def is_online(user):
    """
    A simple check, to see if the user was online
    within a specified time range
    """
    return user.lastseen >= time_diff()


def time_diff():
    """
    Calculates the time difference between `now` and the ONLINE_LAST_MINUTES
    variable from the configuration.
    """
    now = datetime.utcnow()
    diff = now - timedelta(minutes=current_app.config['ONLINE_LAST_MINUTES'])
    return diff


def format_date(value, format='%Y-%m-%d'):
    """
    Returns a formatted time string
    """
    return value.strftime(format)


def time_since(value):
    """
    Just a interface for `time_delta_format`
    """
    return time_delta_format(value)


def time_delta_format(dt, default=None):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    Ref: https://bitbucket.org/danjac/newsmeme/src/a281babb9ca3/newsmeme/
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
