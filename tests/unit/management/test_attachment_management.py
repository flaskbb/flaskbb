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
from flaskbb.forum.models import Attachment, Forum, Post, Topic
from flaskbb.management import views
from flaskbb.utils.helpers import time_utcnow
from werkzeug.exceptions import NotFound


@pytest.fixture
def no_csrf(application):
    previous = application.config.get("WTF_CSRF_ENABLED", True)
    application.config["WTF_CSRF_ENABLED"] = False
    yield
    application.config["WTF_CSRF_ENABLED"] = previous


@pytest.fixture
def private_attachment(category, default_groups, admin_user, attachment_upload_path):
    forum = Forum(title="Staff Forum", category_id=category.id)
    forum.save(groups=[admin_user.primary_group])
    topic = Topic(title="Staff Topic")
    topic.save(forum=forum, user=admin_user, post=Post(content="Staff Content"))

    post_dir = attachment_upload_path / str(topic.first_post_id)
    post_dir.mkdir()
    (post_dir / "cafebabe").write_bytes(b"staff only")

    return Attachment(
        post_id=topic.first_post_id,
        user_id=admin_user.id,
        filename="cafebabe",
        original_filename="staff notes.txt",
        content_type="text/plain",
        size=10,
    ).save()


def _post(view, actor, data=None, **kwargs):
    with views.current_app.test_request_context(method="POST", data=data):
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

    response, messages = _post(view, moderator_user, data={"rowid": [str(attachment.id)]})

    assert response.status_code == 302
    assert ("success", "1 attachments deleted.") in messages
    assert Attachment.query.count() == 0
    assert not on_disk.exists()


def test_moderator_cannot_cleanup_or_purge(default_settings, moderator_user, attachment):
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

    _response, messages = _post(views.CleanupAttachments.as_view("cleanup_attachments"), admin_user)

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

    _response, messages = _post(views.CleanupAttachments.as_view("cleanup_attachments"), admin_user)

    assert not orphan.exists()
    assert not orphan_dir.exists()
    # the attachment that is still backed by a file is left alone
    assert Attachment.query.count() == 1
    assert (attachment_upload_path / str(attachment.post_id) / attachment.filename).exists()
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

    _response, messages = _post(views.PurgeAttachments.as_view("purge_attachments"), admin_user)

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
    assert f'"/admin/attachments/{attachment.id}/delete"' in response
    # admin-only actions stay out of a moderator's page
    assert "/admin/attachments/purge" not in response
    assert "/admin/attachments/cleanup" not in response


def test_attachments_list_renders_admin_actions(default_settings, no_csrf, admin_user, attachment):
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
        with views.current_app.test_request_context(method="POST", data={"search_query": query}):
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


def _list(actor, search_query=None):
    view = views.ManageAttachments.as_view("attachments")
    method, data = ("POST", {"search_query": search_query}) if search_query else ("GET", None)

    with views.current_app.test_request_context(method=method, data=data):
        login_user(actor)
        response = view()
        logout_user()

    return response


def test_attachments_list_hides_restricted_forums(
    default_settings, no_csrf, moderator_user, attachment, private_attachment
):
    response = _list(moderator_user)

    assert attachment.original_filename in response
    assert private_attachment.original_filename not in response
    assert private_attachment.filename not in response
    assert "Staff Topic" not in response


def test_attachments_search_hides_restricted_forums(
    default_settings, no_csrf, moderator_user, private_attachment
):
    for query in ("staff notes", private_attachment.user.username):
        response = _list(moderator_user, query)

        assert private_attachment.original_filename not in response


def test_attachments_list_shows_restricted_forum_to_its_group(
    default_settings, no_csrf, admin_user, attachment, private_attachment
):
    response = _list(admin_user)

    assert attachment.original_filename in response
    assert private_attachment.original_filename in response


def test_delete_refuses_attachment_of_restricted_forum(
    default_settings, moderator_user, private_attachment, attachment_upload_path
):
    on_disk = attachment_upload_path / str(private_attachment.post_id) / private_attachment.filename
    view = views.DeleteAttachment.as_view("delete_attachment")

    with pytest.raises(NotFound):
        _post(view, moderator_user, attachment_id=private_attachment.id)

    assert Attachment.query.count() == 1
    assert on_disk.exists()


def test_bulk_delete_skips_attachments_of_restricted_forums(
    default_settings, moderator_user, attachment, private_attachment, attachment_upload_path
):
    on_disk = attachment_upload_path / str(private_attachment.post_id) / private_attachment.filename
    view = views.DeleteAttachment.as_view("delete_attachment")

    _, messages = _post(
        view, moderator_user, data={"rowid": [attachment.id, private_attachment.id]}
    )

    assert ("success", "1 attachments deleted.") in messages
    assert [a.id for a in Attachment.query.all()] == [private_attachment.id]
    assert on_disk.exists()
