# -*- coding: utf-8 -*-
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
from typing import TYPE_CHECKING

from flask import current_app
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from werkzeug.local import LocalProxy
from werkzeug.utils import secure_filename

from flaskbb.extensions import db
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


def force_login_if_needed():
    """
    Forces a login if the current user is unauthed and the current forum
    doesn't allow guest users.
    """
    if current_forum and should_force_login(current_user, current_forum):
        return current_app.login_manager.unauthorized()  # pyright: ignore


def should_force_login(
    user: "User | LocalProxy[User | None]", forum: "Forum | LocalProxy[Forum | None]"
):
    return not user.is_authenticated and not (
        {g.id for g in forum.groups} & {g.id for g in user.groups}
    )


def parse_attachment_types(raw: str | None) -> set[str]:
    """Parses the ATTACHMENT_TYPES setting (a comma separated string of
    file extensions) into a set of normalized extensions.
    """
    if not raw:
        return set()
    return {
        ext.strip().lstrip(".").lower() for ext in raw.split(",") if ext.strip(". ")
    }


def handle_post_attachments(form, post: "Post | None", user: "User"):
    """Applies the attachment changes of a post/topic form to an already
    saved post: deletes the attachments selected for removal and stores
    the newly uploaded files.

    Must run after ``post.save()`` so ``post.id`` exists.
    """
    from flaskbb.forum.models import Attachment

    delete_ids = set(getattr(form.delete_attachments, "data", None) or [])
    new_files = [
        f
        for f in (getattr(form.new_attachments, "data", None) or [])
        if isinstance(f, FileStorage) and f.filename
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
