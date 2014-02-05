# -*- coding: utf-8 -*-
"""
    flaskbb.utils.permissions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    A place for all permission checks

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""


def check_perm(user, perm, forum, post_user_id=None):
    """Checks if the `user` has a specified `perm` in the `forum`
    If post_user_id is provided, it will also check if the user
    has created the post

    :param user: The user for whom we should check the permission

    :param perm: The permission. You can find a full list of available
                 permissions here: <INSERT LINK TO DOCS>

    :param forum: The forum where we should check the permission against

    :param post_user_id: If post_user_id is given, it will also perform an
                         check if the user is the owner of this topic or post.
    """
    if can_moderate(user, forum):
        return True
    if post_user_id and user.is_authenticated():
        return user.permissions[perm] and user.id == post_user_id
    return user.permissions[perm]


def can_moderate(user, forum):
    """Checks if a user can moderate a forum
    He needs to be super moderator or a moderator of the
    specified forum

    :param user: The user for whom we should check the permission.

    :param forum: The forum that should be checked.
    """
    if user.permissions['mod'] and user in forum.moderators:
        return True
    return user.permissions['super_mod'] or user.permissions['admin']


def can_edit_post(user, post_user_id, forum):
    """Check if the post can be edited by the user"""

    return check_perm(user=user, perm='editpost', forum=forum,
                      post_user_id=post_user_id)


def can_delete_post(user, post_user_id, forum):
    """Check if the post can be deleted by the user"""

    return check_perm(user=user, perm='deletepost', forum=forum,
                      post_user_id=post_user_id)


def can_delete_topic(user, post_user_id, forum):
    """Check if the topic can be deleted by the user"""

    return check_perm(user=user, perm='deletetopic', forum=forum,
                      post_user_id=post_user_id)


def can_lock_topic(user, forum):
    """ Check if the user is allowed to lock a topic in the forum"""

    return check_perm(user=user, perm='locktopic', forum=forum)


def can_move_topic(user, forum):
    """Check if the user is allowed to move a topic in the forum"""

    return check_perm(user=user, perm='movetopic', forum=forum)


def can_post_reply(user, forum):
    """Check if the user is allowed to post in the forum"""

    return check_perm(user=user, perm='postreply', forum=forum)


def can_post_topic(user, forum):
    """Checks if the user is allowed to create a new topic in the forum"""

    return check_perm(user=user, perm='posttopic', forum=forum)
