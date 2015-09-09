"""
    flaskbb.utils.requirements
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Authorization requirements for FlaskBB.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from flask_allows import Requirement, Or, And
from flaskbb.exceptions import FlaskBBError
from flaskbb.forum.models import Post, Topic, Forum


class IsAuthed(Requirement):
    def fulfill(self, user, request):
        return user.is_authenticated()


class IsMod(IsAuthed):
    def fulfill(self, user, request):
        return (super(IsMod, self).fulfill(user, request) and
                user.permissions.get('mod'))


class IsSuperMod(IsAuthed):
    def fulfill(self, user, request):
        return (super(IsSuperMod, self).fulfill(user, request) and
                user.permissions.get('super_mod'))


class IsAdmin(IsAuthed):
    def fulfill(self, user, request):
        return (super(IsAdmin, self).fulfill(user, request) and
                user.permissions.get('admin'))


class IsModeratorInForum(IsAuthed):
    def fulfill(self, user, request):
        moderators = self._get_forum_moderators(request)
        return (super(IsModeratorInForum, self).fulfill(user, request) and
                self._user_is_forum_moderator(user, moderators))

    def _user_is_forum_moderator(self, user, moderators):
        return user in moderators

    def _get_forum_moderators(self, request):
        return self._get_forum_from_request(request).moderators

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
    def fulfill(self, user, request):
        return (super(IsSameUser, self).fulfill(user, request) and
                user.id == self._get_user_id_from_post(request))

    def _get_user_id_from_post(self, request):
        view_args = request.view_args
        if 'post_id' in view_args:
            return Post.query.get(view_args['post_id']).user_id
        elif 'topic_id' in view_args:
            return Topic.query.get(view_args['topic_id']).user_id
        else:
            raise FlaskBBError


class Has(Requirement):
    def __init__(self, permission):
        self.permission = permission

    def fulfill(self, user, request):
        return user.permissions.get(self.permission)


class TopicNotLocked(Requirement):
    def fulfill(self, user, request):
        return not self._is_topic_or_forum_locked(request)

    def _get_topic_from_request(self, request):
        view_args = request.view_args
        if 'post_id' in view_args:
            return Post.query.get(view_args['post_id']).topic
        elif 'topic_id' in view_args:
            return Topic.query.get(view_args['topic_id'])
        else:
            raise FlaskBBError

    def _is_topic_or_forum_locked(self, request):
        topic = self._get_topic_from_request(request)
        return topic.locked or topic.forum.locked


class ForumNotLocked(Requirement):
    def fulfill(self, user, request):
        return not self._is_forum_locked(request)

    def _is_forum_locked(self, request):
        return self._get_forum_from_request(request).locked

    def _get_forum_from_request(self, request):
        view_args = request.view_args
        if 'post_id' in view_args:
            return Post.query.get(view_args['post_id']).topic.forum
        elif 'topic_id' in view_args:
            return Topic.query.get(view_args['topic_id']).forum
        elif 'forum_id' in view_args:
            return Forum.query.get(view_args['forum_id'])


IsAtleastModerator = Or(IsAdmin(), IsSuperMod(), IsMod())

IsAtleastSuperModerator = Or(IsAdmin(), IsSuperMod())

CanBanUser = Or(IsAtleastSuperModerator, Has('mod_banuser'))

CanEditUser = Or(IsAtleastSuperModerator, Has('mod_edituser'))

CanEditPost = Or(And(IsSameUser(), Has('editpost'), TopicNotLocked()),
                 IsAtleastSuperModerator,
                 And(IsModeratorInForum(), Has('editpost')))

CanDeletePost = Or(And(IsSameUser(), Has('editpost'), TopicNotLocked()),
                   IsAtleastSuperModerator,
                   And(IsModeratorInForum(), Has('editpost')))

CanPostReply = Or(And(Has('postreply'), TopicNotLocked()),
                  IsModeratorInForum(),
                  IsAtleastSuperModerator)

CanPostTopic = Or(And(Has('posttopic'), ForumNotLocked()),
                  IsAtleastSuperModerator,
                  IsModeratorInForum())

CanDeleteTopic = Or(And(IsSameUser(), Has('deletetopic'), TopicNotLocked()),
                    IsAtleastSuperModerator,
                    And(IsModeratorInForum, Has('deletetopic')))
