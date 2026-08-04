"""
flaskbb.user.views
~~~~~~~~~~~~~~~~~~

The user view handles the user profile
and the user settings from a signed in user.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import os

from flask import Blueprint, Flask, send_from_directory
from flask.views import MethodView
from pluggy import HookimplMarker

from flaskbb.forum.models import Attachment
from flaskbb.utils.helpers import register_view
from flaskbb.utils.uploads import get_attachment_upload_path, get_avatar_upload_path

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)


class UploadedAvatar(MethodView):  # pragma: no cover
    def get(self, avatar: str):
        return send_from_directory(get_avatar_upload_path(), avatar)


class UploadedAttachment(MethodView):
    def get(self, filename: str, display_name: str):
        # Attachments are served publicly (like avatars). The display_name is cosmetic.
        # Attachments are not yet access control checked
        attachment = Attachment.get_by_or_404(filename=filename)
        return send_from_directory(
            os.path.join(get_attachment_upload_path(), str(attachment.post_id)),
            attachment.filename,
            # the stored name carries no extension, so the type has to come
            # from the (server side determined) content_type instead of being
            # guessed from the path
            mimetype=attachment.content_type,
            # forces Content-Disposition: attachment for anything that is
            # not an image, so browsers never render uploaded markup
            as_attachment=not attachment.is_image,
            download_name=attachment.original_filename,
        )


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    uploads = Blueprint("uploads", __name__)
    register_view(
        uploads,
        routes=["/avatar/<avatar>"],
        view_func=UploadedAvatar.as_view("avatar"),
    )
    register_view(
        uploads,
        routes=["/attachments/<filename>/<path:display_name>"],
        view_func=UploadedAttachment.as_view("attachment"),
    )

    app.register_blueprint(uploads, url_prefix=app.config["UPLOAD_URL_PREFIX"])
