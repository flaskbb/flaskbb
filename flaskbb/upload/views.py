# -*- coding: utf-8 -*-
"""
flaskbb.user.views
~~~~~~~~~~~~~~~~~~

The user view handles the user profile
and the user settings from a signed in user.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging

from flask import Blueprint, Flask, send_from_directory
from flask.views import MethodView
from pluggy import HookimplMarker

from flaskbb.utils.helpers import register_view
from flaskbb.utils.uploads import get_avatar_upload_path

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)


class UploadedAvatar(MethodView):  # pragma: no cover
    def get(self, avatar: str):
        return send_from_directory(get_avatar_upload_path(), avatar)


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    uploads = Blueprint("uploads", __name__)
    register_view(
        uploads,
        routes=["/avatar/<avatar>"],
        view_func=UploadedAvatar.as_view("avatar"),
    )

    app.register_blueprint(uploads, url_prefix=app.config["UPLOAD_URL_PREFIX"])
