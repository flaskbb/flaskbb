# -*- coding: utf-8 -*-
"""
    flaskbb.core.forum.update
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This modules provides services used in updating forum details
    across FlaskBB.

    :copyright: (c) 2014-2018 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import attr

from ..changesets import empty, is_empty


def _should_assign(current, new):
    return not is_empty(new) and current != new


@attr.s(hash=True, cmp=True, repr=True, frozen=True)
class PostUpdate(object):
    """Object representing an update of a post."""

    content = attr.ib(default=empty)
    date_modified = attr.ib(default=empty)
    modified_by = attr.ib(default=empty)

    def assign_to_post(self, post):
        for (name, value) in attr.asdict(self).items():
            if _should_assign(getattr(post, name), value):
                setattr(post, name, value)


@attr.s(hash=True, cmp=True, repr=True, frozen=True)
class TopicUpdate(PostUpdate):
    """Object representing an update of a topic."""

    title = attr.ib(default=empty)
    locked = attr.ib(default=empty)
    important = attr.ib(default=empty)

    def assign_to_topic(self, topic):
        for (name, value) in attr.asdict(self).items():
            if _should_assign(getattr(topic, name), value):
                setattr(topic, name, value)

            elif _should_assign(getattr(topic.first_post, name), value):
                setattr(topic.first_post, name, value)
