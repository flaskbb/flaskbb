"""
    flaskbb.utils.requirements
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Authorization requirements for FlaskBB.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
import logging
from flask_allows import Requirement, Or, And

from flaskbb.exceptions import FlaskBBError
from flaskbb.forum.models import Post, Topic, Forum
from flaskbb.user.models import Group


logger = logging.getLogger(__name__)


class Has(Requirement):
    def __init__(self, permission):
        self.permission = permission

    def __repr__(self):
        return "<Has({!s})>".format(self.permission)

    def fulfill(self, user, request):
        return user.permissions.get(self.permission, False)


class IsAuthed(Requirement):
    def fulfill(self, user, request):
        return user.is_authenticated


class IsModeratorInForum(IsAuthed):
    def __init__(self, forum=None, forum_id=None):
        self.forum_id = forum_id
        self.forum = forum

    def fulfill(self, user, request):
        moderators = self._get_forum_moderators(request)
        return (super(IsModeratorInForum, self).fulfill(user, request) and
                self._user_is_forum_moderator(user, moderators))

    def _user_is_forum_moderator(self, user, moderators):
        return user in moderators

    def _get_forum_moderators(self, request):
        return self._get_forum(request).moderators

    def _get_forum(self, request):
        if self.forum is not None:
            return self.forum
        elif self.forum_id is not None:
            return self._get_forum_from_id()
        return self._get_forum_from_request(request)

    def _get_forum_from_id(self):
        return Forum.query.get(self.forum_id)

    def _get_forum_from_request(self, request):
        view_args = request.view_args
        if 'post_id' in view_args:
            return Post.query.get(view_args['post_id']).topic.forum
        elif 'topic_id' in view_args:
            return Topic.query.get(view_args['topic_id']).forum
        elif 'forum_id' in view_args:
            return Forum.query.get(view_args['forum_id'])
        else:
            raise FlaskBBError


class IsSameUser(IsAuthed):
    def __init__(self, topic_or_post=None):
        self._topic_or_post = topic_or_post

    def fulfill(self, user, request):
        return (super(IsSameUser, self).fulfill(user, request) and
                user.id == self._determine_user(request))

    def _determine_user(self, request):
        if self._topic_or_post is not None:
            return self._topic_or_post.user_id
        return self._get_user_id_from_post(request)

    def _get_user_id_from_post(self, request):
        view_args = request.view_args
        if 'post_id' in view_args:
            return Post.query.get(view_args['post_id']).user_id
        elif 'topic_id' in view_args:
            return Topic.query.get(view_args['topic_id']).user_id
        else:
            raise FlaskBBError


class TopicNotLocked(Requirement):
    def __init__(self, topic=None, topic_id=None, post_id=None, post=None):
        self._topic = topic
        self._topic_id = topic_id
        self._post = post
        self._post_id = post_id

    def fulfill(self, user, request):
        return not any(self._determine_locked(request))

    def _determine_locked(self, request):
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
                Topic.query.join(Forum, Forum.id == Topic.forum_id)
                .filter(Topic.id == self._topic_id)
                .with_entities(Topic.locked, Forum.locked)
                .first()
            )
        else:
            return self._get_topic_from_request(request)

    def _get_topic_from_request(self, request):
        view_args = request.view_args
        if 'post_id' in view_args:
            return (
                Topic.query.join(Post, Post.topic_id == Topic.id)
                .join(Forum, Forum.id == Topic.forum_id)
                .filter(Post.id == view_args['post_id'])
                .with_entities(Topic.locked, Forum.locked)
                .first()
            )
        elif 'topic_id' in view_args:
            return (
                Topic.query.join(Forum, Forum.id == Topic.forum_id)
                .filter(Topic.id == view_args['topic_id'])
                .with_entities(Topic.locked, Forum.locked)
                .first()
            )
        else:
            raise FlaskBBError("How did you get this to happen?")


class ForumNotLocked(Requirement):
    def __init__(self, forum=None, forum_id=None):
        self._forum = forum
        self._forum_id = forum_id

    def fulfill(self, user, request):
        return self._is_forum_locked(request)

    def _is_forum_locked(self, request):
        forum = self._determine_forum(request)
        return not forum.locked

    def _determine_forum(self, request):
        if self._forum is not None:
            return self._forum
        elif self._forum_id is not None:
            return Forum.query.get(self._forum_id)
        else:
            return self._get_forum_from_request(request)

    def _get_forum_from_request(self, request):
        view_args = request.view_args

        # These queries look big and nasty, but they really aren't that bad
        # Basically, find the forum this post or topic belongs to
        # with_entities returns a KeyedTuple with only the locked status

        if 'post_id' in view_args:
            return (
                Forum.query.join(Topic, Topic.forum_id == Forum.id)
                .join(Post, Post.topic_id == Topic.id)
                .filter(Post.id == view_args['post_id'])
                .with_entities(Forum.locked)
                .first()
            )

        elif 'topic_id' in view_args:
            return (
                Forum.query.join(Topic, Topic.forum_id == Forum.id)
                .filter(Topic.id == view_args['topic_id'])
                .with_entities(Forum.locked)
                .first()
            )

        elif 'forum_id' in view_args:
            return Forum.query.get(view_args['forum_id'])


class CanAccessForum(Requirement):
    def fulfill(self, user, request):
        forum_id = request.view_args['forum_id']
        group_ids = [g.id for g in user.groups]

        return Forum.query.filter(
            Forum.id == forum_id,
            Forum.groups.any(Group.id.in_(group_ids))
        ).count()


class CanAccessTopic(Requirement):
    def fulfill(self, user, request):
        topic_id = request.view_args['topic_id']
        group_ids = [g.id for g in user.groups]

        return Forum.query.join(Topic, Topic.forum_id == Forum.id).filter(
            Topic.id == topic_id,
            Forum.groups.any(Group.id.in_(group_ids))
        ).count()


def IsAtleastModeratorInForum(forum_id=None, forum=None):
    return Or(IsAtleastSuperModerator, IsModeratorInForum(forum_id=forum_id,
                                                          forum=forum))

IsMod = And(IsAuthed(), Has('mod'))
IsSuperMod = And(IsAuthed(), Has('super_mod'))
IsAdmin = And(IsAuthed(), Has('admin'))

IsAtleastModerator = Or(IsAdmin, IsSuperMod, IsMod)

IsAtleastSuperModerator = Or(IsAdmin, IsSuperMod)

CanBanUser = Or(IsAtleastSuperModerator, Has('mod_banuser'))

CanEditUser = Or(IsAtleastSuperModerator, Has('mod_edituser'))

CanEditPost = Or(IsAtleastSuperModerator,
                 And(IsModeratorInForum(), Has('editpost')),
                 And(IsSameUser(), Has('editpost'), TopicNotLocked()))

CanDeletePost = CanEditPost

CanPostReply = Or(And(Has('postreply'), TopicNotLocked()),
                  IsModeratorInForum(),
                  IsAtleastSuperModerator)

CanPostTopic = Or(And(Has('posttopic'), ForumNotLocked()),
                  IsAtleastSuperModerator,
                  IsModeratorInForum())

CanDeleteTopic = Or(IsAtleastSuperModerator,
                    And(IsModeratorInForum(), Has('deletetopic')),
                    And(IsSameUser(), Has('deletetopic'), TopicNotLocked()))


# Template Allowances -- gross, I know

def TplCanModerate(request):
    def _(user, forum):
        kwargs = {}

        if isinstance(forum, int):
            kwargs['forum_id'] = forum
        elif isinstance(forum, Forum):
            kwargs['forum'] = forum

        return IsAtleastModeratorInForum(**kwargs)(user, request)
    return _


def TplCanPostReply(request):
    def _(user, topic=None):
        kwargs = {}

        if isinstance(topic, int):
            kwargs['topic_id'] = topic
        elif isinstance(topic, Topic):
            kwargs['topic'] = topic

        return Or(
            IsAtleastSuperModerator,
            IsModeratorInForum(),
            And(Has('postreply'), TopicNotLocked(**kwargs))
        )(user, request)
    return _


def TplCanEditPost(request):
    def _(user, topic_or_post=None):
        kwargs = {}

        if isinstance(topic_or_post, int):
            kwargs['topic_id'] = topic_or_post
        elif isinstance(topic_or_post, Topic):
            kwargs['topic'] = topic_or_post
        elif isinstance(topic_or_post, Post):
            kwargs['post'] = topic_or_post

        return Or(
            IsAtleastSuperModerator,
            And(IsModeratorInForum(), Has('editpost')),
            And(
                IsSameUser(topic_or_post),
                Has('editpost'),
                TopicNotLocked(**kwargs)
            ),
        )(user, request)
    return _

TplCanDeletePost = TplCanEditPost


def TplCanPostTopic(request):
    def _(user, forum):
        kwargs = {}

        if isinstance(forum, int):
            kwargs['forum_id'] = forum
        elif isinstance(forum, Forum):
            kwargs['forum'] = forum

        return Or(
            IsAtleastSuperModerator,
            IsModeratorInForum(**kwargs),
            And(Has('posttopic'), ForumNotLocked(**kwargs))
        )(user, request)
    return _


def TplCanDeleteTopic(request):
    def _(user, topic=None):
        kwargs = {}

        if isinstance(topic, int):
            kwargs['topic_id'] = topic
        elif isinstance(topic, Topic):
            kwargs['topic'] = topic

        return Or(
            IsAtleastSuperModerator,
            And(IsModeratorInForum(), Has('deletetopic')),
            And(IsSameUser(), Has('deletetopic'), TopicNotLocked(**kwargs))
        )(user, request)
    return _
