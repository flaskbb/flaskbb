"""
    flaskbb.utils.requirements
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Authorization requirements for FlaskBB.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
import logging

from flask_allows import And, Or, Permission, Requirement

from flaskbb.exceptions import FlaskBBError
from flaskbb.forum.locals import current_forum, current_post, current_topic
from flaskbb.forum.models import Forum, Post, Topic

logger = logging.getLogger(__name__)


class Has(Requirement):

    def __init__(self, permission):
        self.permission = permission

    def __repr__(self):
        return "<Has({!s})>".format(self.permission)

    def fulfill(self, user):
        return user.permissions.get(self.permission, False)


class IsAuthed(Requirement):

    def fulfill(self, user):
        return user.is_authenticated


class IsModeratorInForum(IsAuthed):

    def __init__(self, forum=None, forum_id=None):
        self.forum_id = forum_id
        self.forum = forum

    def fulfill(self, user):
        moderators = self._get_forum_moderators()
        return (
            super(IsModeratorInForum, self).fulfill(user)
            and self._user_is_forum_moderator(user, moderators)
        )

    def _user_is_forum_moderator(self, user, moderators):
        return user in moderators

    def _get_forum_moderators(self):
        return self._get_forum().moderators

    def _get_forum(self):
        if self.forum is not None:
            return self.forum
        elif self.forum_id is not None:
            return self._get_forum_from_id()
        return self._get_forum_from_request()

    def _get_forum_from_id(self):
        return Forum.query.get(self.forum_id)

    def _get_forum_from_request(self):
        if not current_forum:
            raise FlaskBBError("Could not load forum data")
        return current_forum


class IsSameUser(IsAuthed):

    def __init__(self, topic_or_post=None):
        self._topic_or_post = topic_or_post

    def fulfill(self, user):
        return (
            super(IsSameUser, self).fulfill(user)
            and user.id == self._determine_user()
        )

    def _determine_user(self):
        if self._topic_or_post is not None:
            return self._topic_or_post.user_id
        return self._get_user_id_from_post()

    def _get_user_id_from_post(self):
        if current_post:
            return current_post.user_id
        elif current_topic:
            return current_topic.user_id
        else:
            raise FlaskBBError("Could not determine user")


class TopicNotLocked(Requirement):

    def __init__(self, topic=None, topic_id=None, post_id=None, post=None):
        self._topic = topic
        self._topic_id = topic_id
        self._post = post
        self._post_id = post_id

    def fulfill(self, user):
        return not any(self._determine_locked())

    def _determine_locked(self):
        """
        Returns a pair of booleans:
            * Is the topic locked?
            * Is the forum the topic belongs to locked?

        Except in the case of a topic instance being provided to the
        constructor, all of these tuples are SQLA KeyedTuples.
        """
        if self._topic is not None:
            return self._topic.locked, self._topic.forum.locked
        elif self._post is not None:
            return self._post.topic.locked, self._post.topic.forum.locked
        elif self._topic_id is not None:
            return (
                Topic.query.join(Forum, Forum.id == Topic.forum_id).filter(
                    Topic.id == self._topic_id
                ).with_entities(
                    Topic.locked, Forum.locked
                ).first()
            )
        else:
            return self._get_topic_from_request()

    def _get_topic_from_request(self):
        if current_topic:
            return current_topic.locked, current_forum.locked
        else:
            raise FlaskBBError("How did you get this to happen?")


class ForumNotLocked(Requirement):

    def __init__(self, forum=None, forum_id=None):
        self._forum = forum
        self._forum_id = forum_id

    def fulfill(self, user):
        return self._is_forum_locked()

    def _is_forum_locked(self):
        forum = self._determine_forum()
        return not forum.locked

    def _determine_forum(self):
        if self._forum is not None:
            return self._forum
        elif self._forum_id is not None:
            return Forum.query.get(self._forum_id)
        else:
            return self._get_forum_from_request()

    def _get_forum_from_request(self):
        if current_forum:
            return current_forum
        raise FlaskBBError("Could not determine forum")


class CanAccessForum(Requirement):

    def fulfill(self, user):
        if not current_forum:
            raise FlaskBBError("Could not load forum data")

        forum_groups = {g.id for g in current_forum.groups}
        user_groups = {g.id for g in user.groups}
        return bool(forum_groups & user_groups)


def IsAtleastModeratorInForum(forum_id=None, forum=None):
    return Or(
        IsAtleastSuperModerator,
        IsModeratorInForum(forum_id=forum_id, forum=forum),
    )


IsMod = And(IsAuthed(), Has("mod"))
IsSuperMod = And(IsAuthed(), Has("super_mod"))
IsAdmin = And(IsAuthed(), Has("admin"))

IsAtleastModerator = Or(IsAdmin, IsSuperMod, IsMod)

IsAtleastSuperModerator = Or(IsAdmin, IsSuperMod)

CanBanUser = Or(IsAtleastSuperModerator, Has("mod_banuser"))

CanEditUser = Or(IsAtleastSuperModerator, Has("mod_edituser"))

CanEditPost = Or(
    IsAtleastSuperModerator,
    And(IsModeratorInForum(), Has("editpost")),
    And(CanAccessForum(), IsSameUser(), Has("editpost"), TopicNotLocked()),
)

CanDeletePost = CanEditPost

CanPostReply = Or(
    And(CanAccessForum(), Has("postreply"), TopicNotLocked()),
    IsModeratorInForum(),
    IsAtleastSuperModerator,
)

CanPostTopic = Or(
    And(CanAccessForum(), Has("posttopic"), ForumNotLocked()),
    IsAtleastSuperModerator,
    IsModeratorInForum(),
)

CanDeleteTopic = Or(
    IsAtleastSuperModerator,
    And(IsModeratorInForum(), Has("deletetopic")),
    And(CanAccessForum(), IsSameUser(), Has("deletetopic"), TopicNotLocked()),
)


def permission_with_identity(requirement, name=None):
    """
    Permission instance factory that can set a user at construction time
    can optionally name the closure for nicer debugging
    """

    def _(user):
        return Permission(requirement, identity=user)

    if name is not None:
        _.__name__ = name

    return _


# Template Requirements


def has_permission(permission):

    def _(user):
        return Permission(Has(permission), identity=user)

    _.__name__ = "Has_{}".format(permission)
    return _


def can_moderate(user, forum):
    kwargs = {}

    if isinstance(forum, int):
        kwargs["forum_id"] = forum
    elif isinstance(forum, Forum):
        kwargs["forum"] = forum

    return Permission(IsAtleastModeratorInForum(**kwargs), identity=user)


def can_post_reply(user, topic=None):
    kwargs = {}

    if isinstance(topic, int):
        kwargs["topic_id"] = topic
    elif isinstance(topic, Topic):
        kwargs["topic"] = topic

    return Permission(
        Or(
            IsAtleastSuperModerator,
            IsModeratorInForum(),
            And(Has("postreply"), TopicNotLocked(**kwargs)),
        ),
        identity=user,
    )


def can_edit_post(user, topic_or_post=None):
    kwargs = {}

    if isinstance(topic_or_post, int):
        kwargs["topic_id"] = topic_or_post
    elif isinstance(topic_or_post, Topic):
        kwargs["topic"] = topic_or_post
    elif isinstance(topic_or_post, Post):
        kwargs["post"] = topic_or_post

    return Permission(
        Or(
            IsAtleastSuperModerator,
            And(IsModeratorInForum(), Has("editpost")),
            And(
                IsSameUser(topic_or_post),
                Has("editpost"),
                TopicNotLocked(**kwargs),
            ),
        ),
        identity=user,
    )


def can_post_topic(user, forum):
    kwargs = {}

    if isinstance(forum, int):
        kwargs["forum_id"] = forum
    elif isinstance(forum, Forum):
        kwargs["forum"] = forum

    return Permission(
        Or(
            IsAtleastSuperModerator,
            IsModeratorInForum(**kwargs),
            And(Has("posttopic"), ForumNotLocked(**kwargs)),
        ),
        identity=user,
    )


def can_delete_topic(user, topic=None):
    kwargs = {}

    if isinstance(topic, int):
        kwargs["topic_id"] = topic
    elif isinstance(topic, Topic):
        kwargs["topic"] = topic

    return Permission(
        Or(
            IsAtleastSuperModerator,
            And(IsModeratorInForum(), Has("deletetopic")),
            And(IsSameUser(), Has("deletetopic"), TopicNotLocked(**kwargs)),
        ),
        identity=user,
    )
