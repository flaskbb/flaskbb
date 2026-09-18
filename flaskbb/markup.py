"""
flaskbb.utils.markup
~~~~~~~~~~~~~~~~~~~~

A module for all markup related stuff.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import re
from collections.abc import Callable, Iterable, Mapping
from typing import Any, override
from urllib.parse import urlparse

import mistune
from flask import current_app, Flask, request, url_for
from flask_babelplus import gettext as _
from markupsafe import escape, Markup
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
from werkzeug.exceptions import HTTPException

from flaskbb.extensions import pluggy
from flaskbb.settings import flaskbb_config
from flaskbb.utils.proxies import current_user

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


QUOTE_ATTRIBUTION_SUFFIX = " wrote:"
COLLAPSED_QUOTE_DEPTH = 3
LINE_BREAKS = ("linebreak", "softbreak")


def match_local_url(url: str) -> tuple[Any, Mapping[str, Any]] | None:
    parsed = urlparse(url)
    if parsed.scheme not in ("", "http", "https"):
        return None
    if parsed.netloc and parsed.netloc.lower() != request.host.lower():
        return None

    path = parsed.path
    if request.script_root:
        if not path.startswith(request.script_root):
            return None
        path = path[len(request.script_root) :]

    adapter = current_app.url_map.bind_to_environ(request.environ)
    try:
        return adapter.match(path, method="GET")
    except HTTPException:
        return None


def link_target(token: dict[str, Any], endpoint: str, argument: str) -> Any:
    if token["type"] != "link":
        return None
    match = match_local_url(token["attrs"]["url"])
    if match is None or match[0] != endpoint:
        return None
    return match[1][argument]


def parse_quote_attribution(
    paragraph: dict[str, Any], md: mistune.Markdown, state: mistune.BlockState
) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    """Parses a ``**[user](profile) wrote:** [view post](post)`` paragraph.

    Returns the attribution attrs and whatever content followed the
    attribution on the next lines of the same paragraph.
    """
    if "text" in paragraph:
        # inline parsing normally happens at render time
        if QUOTE_ATTRIBUTION_SUFFIX not in paragraph["text"]:
            return None
        text = paragraph.pop("text").strip(" \r\n\t\f")
        paragraph["children"] = md.inline(text, state.env)

    children = paragraph["children"]
    if not children or children[0]["type"] != "strong":
        return None

    strong = children[0]["children"]
    if len(strong) != 2 or strong[1] != {"type": "text", "raw": QUOTE_ATTRIBUTION_SUFFIX}:
        return None
    author = link_target(strong[0], "user.profile", "username")
    if author is None:
        return None
    attrs: dict[str, Any] = {"author": author}

    rest = children[1:]
    if len(rest) >= 2 and rest[0] == {"type": "text", "raw": " "}:
        post_id = link_target(rest[1], "forum.view_post", "post_id")
        if post_id is not None:
            attrs["post_id"] = post_id
            rest = rest[2:]

    if rest and rest[0]["type"] not in LINE_BREAKS:
        return None
    return attrs, rest[1:]


def next_block(tokens: list[dict[str, Any]], index: int) -> int:
    index += 1
    while index < len(tokens) and tokens[index]["type"] == "blank_line":
        index += 1
    return index


def is_attributed(token: dict[str, Any]) -> bool:
    return "author" in token.get("attrs", {})


def attach_quote_attributions(
    tokens: list[dict[str, Any]],
    md: mistune.Markdown,
    state: mistune.BlockState,
    depth: int = 1,
):
    index = 0
    while index < len(tokens):
        token = tokens[index]
        following = next_block(tokens, index)

        # Legacy quotes put the attribution paragraph in front of the quote.
        if (
            token["type"] == "paragraph"
            and following < len(tokens)
            and tokens[following]["type"] == "block_quote"
            and not is_attributed(tokens[following])
        ):
            attribution = parse_quote_attribution(token, md, state)
            if attribution is not None and not attribution[1]:
                tokens[following].setdefault("attrs", {}).update(attribution[0])
                del tokens[index:following]
                continue

        if token["type"] == "block_quote":
            if not is_attributed(token):
                attach_leading_attribution(token, md, state)
            token.setdefault("attrs", {})["depth"] = depth
            attach_quote_attributions(token["children"], md, state, depth + 1)
        elif token["type"] in ("list", "list_item"):
            attach_quote_attributions(token["children"], md, state, depth)
        index += 1


def attach_leading_attribution(
    quote: dict[str, Any], md: mistune.Markdown, state: mistune.BlockState
):
    children = quote["children"]
    first = next_block(children, -1)
    if first >= len(children) or children[first]["type"] != "paragraph":
        return
    # A paragraph directly followed by a quote attributes that inner quote.
    after = first + 1
    if after < len(children) and children[after]["type"] == "block_quote":
        return

    attribution = parse_quote_attribution(children[first], md, state)
    if attribution is None:
        return
    attrs, remaining = attribution
    quote.setdefault("attrs", {}).update(attrs)
    if remaining:
        children[first]["children"] = remaining
    else:
        del children[first]


def quote_attribution(md: mistune.Markdown):
    """
    Mistune plugin that turns a ``**[user](profile) wrote:**`` line at the
    start of a quote, or directly in front of it, into a quote header.
    Usernames and post ids are taken from the link targets, never from the
    link text, so a header always names the user it links to.

    It also records each quote's nesting depth, so that the renderer can
    collapse deeply nested quotes and offer to expand long top level ones.
    """
    md.before_render_hooks.append(
        lambda md, state: attach_quote_attributions(state.tokens, md, state)
    )


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

POST_PLUGINS = [*DEFAULT_PLUGINS, quote_attribution]


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
    def block_quote(
        self,
        text: str,
        author: str | None = None,
        post_id: int | None = None,
        depth: int | None = None,
    ) -> str:
        if depth is None:
            return super().block_quote(text)

        header = self.quote_header(author, post_id) if author is not None else None
        opening = '<blockquote class="post-quote">' if header else "<blockquote>"

        if depth >= COLLAPSED_QUOTE_DEPTH:
            caret = Markup('<span class="fas fa-chevron-right post-quote-caret"></span>')
            summary = header or escape(_("Quote"))
            return (
                f'{opening}\n<details class="post-quote-collapsed">'
                f'<summary class="post-quote-header">{caret}{summary}</summary>\n'
                f"{text}</details>\n</blockquote>\n"
            )

        html = f"{opening}\n"
        if header:
            html += f'<header class="post-quote-header">{header}</header>\n'
        if depth == 1:
            # revealed by the theme's JavaScript when the quote is clipped
            html += str(
                Markup(
                    '<button type="button" class="btn btn-sm btn-light post-quote-expand" '
                    "hidden>{}</button>\n"
                ).format(_("Show full quote"))
            )
        return f"{html}{text}</blockquote>\n"

    @staticmethod
    def quote_header(author: str, post_id: int | None) -> Markup:
        author_link = Markup('<a class="post-quote-author" href="{}">{}</a>').format(
            url_for("user.profile", username=author), author
        )
        attribution = escape(_("%(author)s wrote:")) % {"author": author_link}
        header = Markup('<span class="post-quote-attribution">{}</span>').format(attribution)
        if post_id is not None:
            header += Markup(
                '<a class="post-quote-source" href="{}" title="{}">'
                '<span class="fas fa-arrow-up"></span></a>'
            ).format(url_for("forum.view_post", post_id=post_id), _("Go to quoted post"))
        return header

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
    app.jinja_env.filters["markup"] = post_renderer(app)
    app.jinja_env.filters["nonpost_markup"] = nonpost_renderer(app)


def post_renderer(app: Flask) -> Callable[[str], Markup]:
    render_classes = pluggy.hook.flaskbb_load_post_markdown_class(app=app)
    plugins = POST_PLUGINS[:]
    pluggy.hook.flaskbb_load_post_markdown_plugins(plugins=plugins, app=app)
    return make_renderer(render_classes, plugins)


def nonpost_renderer(app: Flask) -> Callable[[str], Markup]:
    render_classes = pluggy.hook.flaskbb_load_nonpost_markdown_class(app=app)
    plugins = DEFAULT_PLUGINS[:]
    pluggy.hook.flaskbb_load_nonpost_markdown_plugins(plugins=plugins, app=app)
    return make_renderer(render_classes, plugins)


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
