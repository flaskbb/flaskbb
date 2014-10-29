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
    if can_moderate(user=user, forum=forum):
        return True
    if post_user_id and user.is_authenticated():
        return user.permissions[perm] and user.id == post_user_id
    return not user.permissions['banned'] and user.permissions[perm]


def is_moderator(user):
    """Returns ``True`` if the user is in a moderator or super moderator group.

    :param user: The user who should be checked.
    """
    return user.permissions['mod'] or user.permissions['super_mod']


def is_admin(user):
    """Returns ``True`` if the user is a administrator.

    :param user:  The user who should be checked.
    """
    return user.permissions['admin']


def is_admin_or_moderator(user):
    """Returns ``True`` if the user is either a admin or in a moderator group

    :param user: The user who should be checked.
    """
    return is_admin(user) or is_moderator(user)


def can_moderate(user, forum=None, perm=None):
    """Checks if a user can moderate a forum or a user.
    He needs to be super moderator or a moderator of the
    specified forum.

    :param user: The user for whom we should check the permission.

    :param forum: The forum that should be checked. If no forum is specified
                  it will check if the user has at least moderator permissions
                  and then it will perform another permission check for ``mod``
                  permissions (they start with ``mod_``).

    :param perm: Optional - Check if the user also has the permission to do
                 certain things in the forum. There are a few permissions
                 where you need to be at least a moderator (or anything higher)
                 in the forum and therefore you can pass a permission and
                 it will check if the user has it. Those special permissions
                 are documented here: <INSERT LINK TO DOCS>
    """
    # Check if the user has moderator specific permissions (mod_ prefix)
    if is_admin_or_moderator(user) and forum is None:

        if perm is not None and perm.startswith("mod_"):
            return user.permissions[perm]

        # If no permission is definied, return False
        return False

    # check if the user is a moderation and is moderating the forum
    if user.permissions['mod'] and user in forum.moderators:
        return True

    # if the user is a super_mod or admin, he can moderate all forums
    return user.permissions['super_mod'] or user.permissions['admin']


def can_edit_post(user, post):
    """Check if the post can be edited by the user"""
    topic = post.topic
    if can_moderate(user, topic.forum):
        return True
    if topic.locked or topic.forum.locked:
        return False
    return check_perm(user=user, perm='editpost', forum=post.topic.forum,
                      post_user_id=post.user_id)


def can_delete_post(user, post_user_id, forum):
    """Check if the post can be deleted by the user"""

    return check_perm(user=user, perm='deletepost', forum=forum,
                      post_user_id=post_user_id)


def can_delete_topic(user, post_user_id, forum):
    """Check if the topic can be deleted by the user"""

    return check_perm(user=user, perm='deletetopic', forum=forum,
                      post_user_id=post_user_id)


def can_post_reply(user, topic):
    """Check if the user is allowed to post in the forum"""
    if can_moderate(user, topic.forum):
        return True
    if topic.locked or topic.forum.locked:
        return False
    return check_perm(user=user, perm='postreply', forum=topic.forum)


def can_post_topic(user, forum):
    """Checks if the user is allowed to create a new topic in the forum"""

    return check_perm(user=user, perm='posttopic', forum=forum)


# Moderator permission checks
def can_edit_user(user):
    """Check if the user is allowed to edit another users profile.
    Requires at least ``mod`` permissions.
    """
    return can_moderate(user=user, perm="mod_edituser")


def can_ban_user(user):
    """Check if the user is allowed to ban another user.
    Requires at least ``mod`` permissions.
    """
    return can_moderate(user=user, perm="mod_banuser")
