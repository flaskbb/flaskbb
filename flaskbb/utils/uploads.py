# -*- coding: utf-8 -*-
"""
flaskbb.utils.helpers
~~~~~~~~~~~~~~~~~~~~~

A few helpers that are used by flaskbb

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import os
from typing import TYPE_CHECKING, override

from flask import Flask, current_app
from flask_wtf.file import FileAllowed, FileSize, FileStorage
from PIL import ImageFile
from werkzeug.utils import secure_filename

if TYPE_CHECKING:
    pass

from flaskbb.utils.settings import flaskbb_config

logger = logging.getLogger(__name__)


class AvatarExtensionValidator(FileAllowed):
    def __init__(self, message: str | None = None):
        super().__init__(upload_set=[], message=message)  # pyright: ignore[reportUnknownMemberType]

    @override
    def __call__(self, form, field):
        self.upload_set = current_app.config.get("AVATAR_EXTENSIONS", [])  # pyright: ignore[reportUnknownMemberType]
        return super(AvatarExtensionValidator, self).__call__(form, field)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


class AvatarSizeValidator(FileSize):
    def __init__(self, message: str | None = None):
        super().__init__(max_size=None, min_size=0, message=message)  # pyright: ignore[reportUnknownMemberType]

    @override
    def __call__(self, form, field):
        self.max_size = flaskbb_config["AVATAR_SIZE"] * 1024
        self.min_size = 0
        if not self.message:
            self.message = "Image is too big! {}kb are allowed.".format(
                flaskbb_config["AVATAR_SIZE"]
            )
        return super(AvatarSizeValidator, self).__call__(form, field)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


def get_avatar_upload_path() -> str:
    if current_app.config.get("AVATAR_UPLOAD_PATH") is None:
        return os.path.join(current_app.static_folder or "static", "uploads", "avatar")
    return current_app.config["AVATAR_UPLOAD_PATH"]


def get_avatar_filename(username: str, filename: str | None) -> str:
    if filename:
        file_ext = os.path.splitext(filename)[1]
        return secure_filename("avatar_" + username + file_ext)
    return secure_filename("avatar_" + username)


def create_upload_directory(app: Flask):
    avatar_upload_path: str | None = app.config["AVATAR_UPLOAD_PATH"]

    if not avatar_upload_path:
        avatar_upload_path = os.path.join(
            app.static_folder or "static", "uploads", "avatar"
        )

    if os.path.exists(avatar_upload_path):
        return

    logger.info(f"Creating avatar upload path: {avatar_upload_path}")
    os.makedirs(avatar_upload_path, exist_ok=True)


def get_image_info(file: FileStorage):
    """Returns the content-type, image size (kb), height and width of
    an image without fully downloading it.

    :param url: The URL of the image.
    """
    if not file or not file.stream:
        return None

    image_data = {
        "content_type": "",
        "width": 0,
        "height": 0,
    }

    data = None
    parser = ImageFile.Parser()

    while True:
        data = file.stream.read(1024)
        if not data:
            file.stream.seek(0)
            break

        parser.feed(data)
        if parser.image:
            image_data["content_type"] = str.lower(parser.image.format or "")
            image_data["width"] = parser.image.size[0]
            image_data["height"] = parser.image.size[1]
            file.stream.seek(0)
            break

    return image_data


def validate_image(file: FileStorage):
    """A little wrapper for the :func:`get_image_info` function.
    If the image doesn't match the ``flaskbb_config`` settings it will
    return a tuple with a the first value is the custom error message and
    the second value ``False`` for not passing the check.
    If the check is successful, it will return ``None`` for the error message
    and ``True`` for the passed check.

    :param url: The image url to be checked.
    """
    img_info = get_image_info(file)
    error = None

    if img_info is None:
        error = "Couldn't check image info."
        return error, False

    if (
        current_app.config["AVATAR_EXTENSIONS"]
        and img_info["content_type"] not in current_app.config["AVATAR_EXTENSIONS"]
    ):
        error = "Image type {} is not allowed. Allowed types are: {}".format(
            img_info["content_type"],
            ", ".join(current_app.config["AVATAR_EXTENSIONS"]),  # pyright: ignore[reportUnknownArgumentType]
        )
        return error, False

    if (
        flaskbb_config["AVATAR_WIDTH"]
        and img_info["width"] > flaskbb_config["AVATAR_WIDTH"]
    ):
        error = "Image is too wide! {}px width is allowed.".format(
            flaskbb_config["AVATAR_WIDTH"]
        )
        return error, False

    if (
        flaskbb_config["AVATAR_HEIGHT"]
        and img_info["height"] > flaskbb_config["AVATAR_HEIGHT"]
    ):
        error = "Image is too high! {}px height is allowed.".format(
            flaskbb_config["AVATAR_HEIGHT"]
        )
        return error, False

    return error, True
