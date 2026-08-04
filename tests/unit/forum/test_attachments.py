"""Tests for post attachment uploads."""

from io import BytesIO

import pytest
from flask_login import login_user, logout_user
from flaskbb.forum.forms import ReplyForm
from flaskbb.forum.models import Attachment
from flaskbb.forum.utils import parse_attachment_types
from flaskbb.utils.settings import flaskbb_config
from werkzeug.datastructures import FileStorage, MultiDict


def test_parse_attachment_types():
    assert parse_attachment_types("png, jpg, jpeg, gif, pdf") == {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "pdf",
    }
    assert parse_attachment_types(" .PNG , Jpg,, ") == {"png", "jpg"}
    assert parse_attachment_types("") == set()
    assert parse_attachment_types(None) == set()


def _upload(filename, content=b"x"):
    return FileStorage(stream=BytesIO(content), filename=filename)


def _reply_form(files, obj=None, **formdata):
    data = MultiDict(formdata)
    for file in files:
        data.add("new_attachments", file)
    kwargs = {"formdata": data, "meta": {"csrf": False}}
    if obj is not None:
        kwargs["obj"] = obj
    return ReplyForm(**kwargs)


@pytest.fixture
def member_request(application, user, attachment_upload_path, default_settings):
    # logout before the context is popped: login_user writes g._login_user
    # onto the package-scoped app context, which outlives this request
    # context and would leak a detached user into later tests
    with application.test_request_context():
        login_user(user)
        yield user
        logout_user()


def test_reply_form_saves_attachment(member_request, topic, attachment_upload_path):
    user = member_request
    form = _reply_form([_upload("a.png")], content="test content")

    assert form.validate()
    post = form.save(user, topic)

    assert len(post.attachments) == 1
    attachment = post.attachments[0]
    assert attachment.original_filename == "a.png"
    # nothing of the uploaded name lands on disk, not even the extension
    assert "." not in attachment.filename
    assert attachment.size == 1
    assert (attachment_upload_path / str(post.id) / attachment.filename).exists()


def test_reply_form_rejects_bad_extension(member_request, topic):
    form = _reply_form([_upload("evil.exe")], content="test content")

    assert not form.validate()
    assert "not allowed" in form.new_attachments.errors[0]


def test_reply_form_rejects_too_large(member_request, topic):
    flaskbb_config["ATTACHMENT_MAX_SIZE"] = 1
    form = _reply_form([_upload("big.png", b"x" * 2048)], content="test content")

    assert not form.validate()
    assert "bigger" in form.new_attachments.errors[0]


def test_reply_form_rejects_when_disabled(member_request, topic):
    flaskbb_config["ATTACHMENTS_ENABLED"] = False
    form = _reply_form([_upload("a.png")], content="test content")

    assert not form.validate()
    assert "disabled" in form.new_attachments.errors[0]


def test_reply_form_rejects_too_many(member_request, topic):
    files = [_upload(f"a{i}.png") for i in range(6)]
    form = _reply_form(files, content="test content")

    assert not form.validate()
    assert "per post" in form.new_attachments.errors[0]


def test_reply_form_rejects_without_permission(
    application, user, topic, attachment_upload_path, default_settings
):
    user.primary_group.postattachment = False
    user.primary_group.save()
    user.invalidate_cache()

    with application.test_request_context(f"/topic/{topic.id}"):
        login_user(user)
        form = _reply_form([_upload("a.png")], content="test content")

        assert not form.validate()
        assert "not allowed to upload" in form.new_attachments.errors[0]
        logout_user()


def test_edit_form_deletes_attachment(
    member_request, topic, attachment, attachment_upload_path
):
    user = member_request
    post = topic.first_post
    file_path = attachment_upload_path / str(post.id) / attachment.filename
    assert file_path.exists()

    form = _reply_form(
        [],
        obj=post,
        content="edited content",
        delete_attachments=str(attachment.id),
    )
    assert form.delete_attachments.choices == [
        (attachment.id, attachment.original_filename)
    ]

    assert form.validate()
    form.save(user, topic)

    assert post.attachments == []
    assert Attachment.get_by(id=attachment.id) is None
    assert not file_path.exists()
