from flaskbb.forum import views


def _preview(text, **kwargs):
    with views.current_app.test_request_context(method="POST", data={"text": text}):
        return views.MarkdownPreview.as_view("markdown_preview")(**kwargs)


def test_preview_renders_post_markdown(default_settings):
    assert "<strong>bold</strong>" in _preview("**bold**")


def test_preview_includes_the_markdown_plugins(default_settings):
    assert "<del>gone</del>" in _preview("~~gone~~")


def test_preview_escapes_html(default_settings):
    preview = _preview("<script>alert(1)</script>")

    assert "<script>" not in preview
    assert "&lt;script&gt;" in preview


def test_preview_renders_nonpost_markdown(default_settings):
    assert "<em>italic</em>" in _preview("*italic*", mode="nonpost")
