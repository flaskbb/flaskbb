"""
flaskbb.utils.helpers
~~~~~~~~~~~~~~~~~~~~~

A few helpers that are used by flaskbb

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import os
import uuid
from pathlib import Path

from flask import current_app, Flask
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


def get_attachment_upload_path() -> str:
    if current_app.config.get("ATTACHMENT_UPLOAD_PATH", None) is None:
        return os.path.join(
            current_app.static_folder or "static", "uploads", "attachments"
        )
    return current_app.config["ATTACHMENT_UPLOAD_PATH"]


def make_attachment_filename() -> str:
    # nothing of the name the uploader chose ends up on disk - not even the
    # extension. The name is kept in the database (original_filename) and the
    # type in content_type, so the stored name can stay a plain uuid
    return uuid.uuid4().hex


def get_attachment_disk_path(post_id: int, stored_filename: str) -> str:
    return os.path.join(get_attachment_upload_path(), str(post_id), stored_filename)


def delete_attachment_file(post_id: int, stored_filename: str):
    file_path = Path(get_attachment_upload_path(), str(post_id), stored_filename)
    try:
        file_path.unlink(missing_ok=True)
        try:
            file_path.parent.rmdir()
        except OSError:
            pass
    except PermissionError:
        logger.error(
            f"You do not have permission to delete this file: {stored_filename}"
        )
    except IsADirectoryError:
        logger.error(
            f"The specified path is a directory, not a file: {stored_filename}"
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


def scan_attachment_storage() -> dict[str, dict[str, float]]:
    """Maps every directory below the attachment upload path to the files it
    holds and their modification times.
    """
    root = get_attachment_upload_path()
    storage: dict[str, dict[str, float]] = {}
    if not os.path.isdir(root):
        return storage

    with os.scandir(root) as entries:
        for entry in entries:
            # only the <post_id> directories flaskbb creates itself are
            # scanned - symlinks are never followed
            if not entry.is_dir(follow_symlinks=False):
                continue

            with os.scandir(entry.path) as files:
                storage[entry.name] = {
                    file.name: file.stat().st_mtime
                    for file in files
                    if file.is_file(follow_symlinks=False)
                }

    return storage


def remove_orphan_attachment_files(
    storage: dict[str, dict[str, float]],
    known: dict[str, set[str]],
    cutoff: float | None = None,
) -> int:
    """Deletes every file in ``storage`` that no attachment row claims and
    prunes the directories that end up empty.

    ``known`` maps a post id (as a string) to the filenames its attachments
    still reference. Files newer than ``cutoff`` are kept - they may belong to
    an upload whose row has not been committed yet.
    """
    root = Path(get_attachment_upload_path())
    removed = 0

    for dirname, files in storage.items():
        keep = known.get(dirname, set())
        for filename, mtime in files.items():
            if filename in keep or (cutoff is not None and mtime > cutoff):
                continue

            (root / dirname / filename).unlink(missing_ok=True)
            removed += 1

        try:
            (root / dirname).rmdir()
        except OSError:
            pass

    return removed


def create_upload_directory(app: Flask):
    with app.app_context():
        for upload_path in (get_avatar_upload_path(), get_attachment_upload_path()):
            if os.path.exists(upload_path):
                continue

            logger.info(f"Creating upload path: {upload_path}")
            os.makedirs(upload_path, exist_ok=True)


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
