"""Tests for the attachment serving route."""


def test_serves_image_attachment_inline(application, attachment, default_settings):
    with application.test_client() as client:
        resp = client.get(
            "/uploads/attachments/{}/{}".format(attachment.filename, "test-image.png")
        )

    assert resp.status_code == 200
    assert resp.data == b"not really a png"
    assert "attachment" not in resp.headers.get("Content-Disposition", "")
    # the stored name has no extension, so this comes from content_type
    assert resp.headers["Content-Type"].startswith("image/png")


def test_serves_non_image_attachment_as_download(
    application, attachment, default_settings
):
    attachment.content_type = "application/pdf"
    attachment.save()

    with application.test_client() as client:
        resp = client.get(
            "/uploads/attachments/{}/{}".format(attachment.filename, "whatever.pdf")
        )

    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("application/pdf")
    disposition = resp.headers["Content-Disposition"]
    assert disposition.startswith("attachment")
    assert "test image.png" in disposition


def test_display_name_segment_does_not_identify_the_attachment(
    application, attachment, default_settings
):
    """Only the stored filename is looked up - the display segment is
    cosmetic, and the sequential id is not a valid key anymore."""
    with application.test_client() as client:
        any_name = client.get(
            "/uploads/attachments/{}/{}".format(attachment.filename, "anything.png")
        )
        by_id = client.get(
            "/uploads/attachments/{}/{}".format(attachment.id, "test-image.png")
        )

    assert any_name.status_code == 200
    assert by_id.status_code == 404


def test_unknown_attachment_404s(application, database, default_settings):
    with application.test_client() as client:
        resp = client.get("/uploads/attachments/0123456789abcdef/nope.png")

    assert resp.status_code == 404


def test_too_large_request_flashes_the_limit(application, database, default_settings):
    """413 is raised by Flask before the view runs, so the user only learns
    the limit from the error handler."""
    original = application.config["MAX_CONTENT_LENGTH"]
    application.config["MAX_CONTENT_LENGTH"] = 2048
    try:
        with application.test_client() as client:
            resp = client.post("/1/topic/new", data={"content": "x" * 4096})
            with client.session_transaction() as session:
                flashes = session["_flashes"]
    finally:
        application.config["MAX_CONTENT_LENGTH"] = original

    assert resp.status_code == 302
    category, message = flashes[0]
    assert category == "danger"
    assert "2.0 kB" in message
