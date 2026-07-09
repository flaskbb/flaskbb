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
from pathlib import Path
from typing import TYPE_CHECKING, override

from flask import Flask, current_app
from flask_wtf.file import FileStorage
from PIL import ImageFile
from werkzeug.utils import secure_filename

from flaskbb.core.settings import flaskbb_config

logger = logging.getLogger(__name__)


def get_avatar_upload_path() -> str:
    if current_app.config.get("AVATAR_UPLOAD_PATH", None) is None:
        return os.path.join(current_app.static_folder or "static", "uploads", "avatar")
    return current_app.config["AVATAR_UPLOAD_PATH"]


def get_avatar_filename(username: str, filename: str | None) -> str:
    if filename:
        file_ext = os.path.splitext(filename)[1]
        return secure_filename("avatar_" + username + file_ext)
    return secure_filename("avatar_" + username)


def delete_avatar_file(filename: str | None):
    if not filename:
        logger.warning("avatar filename not provided - nothing to delete.")
        return

    file_path = Path(get_avatar_upload_path(), filename)
    try:
        file_path.unlink(missing_ok=True)
    except PermissionError:
        logger.error(f"You do not have permission to delete this file: {filename}")
    except IsADirectoryError:
        logger.error(f"The specified path is a directory, not a file: {filename}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


def create_upload_directory(app: Flask):
    with app.app_context():
        avatar_upload_path = get_avatar_upload_path()

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
