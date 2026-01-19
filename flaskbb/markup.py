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
from mistune.plugins.speedup import speedup
from mistune.plugins.url import url
from mistune.plugins.formatting import strikethrough, subscript, superscript, insert, mark
from mistune.plugins.abbr import abbr
from mistune.plugins.def_list import def_list
from mistune.plugins.task_lists import task_lists
from mistune.plugins.table import table
from mistune.plugins.footnotes import footnotes
from mistune.plugins.spoiler import spoiler
from flask import url_for
from markupsafe import Markup
from pluggy import HookimplMarker
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
import re

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)

USER_TAG_PATTERN = r"@(\w+)"


def parse_user_link(inline, m, state):
    url = url_for("user.profile", username=m.group(0).replace("@", ""), _external=False)
    text = m.group(0)
    state.append_token(
        {
            "type": "link",
            "children": [{"type": "text", "raw": text}],
            "attrs": {"url": url},
        }
    )

    return m.end()


def flaskbb_userify(md):
    """Mistune plugin that transforms @username references to links."""
    md.inline.register("flaskbb_user_link", USER_TAG_PATTERN, parse_user_link, before="link")


DEFAULT_PLUGINS = [
    url,
    strikethrough,
    spoiler,
    subscript,
    superscript,
    insert,
    mark,
    abbr,
    def_list,
    task_lists,
    table,
    footnotes,
    speedup,
    flaskbb_userify
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
    app.pluggy.hook.flaskbb_load_post_markdown_plugins(plugins=plugins, app=app)
    app.jinja_env.filters["markup"] = make_renderer(render_classes, plugins)

    render_classes = app.pluggy.hook.flaskbb_load_nonpost_markdown_class(app=app)
    plugins = DEFAULT_PLUGINS[:]
    plugins = app.pluggy.hook.flaskbb_load_nonpost_markdown_plugins(
        plugins=plugins, app=app
    )
    app.jinja_env.filters["nonpost_markup"] = make_renderer(render_classes, plugins)


def make_renderer(classes, plugins):
    RenderCls = type("FlaskBBRenderer", tuple(classes), {})

    markup = mistune.create_markdown(
        renderer=RenderCls(), plugins=plugins, escape=True, hard_wrap=True
    )
    return lambda text: Markup(markup(text))
