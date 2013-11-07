# -*- coding: utf-8 -*-
"""
    flaskbb.forum.helpers
    ~~~~~~~~~~~~~~~~~~~~

    A few helper functions that are used by the forum's module.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from collections import OrderedDict


def get_child_ids(forum):
    """
    Returns a list of forum ids for the passed `forum` object and its
    child hierarchy.
    """
    forum_ids = [forum.id]
    if forum.children:
        for child in forum.children:
            forum_ids.extend(
                get_child_ids(child)  # Get the children from the children
            )
    return forum_ids


def get_parent_ids(forum):
    """
    Returns a list of forum ids for the passed `forum` object and its
    parent and child hierarchy.
    """
    forum_ids = []
    parent = forum.parent
    while parent is not None and not parent.is_category:
        forum_ids.append(parent.id)
        parent = parent.parent

    return forum_ids


def get_forum_ids(forum):
    forum_ids = []
    parent = forum.parent
    while parent is not None:
        if parent.is_category:
            forum_ids.extend(get_child_ids(forum))
            break
        else:
            forum_ids.extend(get_child_ids(parent))
            parent = parent.parent
    return set(forum_ids)


def get_forums(forum_query):
    """
    Pack all forum objects in a dict
    It looks like this:
      Category      Forum         Subforums
    {<Forum 1)>: {<Forum 2)>: [<Forum 5)>, <Forum 6)>]},
    """
    forums = OrderedDict()
    for category in forum_query:
        if category.is_category:
            forums[category] = OrderedDict()

            for forum in forum_query:
                if forum.parent_id == category.id:
                    forums[category][forum] = []

                    for subforum in forum_query:
                        if subforum.parent_id == forum.id:
                            forums[category][forum].append(subforum)
    return forums
