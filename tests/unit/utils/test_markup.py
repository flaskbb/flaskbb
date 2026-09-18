import pytest
from flask import current_app, url_for
from flask_login import login_user
from flaskbb.markup import (
    DEFAULT_PLUGINS,
    FlaskBBRenderer,
    make_renderer,
    nonpost_renderer,
    POST_PLUGINS,
)
from flaskbb.settings import flaskbb_config
from flaskbb.utils.helpers import format_quote

markdown = make_renderer([FlaskBBRenderer], DEFAULT_PLUGINS)


def test_userify():
    # user link rendering plugin
    with current_app.test_request_context():
        result = markdown("@sh4nks is developing flaskbb.")
        result2 = markdown("Hello, @sh4nks is developing @flaskbb @wow.")

    assert all(substring in result for substring in ("/user/sh4nks"))
    assert all(substring in result2 for substring in ("/user/sh4nks", "/user/flaskbb", "/user/wow"))


def test_highlighting():
    # custom block code with pygments highlighting (jus)
    b_plain = """
```
print("Hello World")
```
"""
    b_plain_lang = """
```python
print("Hello World")
```
"""

    assert "<pre>" in markdown(b_plain)
    assert "highlight" in markdown(b_plain_lang)

    # typo in language
    bad_language = """
```notpython
print("Hello World")
```
"""

    bad_language_render = markdown(bad_language)
    assert "<pre>" in bad_language_render
    assert "highlight" not in bad_language_render


EXTERNAL_LINK_SOURCES = [
    "[external](http://example.com/page)",
    "http://example.com/page",
]
INTERNAL_LINK_SOURCES = [
    "[internal](http://localhost:5000/topic/1)",
    "http://localhost:5000/topic/1",
]


@pytest.mark.parametrize("source", EXTERNAL_LINK_SOURCES)
def test_external_link_new_tab_on(source, database, default_settings, application):
    flaskbb_config["OPEN_LINKS_IN_NEW_TAB"] = True

    with application.test_request_context():
        result = markdown(source)

    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer nofollow"' in result


@pytest.mark.parametrize("source", EXTERNAL_LINK_SOURCES)
def test_external_link_new_tab_off(source, database, default_settings, application):
    with application.test_request_context():
        result = markdown(source)

    assert 'target="_blank"' not in result
    assert 'rel="noopener noreferrer nofollow"' in result


@pytest.mark.parametrize("source", INTERNAL_LINK_SOURCES)
@pytest.mark.parametrize("new_tab_setting", [True, False])
def test_internal_link_is_never_rewritten(
    source, new_tab_setting, database, default_settings, application
):
    flaskbb_config["OPEN_LINKS_IN_NEW_TAB"] = new_tab_setting

    with application.test_request_context():
        result = markdown(source)

    assert 'target="_blank"' not in result
    assert "rel=" not in result


def test_user_override_true_wins_over_system_default_off(user, database, application):
    user.open_links_in_new_tab = True
    user.save()

    with application.test_request_context():
        login_user(user)
        result = markdown("http://example.com/page")

    assert 'target="_blank"' in result


def test_user_override_false_wins_over_system_default_on(
    user, database, default_settings, application
):
    flaskbb_config["OPEN_LINKS_IN_NEW_TAB"] = True
    user.open_links_in_new_tab = False
    user.save()

    with application.test_request_context():
        login_user(user)
        result = markdown("http://example.com/page")

    assert 'target="_blank"' not in result
    assert 'rel="noopener noreferrer nofollow"' in result


def test_user_inherits_system_default_when_override_unset(
    user, database, default_settings, application
):
    flaskbb_config["OPEN_LINKS_IN_NEW_TAB"] = True

    with application.test_request_context():
        login_user(user)
        result = markdown("http://example.com/page")

    assert 'target="_blank"' in result


post_markdown = make_renderer([FlaskBBRenderer], POST_PLUGINS)


def attribution(username, post_id=None):
    line = f"**[{username}]({url_for('user.profile', username=username)}) wrote:**"
    if post_id is not None:
        line += f" [view post]({url_for('forum.view_post', post_id=post_id)})"
    return line


def test_quote_header_links_author_and_quoted_post(database, default_settings, application):
    with application.test_request_context():
        result = post_markdown(f"> {attribution('alice', 7)}\n>\n> hello\n")
        profile_url = url_for("user.profile", username="alice")
        post_url = url_for("forum.view_post", post_id=7)

    assert '<blockquote class="post-quote">' in result
    assert f'<a class="post-quote-author" href="{profile_url}">alice</a> wrote:</span>' in result
    assert f'<a class="post-quote-source" href="{post_url}"' in result
    assert "view post" not in result
    assert "<p>hello</p>" in result


def test_quote_header_without_post_link(database, default_settings, application):
    with application.test_request_context():
        result = post_markdown(f"> {attribution('alice')}\n>\n> hello\n")

    assert '<header class="post-quote-header">' in result
    assert "post-quote-source" not in result


def test_quote_header_keeps_content_on_the_attribution_paragraph(
    database, default_settings, application
):
    with application.test_request_context():
        result = post_markdown(f"> {attribution('alice', 7)}\n> hello\n")

    assert '<header class="post-quote-header">' in result
    assert "<p>hello</p>" in result


def test_legacy_quote_attribution_moves_into_the_quote(database, default_settings, application):
    with application.test_request_context():
        result = post_markdown(f"{attribution('alice')}\n> hello\n")

    assert result.startswith('<blockquote class="post-quote">')
    assert result.count(">alice</a>") == 1
    assert "<p><strong>" not in result


def test_nested_quotes_get_their_own_headers(database, default_settings, application):
    source = (
        f"> {attribution('alice', 2)}\n>\n"
        f"> > {attribution('bob', 1)}\n> >\n> > first\n>\n"
        "> second\n"
    )

    with application.test_request_context():
        result = post_markdown(source)

    assert result.count('<blockquote class="post-quote">') == 2
    assert result.index(">alice</a>") < result.index(">bob</a>")


def test_nested_legacy_quotes_get_their_own_headers(database, default_settings, application):
    source = f"{attribution('alice')}\n> {attribution('bob')}\n> > first\n>\n> second\n"

    with application.test_request_context():
        result = post_markdown(source)

    assert result.count('<blockquote class="post-quote">') == 2
    assert result.index(">alice</a>") < result.index(">bob</a>")


def test_quote_header_names_the_linked_user_not_the_link_text(
    database, default_settings, application
):
    with application.test_request_context():
        profile_url = url_for("user.profile", username="bob")
        result = post_markdown(f"> **[admin]({profile_url}) wrote:**\n>\n> hello\n")

    assert ">bob</a> wrote:" in result
    assert "admin" not in result


@pytest.mark.parametrize(
    "source",
    [
        "> **[alice](http://example.com/user/alice) wrote:**\n>\n> hello\n",
        "> **[alice](/topic/1) wrote:**\n>\n> hello\n",
        "> **[alice](/user/alice) says:**\n>\n> hello\n",
        "> **[alice](/user/alice) wrote:** hello\n",
        "> hello\n",
    ],
)
def test_quote_without_valid_attribution_renders_plain(
    source, database, default_settings, application
):
    with application.test_request_context():
        result = post_markdown(source)

    assert "<blockquote>" in result
    assert "post-quote" not in result


def test_quote_headers_are_only_rendered_in_posts(database, default_settings, application):
    with application.test_request_context():
        result = markdown(f"> {attribution('alice', 7)}\n>\n> hello\n")

    assert "post-quote" not in result


def test_formatted_quote_renders_with_header(database, default_settings, application):
    with application.test_request_context():
        post_url = url_for("forum.view_post", post_id=3)
        result = post_markdown(format_quote("alice", "hello\n> nested", post_url))

    assert result.count('<blockquote class="post-quote">') == 1
    assert "post-quote-source" in result


def test_nonpost_renderer_applies_markdown_plugins(application):
    render = nonpost_renderer(application)

    with application.test_request_context():
        result = render("~~strike~~\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")

    assert "<del>strike</del>" in result
    assert "<table>" in result
