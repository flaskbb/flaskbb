"""
flaskbb.search.forms
~~~~~~~~~~~~~~~~~~~~~

The forms for the search page.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging

from flask_babelplus import lazy_gettext as _
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateField, HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms_sqlalchemy.fields import QuerySelectField

from flaskbb.forum.models import Forum
from flaskbb.search.service import search_forums, search_users
from flaskbb.user.models import User
from flaskbb.utils.helpers import real

logger = logging.getLogger(__name__)


class SearchForm(FlaskForm):
    search_query = StringField(_("Criteria"), validators=[DataRequired(), Length(min=3, max=50)])

    search_type = SelectField(
        _("Search in"),
        validators=[DataRequired()],
        choices=[("forum", _("Forums")), ("user", _("Users"))],
        default="forum",
    )

    # Advanced filters, only relevant when search_type == "forum".
    content_type = SelectField(
        _("Content type"),
        validators=[DataRequired()],
        choices=[("topic", _("Topics")), ("post", _("Posts"))],
        default="topic",
    )

    forum_id = QuerySelectField(
        _("Forum"),
        validators=[Optional()],
        allow_blank=True,
        blank_text=_("All forums"),
        get_label="title",
    )

    author = StringField(_("Author"), validators=[Optional()])

    date_from = DateField(_("From"), validators=[Optional()])

    date_to = DateField(_("To"), validators=[Optional()])

    state = SelectField(
        _("State"),
        validators=[Optional()],
        choices=[
            ("", _("Any")),
            ("locked", _("Locked")),
            ("unlocked", _("Not locked")),
            ("important", _("Pinned")),
            ("hidden", _("Hidden")),
        ],
        default="",
    )

    # Tracks whether the advanced filters panel was expanded, so it stays
    # expanded/collapsed across the search submit instead of only opening
    # when an advanced field happens to have data.
    advanced_open = HiddenField(default="")

    submit = SubmitField(_("Search"))

    def __init__(self, *args, user: User | None = None, **kwargs):
        self.user = real(user) if user is not None else real(current_user)
        super().__init__(*args, **kwargs)

        self.forum_id.query_factory = lambda: Forum.get_accessible(self.user)

        has_viewhidden = bool(
            self.user.is_authenticated and self.user.permissions.get("viewhidden")
        )
        if not has_viewhidden:
            self.state.choices = [  # pyright: ignore[reportAttributeAccessIssue]
                choice for choice in self.state.choices or [] if choice[0] != "hidden"
            ]

    def get_results(self):
        query = self.search_query.data or ""
        if self.search_type.data == "user":
            return search_users(query)

        return search_forums(
            query,
            self.user,
            content_type=self.content_type.data or "topic",
            forum=self.forum_id.data,
            author=self.author.data,
            date_from=self.date_from.data,
            date_to=self.date_to.data,
            state=self.state.data or "",
        )
