# -*- coding: utf-8 -*-
"""
    flaskbb.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~~

    A place for our decorators.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)
        if not current_user.permissions['admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def moderator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)

        if not any([current_user.permissions['admin'],
                    current_user.permissions['super_mod'],
                    current_user.permissions['mod']]):
            abort(403)

        return f(*args, **kwargs)
    return decorated


def can_access_forum(func):
    def decorated(*args, **kwargs):
        forum_id = kwargs['forum_id'] if 'forum_id' in kwargs else args[1]
        from flaskbb.forum.models import Forum
        from flaskbb.user.models import Group

        # get list of user group ids
        if current_user.is_authenticated():
            user_groups = [gr.id for gr in current_user.groups]
        else:
            user_groups = [Group.get_guest_group().id]

        user_forums = Forum.query.filter(
            Forum.id == forum_id, Forum.groups.any(Group.id.in_(user_groups))
        ).all()

        if len(user_forums) < 1:
            abort(403)

        return func(*args, **kwargs)
    return decorated


def can_access_topic(func):
    def decorated(*args, **kwargs):
        topic_id = kwargs['topic_id'] if 'topic_id' in kwargs else args[1]
        from flaskbb.forum.models import Forum, Topic
        from flaskbb.user.models import Group

        topic = Topic.query.get(topic_id == topic_id)
        # get list of user group ids
        if current_user.is_authenticated():
            user_groups = [gr.id for gr in current_user.groups]
        else:
            user_groups = [Group.get_guest_group().id]

        user_forums = Forum.query.filter(
            Forum.id == topic.forum.id,
            Forum.groups.any(Group.id.in_(user_groups))
        ).all()

        if len(user_forums) < 1:
            abort(403)

        return func(*args, **kwargs)
    return decorated
