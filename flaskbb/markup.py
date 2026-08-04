"""
flaskbb.utils.markup
~~~~~~~~~~~~~~~~~~~~

A module for all markup related stuff.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import re
from collections.abc import Callable, Iterable
from typing import Any, override
from urllib.parse import urlparse

import mistune
from flask import Flask, request, url_for
from flask_login import current_user
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

from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import pluggy

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)

# MENTION_PATTERN = r"@(?:(?<!\\)(?:\\\\)*\\|\w+|\\ \.)(?: |$|)"
MENTION_REGEX = re.compile(r"\B@([\w\-]+)")


def replace_mention_with_linktag(m: re.Match[str]) -> str:
    username = m.group(1)
    url = url_for("user.profile", username=username, _external=False)
    return f"[{m.group(0)}]({url})"


def process_mentions(md: mistune.Markdown, state: mistune.BlockState):
    state.src = MENTION_REGEX.sub(replace_mention_with_linktag, state.src)


def plugin_mention(md: mistune.Markdown):
    """
    Mistune plugin to parse @username mentions and convert them
    to [@username](/user/username) tags.
    I couldn't get it to work otherwise. If anyone knows a better way
    or knows regex better feel free to open a PR :)
    """
    md.before_parse_hooks.append(process_mentions)


DEFAULT_PLUGINS = [
    plugin_mention,
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
]


def should_open_in_new_tab() -> bool:
    if current_user.is_authenticated and current_user.open_links_in_new_tab is not None:
        return current_user.open_links_in_new_tab
    return bool(flaskbb_config["OPEN_LINKS_IN_NEW_TAB"])


class FlaskBBRenderer(mistune.HTMLRenderer):
    """Mistune renderer that uses pygments to apply code highlighting."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    @override
    def block_code(self, code: str, info: str | None = None) -> str:
        if info:
            try:
                lexer = get_lexer_by_name(info, stripall=True)
            except ClassNotFound:
                lexer = None
        else:
            lexer = None
        if not lexer:
            return f"\n<pre><code>{mistune.escape(code)}</code></pre>\n"
        formatter = HtmlFormatter()  # pyright: ignore
        return highlight(code, lexer, formatter)

    @override
    def link(self, text: str, url: str, title: str | None = None) -> str:
        html = super().link(text, url, title)
        if self._is_external(url):
            attrs = ' rel="noopener noreferrer nofollow"'
            if should_open_in_new_tab():
                attrs += ' target="_blank"'
            html = html.replace("<a ", f"<a{attrs} ", 1)
        return html

    @staticmethod
    def _is_external(url: str) -> bool:
        netloc = urlparse(url).netloc.lower()
        return bool(netloc) and netloc != request.host.lower()


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
    plugins = pluggy.hook.flaskbb_load_nonpost_markdown_plugins(plugins=plugins, app=app)
    app.jinja_env.filters["nonpost_markup"] = make_renderer(render_classes, plugins)


def make_renderer(
    classes: tuple[type] | list[type], plugins: Iterable[PluginRef] | None = None
) -> Callable[[str], Markup]:
    RenderCls = type("FlaskBBRenderer", tuple(classes), {})

    markup = mistune.create_markdown(
        renderer=RenderCls(),  # pyright: ignore
        plugins=plugins,
        escape=True,
        hard_wrap=True,
    )
    return lambda text: Markup(markup(text))
