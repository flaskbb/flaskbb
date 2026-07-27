"""Tests for the attachment management views.

The views are invoked directly rather than over HTTP, which skips the
blueprint's ``login_fresh()`` gate - that gate is orthogonal to what is
tested here.
"""

import datetime
import os

import pytest
from flask import get_flashed_messages
from flask_login import login_user, logout_user

from flaskbb.forum.models import Attachment, Post
from flaskbb.management import views
from flaskbb.utils.helpers import time_utcnow


@pytest.fixture
def no_csrf(application):
    previous = application.config.get("WTF_CSRF_ENABLED", True)
    application.config["WTF_CSRF_ENABLED"] = False
    yield
    application.config["WTF_CSRF_ENABLED"] = previous


def _post(view, actor, json=None, **kwargs):
    with views.current_app.test_request_context(method="POST", json=json):
        login_user(actor)
        response = view(**kwargs)
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    return response, messages


def _backdate(attachment):
    """Moves an attachment out of the cleanup grace window."""
    attachment.date_created = time_utcnow() - datetime.timedelta(hours=1)
    attachment.save()


def _make_stale_file(path, name):
    path.mkdir(parents=True, exist_ok=True)
    stray = path / name
    stray.write_bytes(b"stray")
    old = (time_utcnow() - datetime.timedelta(hours=1)).timestamp()
    os.utime(stray, (old, old))
    return stray


def test_delete_attachment_removes_row_and_file(
    default_settings, moderator_user, attachment, attachment_upload_path
):
    on_disk = attachment_upload_path / str(attachment.post_id) / attachment.filename
    view = views.DeleteAttachment.as_view("delete_attachment")

    response, messages = _post(view, moderator_user, attachment_id=attachment.id)

    assert response.status_code == 302
    assert ("success", "Attachment deleted.") in messages
    assert Attachment.query.count() == 0
    assert not on_disk.exists()
    # the per-post directory is pruned once it empties
    assert not on_disk.parent.exists()


def test_bulk_delete_attachments(
    default_settings, moderator_user, attachment, attachment_upload_path
):
    on_disk = attachment_upload_path / str(attachment.post_id) / attachment.filename
    view = views.DeleteAttachment.as_view("delete_attachment")

    response, _messages = _post(view, moderator_user, json={"ids": [attachment.id]})

    payload = response.get_json()
    assert payload["status"] == 200
    assert payload["data"] == [
        {
            "id": attachment.id,
            "type": "delete",
            "reverse": False,
            "reverse_name": None,
            "reverse_url": None,
        }
    ]
    assert Attachment.query.count() == 0
    assert not on_disk.exists()


def test_moderator_cannot_cleanup_or_purge(
    default_settings, moderator_user, attachment
):
    for view_cls in (views.CleanupAttachments, views.PurgeAttachments):
        response, messages = _post(view_cls.as_view("attachments"), moderator_user)

        assert response.status_code == 302
        assert ("danger", "You are not allowed to manage attachments") in messages

    assert Attachment.query.count() == 1


def test_cleanup_removes_row_with_missing_file(
    default_settings, admin_user, attachment, attachment_upload_path
):
    _backdate(attachment)
    (attachment_upload_path / str(attachment.post_id) / attachment.filename).unlink()

    _response, messages = _post(
        views.CleanupAttachments.as_view("cleanup_attachments"), admin_user
    )

    assert Attachment.query.count() == 0
    assert (
        "success",
        "Removed 1 attachment(s) with a missing file and 0 orphaned file(s).",
    ) in messages


def test_cleanup_removes_orphan_file(
    default_settings, admin_user, attachment, attachment_upload_path
):
    _backdate(attachment)
    orphan_dir = attachment_upload_path / "999"
    orphan = _make_stale_file(orphan_dir, "stray")

    _response, messages = _post(
        views.CleanupAttachments.as_view("cleanup_attachments"), admin_user
    )

    assert not orphan.exists()
    assert not orphan_dir.exists()
    # the attachment that is still backed by a file is left alone
    assert Attachment.query.count() == 1
    assert (
        attachment_upload_path / str(attachment.post_id) / attachment.filename
    ).exists()
    assert (
        "success",
        "Removed 0 attachment(s) with a missing file and 1 orphaned file(s).",
    ) in messages


def test_cleanup_keeps_recent_files_and_rows(
    default_settings, admin_user, attachment, attachment_upload_path
):
    """A file written seconds ago may belong to an upload whose row is not
    committed yet, and a row created seconds ago may be waiting for its file.
    """
    fresh_dir = attachment_upload_path / "999"
    fresh_dir.mkdir()
    fresh = fresh_dir / "stray"
    fresh.write_bytes(b"stray")

    (attachment_upload_path / str(attachment.post_id) / attachment.filename).unlink()

    _response, _messages = _post(
        views.CleanupAttachments.as_view("cleanup_attachments"), admin_user
    )

    assert fresh.exists()
    assert Attachment.query.count() == 1


def test_cleanup_leaves_nested_directories_alone(
    default_settings, admin_user, attachment, attachment_upload_path
):
    """Only the flat <post_id>/<filename> layout flaskbb creates itself is
    reconciled - anything nested is never descended into or removed.
    """
    nested = attachment_upload_path / "abc" / "sub"
    nested.mkdir(parents=True)
    (nested / "keep").write_bytes(b"keep")

    _post(views.CleanupAttachments.as_view("cleanup_attachments"), admin_user)

    assert (nested / "keep").exists()


def test_purge_removes_everything(
    default_settings, admin_user, attachment, topic, attachment_upload_path
):
    second_post = Post(content="Another post")
    second_post.save(topic=topic, user=attachment.user)
    second_dir = attachment_upload_path / str(second_post.id)
    second_dir.mkdir()
    (second_dir / "cafebabe").write_bytes(b"another file")
    Attachment(
        post_id=second_post.id,
        user_id=attachment.user_id,
        filename="cafebabe",
        original_filename="other.png",
        content_type="image/png",
        size=12,
    ).save()

    orphan = _make_stale_file(attachment_upload_path / "999", "stray")

    _response, messages = _post(
        views.PurgeAttachments.as_view("purge_attachments"), admin_user
    )

    assert Attachment.query.count() == 0
    assert not orphan.exists()
    # every file the rows pointed at went with them, not just the rows
    assert list(attachment_upload_path.iterdir()) == []
    assert (
        "success",
        "Purged 2 attachment(s) and 1 leftover file(s).",
    ) in messages


def test_attachments_list_renders_for_moderator(
    default_settings, no_csrf, moderator_user, attachment
):
    view = views.ManageAttachments.as_view("attachments")

    with views.current_app.test_request_context():
        login_user(moderator_user)
        response = view()
        logout_user()

    assert attachment.original_filename in response
    assert attachment.user.username in response
    assert '"/admin/attachments/{}/delete"'.format(attachment.id) in response
    # admin-only actions stay out of a moderator's page
    assert "/admin/attachments/purge" not in response
    assert "/admin/attachments/cleanup" not in response


def test_attachments_list_renders_admin_actions(
    default_settings, no_csrf, admin_user, attachment
):
    view = views.ManageAttachments.as_view("attachments")

    with views.current_app.test_request_context():
        login_user(admin_user)
        response = view()
        logout_user()

    assert "/admin/attachments/purge" in response
    assert "/admin/attachments/cleanup" in response


def test_attachments_list_flags_missing_file(
    default_settings, no_csrf, admin_user, attachment, attachment_upload_path
):
    (attachment_upload_path / str(attachment.post_id) / attachment.filename).unlink()
    view = views.ManageAttachments.as_view("attachments")

    with views.current_app.test_request_context():
        login_user(admin_user)
        response = view()
        logout_user()

    assert "file missing" in response


def test_attachments_search_matches_filename_and_uploader(
    default_settings, no_csrf, admin_user, attachment
):
    view = views.ManageAttachments.as_view("attachments")

    for query in (attachment.original_filename[:5], attachment.user.username):
        with views.current_app.test_request_context(
            method="POST", data={"search_query": query}
        ):
            login_user(admin_user)
            response = view()
            logout_user()

        assert attachment.original_filename in response

    with views.current_app.test_request_context(
        method="POST", data={"search_query": "nothingmatchesthis"}
    ):
        login_user(admin_user)
        response = view()
        logout_user()

    assert "No attachments found." in response
