# -*- coding: utf-8 -*-
"""
flaskbb.utils.markup
~~~~~~~~~~~~~~~~~~~~

A module for all markup related stuff.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import re
from typing import Callable

import mistune
from flask import Flask, url_for
from markupsafe import Markup
from mistune.plugins import PluginRef
from mistune.plugins.abbr import abbr
from mistune.plugins.def_list import def_list
from mistune.plugins.footnotes import footnotes
from mistune.plugins.formatting import (
    insert,
    mark,
    strikethrough,
    subscript,
    superscript,
)
from mistune.plugins.speedup import speedup
from mistune.plugins.spoiler import spoiler
from mistune.plugins.table import table
from mistune.plugins.task_lists import task_lists
from mistune.plugins.url import url
from pluggy import HookimplMarker
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from typing_extensions import Iterable

from flaskbb.extensions import pluggy

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)

MENTION_PATTERN = r"@(\w+)"


def parse_mention(
    inline: mistune.InlineParser, m: re.Match[str], state: mistune.InlineState
) -> int:
    """Parse @username mention and return token"""
    username = m.group(0)
    state.append_token({"type": "mention", "raw": username})
    return m.end()


def render_html_mention(renderer: mistune.HTMLRenderer, text: str):
    """Render mention token as HTML link"""
    url = url_for("user.profile", username=text, _external=False)
    return f'<a href="{url.replace("@", "")}">{text}</a>'


def plugin_mention(md: mistune.Markdown):
    """
    Mistune v3 plugin to parse @username mentions and convert them to links.

    Usage:
        import mistune
        from mention_plugin import plugin_mention

        md = mistune.create_markdown(plugins=[plugin_mention])
        html = md("Hello @john, how are you?")
    """

    # Pattern to match @username (alphanumeric and underscores)

    # Register the inline rule
    md.inline.register("mention", MENTION_PATTERN, parse_mention, before="link")

    # Register the HTML renderer
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("mention", render_html_mention)


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
    plugin_mention,
]


class FlaskBBRenderer(mistune.HTMLRenderer):
    """Mistune renderer that uses pygments to apply code highlighting."""

    def __init__(self, **kwargs):
        super(FlaskBBRenderer, self).__init__(**kwargs)

    def block_code(self, code: str, info: str | None = None):
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
def flaskbb_jinja_directives(app: Flask):
    render_classes = pluggy.hook.flaskbb_load_post_markdown_class(app=app)
    plugins = DEFAULT_PLUGINS[:]
    pluggy.hook.flaskbb_load_post_markdown_plugins(plugins=plugins, app=app)
    app.jinja_env.filters["markup"] = make_renderer(render_classes, plugins)

    render_classes = pluggy.hook.flaskbb_load_nonpost_markdown_class(app=app)
    plugins = DEFAULT_PLUGINS[:]
    plugins = pluggy.hook.flaskbb_load_nonpost_markdown_plugins(
        plugins=plugins, app=app
    )
    app.jinja_env.filters["nonpost_markup"] = make_renderer(render_classes, plugins)


def make_renderer(
    classes: tuple[type], plugins: Iterable[PluginRef] | None = None
) -> Callable[[str], Markup]:
    RenderCls = type("FlaskBBRenderer", tuple(classes), {})

    markup = mistune.create_markdown(
        renderer=RenderCls(),  # pyright: ignore
        plugins=plugins,
        escape=True,
        hard_wrap=True,
    )
    return lambda text: Markup(markup(text))
