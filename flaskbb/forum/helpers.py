# -*- coding: utf-8 -*-
"""
    flaskbb.forum.helpers
    ~~~~~~~~~~~~~~~~~~~~

    A few helper functions that are used by the forum's module.

    :copyright: (c) 2014 by the FlaskBB Team.
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
    Returns a list of parent forum ids for the passed `forum` object.
    """
    forum_ids = []
    parent = forum.parent
    while parent is not None and not parent.is_category:
        forum_ids.append(parent.id)
        parent = parent.parent

    return forum_ids


def get_forum_ids(forum):
    """
    Returns a list of forum ids for the passed `forum` object and its
    parent and child hierarchy.
    """
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


def get_forums(forum_query, current_user=False):
    """
    Assign each forum/category its appropriate (sub)forum
    If current_user is `True` the `forum_query` will look like this:
          Forum     ForumsRead
        [(<Forum 1>, None),
         (<Forum 2>, None),
         (<Forum 3>, <flaskbb.forum.models.ForumsRead at 0x105319250>),
         (<Forum 4>, None),
         (<Forum 5>, None),
         (<Forum 6>, <flaskbb.forum.models.ForumsRead at 0x105281090>)]
    and it will return something like this:
      Category      Forum         Subforums
    {<Forum 1>: {<Forum 2>: [<Forum 5>, <Forum 6>]},
    """
    if not current_user:
        forum_query = [(item, None) for item in forum_query]

    forums = OrderedDict()
    for category in forum_query:
        if category[0].is_category:
            forums[category] = OrderedDict()

            for forum in forum_query:
                if forum[0].parent_id == category[0].id:
                    forums[category][forum] = []

                    for subforum in forum_query:
                        if subforum[0].parent_id == forum[0].id:
                            forums[category][forum].append(subforum)
    return forums
