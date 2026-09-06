"""
flaskbb.forum.forms
~~~~~~~~~~~~~~~~~~~

It provides the forms that are needed for the forum views.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
from typing import Any, override

from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional

from flaskbb.extensions import flaskbb_search, pluggy
from flaskbb.forum.models import Forum, Post, Report, Topic
from flaskbb.forum.utils import AttachmentFormMixin, handle_post_attachments
from flaskbb.user.models import User
from flaskbb.utils.helpers import time_utcnow

logger = logging.getLogger(__name__)


class PostForm(FlaskForm, AttachmentFormMixin):
    content = TextAreaField(
        _("Content"),
        validators=[DataRequired(message=_("You cannot post a reply without content."))],
    )

    submit = SubmitField(_("Reply"))

    def save(self, user: User, topic: Topic):
        post = Post(content=self.content.data)
        pluggy.hook.flaskbb_form_post_save(form=self, post=post)
        post = post.save(user=user, topic=topic)
        handle_post_attachments(self, post, user)
        return post


class QuickreplyForm(PostForm):
    pass


class ReplyForm(PostForm):
    track_topic = BooleanField(_("Track this topic"), default=False, validators=[Optional()])

    post: Post | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.post = kwargs.get("obj")
        PostForm.__init__(self, *args, **kwargs)
        self._set_attachment_choices(self.post)

    @override
    def _existing_attachment_count(self) -> int:
        if self.post is None or not self.post.id:
            return 0
        return len(self.post.attachments)

    @override
    def save(self, user: User, topic: Topic):
        # new post
        if self.post is None:
            self.post = Post(content=self.content.data)
        else:
            self.post.date_modified = time_utcnow()
            self.post.modified_by = user.username

        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        pluggy.hook.flaskbb_form_post_save(form=self, post=self.post)
        post = self.post.save(user=user, topic=topic)
        handle_post_attachments(self, post, user)
        return post


class TopicForm(FlaskForm, AttachmentFormMixin):
    title = StringField(
        _("Topic title"),
        validators=[DataRequired(message=_("Please choose a title for your topic."))],
    )

    content = TextAreaField(
        _("Content"),
        validators=[DataRequired(message=_("You cannot post a reply without content."))],
    )

    track_topic = BooleanField(_("Track this topic"), default=False, validators=[Optional()])

    submit = SubmitField(_("Post topic"))

    def save(self, user: User, forum: Forum):
        topic = Topic(title=self.title.data, content=self.content.data)

        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        pluggy.hook.flaskbb_form_topic_save(form=self, topic=topic)
        topic = topic.save(user=user, forum=forum)
        handle_post_attachments(self, topic.first_post, user)
        return topic


class NewTopicForm(TopicForm):
    pass


class EditTopicForm(TopicForm):
    submit = SubmitField(_("Save topic"))

    # the form is always built from the topic's first post
    post: Post
    topic: Topic

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.post = kwargs["obj"]
        self.topic = self.post.topic
        TopicForm.__init__(self, *args, **kwargs)
        self._set_attachment_choices(self.post)

    @override
    def _existing_attachment_count(self) -> int:
        return len(self.post.attachments)

    @override
    def populate_obj(self, obj: object, *objs: object) -> None:
        """
        Populates the attributes of the passed `obj`s with data from the
        form's fields. This is especially useful to populate the topic and
        post objects at the same time.
        """
        for o in (obj, *objs):
            super().populate_obj(o)

    @override
    def save(self, user: User, forum: Forum):
        if self.track_topic.data:
            user.track_topic(self.topic)
        else:
            user.untrack_topic(self.topic)

        if (
            self.topic.last_post_id == forum.last_post_id
            and self.title.data != forum.last_post_title
        ):
            forum.last_post_title = self.title.data

        self.post.date_modified = time_utcnow()
        self.post.modified_by = user.username

        pluggy.hook.flaskbb_form_topic_save(form=self, topic=self.topic)
        topic = self.topic.save(user=user, forum=forum)
        handle_post_attachments(self, self.post, user)
        return topic


class ReportForm(FlaskForm):
    reason = TextAreaField(
        _("Reason"),
        validators=[DataRequired(message=_("What is the reason for reporting this post?"))],
    )

    submit = SubmitField(_("Report post"))

    def save(self, user: User, post: Post):
        report = Report(reason=self.reason.data)
        return report.save(post=post, user=user)


class UserSearchForm(FlaskForm):
    search_query = StringField(_("Search"), validators=[DataRequired(), Length(min=3, max=50)])

    submit = SubmitField(_("Search"))

    def get_results(self):
        # search_query is DataRequired, so by the time get_results() is
        # called (after a successful validate()) .data is never empty -
        # the "or ''" is only to satisfy the type checker.
        query = self.search_query.data or ""
        return flaskbb_search.search(User, query)
