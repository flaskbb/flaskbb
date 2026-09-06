"""
flaskbb.forum.utils
~~~~~~~~~~~~~~~~~~~

Utilities specific to the FlaskBB forums module

:copyright: (c) 2018 the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

import logging
import mimetypes
import os
from typing import cast, TYPE_CHECKING

from flask import Response
from flask_allows2 import Permission
from flask_babelplus import lazy_gettext as _
from flask_wtf.file import MultipleFileField
from jinja2.filters import do_filesizeformat
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from wtforms import Field, SelectMultipleField, widgets
from wtforms.validators import Optional, ValidationError

from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import db, login_manager
from flaskbb.utils.proxies import current_user
from flaskbb.utils.requirements import CanPostAttachment
from flaskbb.utils.uploads import (
    get_attachment_disk_path,
    get_image_info,
    make_attachment_filename,
)

if TYPE_CHECKING:
    from flaskbb.forum.models import Forum, Post
    from flaskbb.user.models import User

from .locals import current_forum

logger = logging.getLogger(__name__)


def force_login_if_needed() -> Response | None:
    """
    Forces a login if the current user is unauthed and the current forum
    doesn't allow guest users.
    """
    if current_forum and should_force_login(current_user, current_forum):
        return cast(Response, login_manager.unauthorized())


def should_force_login(user: "User", forum: "Forum"):
    return not user.is_authenticated and not (
        {g.id for g in forum.groups} & {g.id for g in user.groups}
    )


def parse_attachment_types(raw: str | None) -> set[str]:
    """Parses the ATTACHMENT_TYPES setting (a comma separated string of
    file extensions) into a set of normalized extensions.
    """
    if not raw:
        return set()
    return {ext.strip().lstrip(".").lower() for ext in raw.split(",") if ext.strip(". ")}


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

    def _set_attachment_choices(self, post: "Post | None"):
        if post is not None and post.id:
            self.delete_attachments.choices = [
                (a.id, a.original_filename) for a in post.attachments
            ]

    def validate_new_attachments(self, field: Field):
        files = [f for f in (field.data or []) if isinstance(f, FileStorage) and f.filename]
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
                        "File type %(ext)s is not allowed. Allowed types are: %(types)s",
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


def handle_post_attachments(form: AttachmentFormMixin, post: "Post | None", user: "User") -> None:
    """Applies the attachment changes of a post/topic form to an already
    saved post: deletes the attachments selected for removal and stores
    the newly uploaded files.

    Must run after ``post.save()`` so ``post.id`` exists.
    """
    from flaskbb.forum.models import Attachment

    delete_ids = set(form.delete_attachments.data or [])
    new_files = [
        f for f in (form.new_attachments.data or []) if isinstance(f, FileStorage) and f.filename
    ]

    if post is None or (not delete_ids and not new_files):
        return

    for attachment in post.attachments:
        if attachment.id in delete_ids:
            db.session.delete(attachment)

    for file in new_files:
        stored_filename = make_attachment_filename()
        disk_path = get_attachment_disk_path(post.id, stored_filename)

        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)

        # never trust the client-supplied mimetype: use the sniffed image
        # format if there is one, the (sanitized) extension otherwise
        width = height = None
        content_type = None
        image_info = get_image_info(file)
        if image_info and image_info["content_type"]:
            content_type = "image/" + str(image_info["content_type"])
            width = int(image_info["width"])
            height = int(image_info["height"])
        if content_type is None:
            content_type = (
                mimetypes.guess_type(secure_filename(file.filename or ""))[0]
                or "application/octet-stream"
            )

        os.makedirs(os.path.dirname(disk_path), exist_ok=True)
        file.save(disk_path)

        attachment = Attachment(
            post_id=post.id,
            user_id=user.id,
            filename=stored_filename,
            original_filename=file.filename or stored_filename,
            content_type=content_type,
            size=size,
            width=width,
            height=height,
        )
        db.session.add(attachment)

    db.session.commit()
