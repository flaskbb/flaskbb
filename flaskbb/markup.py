# -*- coding: utf-8 -*-
"""
    flaskbb.utils.markup
    ~~~~~~~~~~~~~~~~~~~~

    A module for all markup related stuff.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

import mistune
from flask import url_for
from markupsafe import Markup
from pluggy import HookimplMarker
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

impl = HookimplMarker('flaskbb')

logger = logging.getLogger(__name__)

_re_user = r'(?i)@(\w+)'


def parse_user_link(inline, match, state):
    url = url_for("user.profile", username=match.group(1), _external=False)
    return 'link', url, match.group(0)


def plugin_userify(md):
    """Mistune plugin that transforms @username references to links."""
    md.inline.register_rule('flaskbb_user_link', _re_user, parse_user_link)
    md.inline.rules.append('flaskbb_user_link')


DEFAULT_PLUGINS = [
    "url",
    "strikethrough",
    "spoiler",
    "subscript",
    "superscript",
    "insert",
    "mark",
    "abbr",
    "def_list",
    "task_lists",
    "table",
    "footnotes",
]


class FlaskBBRenderer(mistune.HTMLRenderer):
    """Mistune renderer that uses pygments to apply code highlighting."""

    def __init__(self, **kwargs):
        super(FlaskBBRenderer, self).__init__(**kwargs)

    def block_code(self, code, info=None):
        if info:
            try:
                lexer = get_lexer_by_name(info, stripall=True)
            except ClassNotFound:
                lexer = None
        else:
            lexer = None
        if not lexer:
            return "\n<pre><code>%s</code></pre>\n" % mistune.escape(code)
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)


@impl
def flaskbb_load_post_markdown_class():
    return FlaskBBRenderer


@impl
def flaskbb_load_nonpost_markdown_class():
    return FlaskBBRenderer


@impl
def flaskbb_jinja_directives(app):
    render_classes = app.pluggy.hook.flaskbb_load_post_markdown_class(app=app)
    plugins = DEFAULT_PLUGINS[:]
    app.pluggy.hook.flaskbb_load_post_markdown_plugins(
        plugins=plugins,
        app=app
    )
    app.jinja_env.filters['markup'] = make_renderer(render_classes, plugins)

    render_classes = app.pluggy.hook.flaskbb_load_nonpost_markdown_class(
        app=app
    )
    plugins = DEFAULT_PLUGINS[:]
    plugins = app.pluggy.hook.flaskbb_load_nonpost_markdown_plugins(
        plugins=plugins,
        app=app
    )
    app.jinja_env.filters['nonpost_markup'] = make_renderer(
        render_classes,
        plugins
    )


def make_renderer(classes, plugins):
    RenderCls = type('FlaskBBRenderer', tuple(classes), {})

    markup = mistune.create_markdown(
        renderer=RenderCls(),
        plugins=plugins,
        escape=True,
        hard_wrap=True
    )
    return lambda text: Markup(markup(text))
