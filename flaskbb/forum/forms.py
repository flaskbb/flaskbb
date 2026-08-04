"""
flaskbb.forum.forms
~~~~~~~~~~~~~~~~~~~

It provides the forms that are needed for the forum views.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import os

from flask_allows2 import Permission
from flask_babelplus import lazy_gettext as _
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileStorage, MultipleFileField
from jinja2.filters import do_filesizeformat
from wtforms import (
    BooleanField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    widgets,
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import flaskbb_search, pluggy
from flaskbb.forum.models import Post, Report, Topic
from flaskbb.forum.utils import handle_post_attachments, parse_attachment_types
from flaskbb.user.models import User
from flaskbb.utils.helpers import time_utcnow
from flaskbb.utils.requirements import CanPostAttachment

logger = logging.getLogger(__name__)


class AttachmentFormMixin:
    """Adds attachment upload/removal fields to a post or topic form.

    The fields are deliberately not named ``attachments`` -
    ``EditTopicForm.populate_obj`` populates every form field onto the
    post object and would clobber the ORM relationship of the same name.
    """

    new_attachments = MultipleFileField(_("Attachments"))
    delete_attachments = SelectMultipleField(
        _("Delete attachments"),
        coerce=int,
        choices=[],
        validators=[Optional()],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
    )

    def _existing_attachment_count(self) -> int:
        return 0

    def _set_attachment_choices(self, post: Post | None):
        if post is not None and post.id:
            self.delete_attachments.choices = [
                (a.id, a.original_filename) for a in post.attachments
            ]

    def validate_new_attachments(self, field):
        files = [
            f for f in (field.data or []) if isinstance(f, FileStorage) and f.filename
        ]
        if not files:
            return

        if not flaskbb_config["ATTACHMENTS_ENABLED"]:
            raise ValidationError(_("Attachments are disabled."))

        if not Permission(CanPostAttachment, identity=current_user):
            raise ValidationError(_("You are not allowed to upload attachments."))

        per_post = int(flaskbb_config["ATTACHMENTS_PER_POST"] or 0)
        deleted = len(self.delete_attachments.data or [])
        total = len(files) + self._existing_attachment_count() - deleted
        if total > per_post:
            raise ValidationError(
                _(
                    "Only %(amount)s attachments per post are allowed.",
                    amount=per_post,
                )
            )

        allowed_types = parse_attachment_types(flaskbb_config["ATTACHMENT_TYPES"])
        max_size_kb = int(flaskbb_config["ATTACHMENT_MAX_SIZE"] or 0)
        max_size = max_size_kb * 1024
        for file in files:
            ext = os.path.splitext(file.filename or "")[1].lstrip(".").lower()
            if ext not in allowed_types:
                raise ValidationError(
                    _(
                        "File type %(ext)s is not allowed. Allowed types "
                        "are: %(types)s",
                        ext=ext,
                        types=", ".join(sorted(allowed_types)),
                    )
                )

            file.stream.seek(0, os.SEEK_END)
            size = file.stream.tell()
            file.stream.seek(0)
            if max_size and size > max_size:
                raise ValidationError(
                    _(
                        "Attachments cannot be bigger than %(size)s.",
                        size=do_filesizeformat(max_size),
                    )
                )


class PostForm(FlaskForm, AttachmentFormMixin):
    content = TextAreaField(
        _("Content"),
        validators=[
            DataRequired(message=_("You cannot post a reply without content."))
        ],
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
    track_topic = BooleanField(
        _("Track this topic"), default=False, validators=[Optional()]
    )

    def __init__(self, *args, **kwargs):
        self.post = kwargs.get("obj", None)
        PostForm.__init__(self, *args, **kwargs)
        self._set_attachment_choices(self.post)

    def _existing_attachment_count(self):
        if self.post is None or not self.post.id:
            return 0
        return len(self.post.attachments)

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
        validators=[
            DataRequired(message=_("You cannot post a reply without content."))
        ],
    )

    track_topic = BooleanField(
        _("Track this topic"), default=False, validators=[Optional()]
    )

    submit = SubmitField(_("Post topic"))

    def save(self, user, forum):
        topic = Topic(title=self.title.data, content=self.content.data)

        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        pluggy.hook.flaskbb_form_topic_save(form=self, topic=topic)
        topic = topic.save(user=user, forum=forum)
        if topic is not None:
            handle_post_attachments(self, topic.first_post, user)
        return topic


class NewTopicForm(TopicForm):
    pass


class EditTopicForm(TopicForm):
    submit = SubmitField(_("Save topic"))

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.get("obj").topic
        TopicForm.__init__(self, *args, **kwargs)
        self._set_attachment_choices(self.topic.first_post)

    def _existing_attachment_count(self):
        return len(self.topic.first_post.attachments)

    def populate_obj(self, *objs):
        """
        Populates the attributes of the passed `obj`s with data from the
        form's fields. This is especially useful to populate the topic and
        post objects at the same time.
        """
        for obj in objs:
            super().populate_obj(obj)

    def save(self, user, forum):
        if self.track_topic.data:
            user.track_topic(self.topic)
        else:
            user.untrack_topic(self.topic)

        if (
            self.topic.last_post_id == forum.last_post_id
            and self.title.data != forum.last_post_title
        ):
            forum.last_post_title = self.title.data

        self.topic.first_post.date_modified = time_utcnow()
        self.topic.first_post.modified_by = user.username

        pluggy.hook.flaskbb_form_topic_save(form=self, topic=self.topic)
        topic = self.topic.save(user=user, forum=forum)
        if topic is not None:
            handle_post_attachments(self, topic.first_post, user)
        return topic


class ReportForm(FlaskForm):
    reason = TextAreaField(
        _("Reason"),
        validators=[
            DataRequired(message=_("What is the reason for reporting this post?"))
        ],
    )

    submit = SubmitField(_("Report post"))

    def save(self, user, post):
        report = Report(reason=self.reason.data)
        return report.save(post=post, user=user)


class UserSearchForm(FlaskForm):
    search_query = StringField(
        _("Search"), validators=[DataRequired(), Length(min=3, max=50)]
    )

    submit = SubmitField(_("Search"))

    def get_results(self):
        # search_query is DataRequired, so by the time get_results() is
        # called (after a successful validate()) .data is never empty -
        # the "or ''" is only to satisfy the type checker.
        query = self.search_query.data or ""
        return flaskbb_search.search(User, query)
