import pytest
from flask import current_app
from flask_login import login_user
from flaskbb.core.settings import flaskbb_config
from flaskbb.markup import DEFAULT_PLUGINS, FlaskBBRenderer, make_renderer

markdown = make_renderer([FlaskBBRenderer], DEFAULT_PLUGINS)


def test_userify():
    # user link rendering plugin
    with current_app.test_request_context():
        result = markdown("@sh4nks is developing flaskbb.")
        result2 = markdown("Hello, @sh4nks is developing @flaskbb @wow.")

    assert all(substring in result for substring in ("/user/sh4nks"))
    assert all(
        substring in result2
        for substring in ("/user/sh4nks", "/user/flaskbb", "/user/wow")
    )


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
