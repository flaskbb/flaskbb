import pytest
from flask import render_template, render_template_string
from flask_wtf import FlaskForm
from flaskbb.extensions import pluggy
from flaskbb.utils.helpers import render_template as render_themed_template
from pluggy import HookimplMarker
from wtforms import TextAreaField

hookimpl = HookimplMarker("flaskbb")

CHEATSHEET = "<h2>Spoilers</h2><p>||hidden||</p>"
TOOLBAR_BUTTON = '<md-custom data-md-prefix="||">spoiler</md-custom>'
SCRIPT = '<script src="/spoiler/static/spoiler.js"></script>'


class EditorPlugin:
    @hookimpl
    def flaskbb_tpl_markdown_cheatsheet(self):
        return CHEATSHEET

    @hookimpl
    def flaskbb_tpl_markdown_toolbar_buttons(self):
        return TOOLBAR_BUTTON

    @hookimpl
    def flaskbb_tpl_scripts(self):
        return SCRIPT


class EditorForm(FlaskForm):
    content = TextAreaField("Content")


@pytest.fixture
def editor_plugin():
    plugin = EditorPlugin()
    pluggy.register(plugin, "test_editor_plugin")

    yield plugin

    pluggy.unregister(plugin)


def render_editor():
    return render_template_string(
        "{% from '_macros/form.html' import render_editor_field %}"
        "{{ render_editor_field(form.content) }}",
        form=EditorForm(),
    )


def render_cheatsheet():
    return render_template("_partials/editor_help.html")


def test_cheatsheet_renders_without_plugins(request_context, default_settings):
    assert "Markdown Cheatsheet" in render_cheatsheet()


def test_cheatsheet_renders_plugin_entry(request_context, default_settings, editor_plugin):
    rendered = render_cheatsheet()

    assert CHEATSHEET in rendered
    assert rendered.index(CHEATSHEET) < rendered.index('class="credit')


def test_toolbar_renders_without_plugins(request_context, default_settings):
    assert "<md-bold" in render_editor()


def test_toolbar_renders_plugin_button(request_context, default_settings, editor_plugin):
    rendered = render_editor()

    assert TOOLBAR_BUTTON in rendered
    # inside the toolbar, after the built-in buttons, before the preview button
    assert rendered.index("<markdown-toolbar") < rendered.index(TOOLBAR_BUTTON)
    assert rendered.index("<md-mention") < rendered.index(TOOLBAR_BUTTON)
    assert rendered.index(TOOLBAR_BUTTON) < rendered.index("preview-btn")


def test_toolbar_hook_is_markup(request_context, default_settings, editor_plugin):
    assert "&lt;md-custom" not in render_editor()


def test_layout_renders_plugin_script(request_context, default_settings, editor_plugin):
    rendered = render_themed_template("layout.html")

    assert SCRIPT in rendered
    assert rendered.index("app.js") < rendered.index(SCRIPT)
