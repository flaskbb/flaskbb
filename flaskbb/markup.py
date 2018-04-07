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

import mistune
from flask import url_for
from jinja2 import Markup
from pluggy import HookimplMarker
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

impl = HookimplMarker('flaskbb')

logger = logging.getLogger(__name__)

_re_user = re.compile(r'@(\w+)', re.I)


def userify(match):
    value = match.group(1)
    user = "<a href='{url}'>@{user}</a>".format(
        url=url_for("user.profile", username=value, _external=False),
        user=value
    )
    return user


class FlaskBBRenderer(mistune.Renderer):
    """Markdown with some syntactic sugar, such as @user gettting linked
    to the user's profile.
    """

    def __init__(self, **kwargs):
        super(FlaskBBRenderer, self).__init__(**kwargs)

    def paragraph(self, text):
        """Render paragraph tags, autolinking user handles."""

        text = _re_user.sub(userify, text)
        return super(FlaskBBRenderer, self).paragraph(text)

    def block_code(self, code, lang):
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                lexer = None
        else:
            lexer = None
        if not lexer:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
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
    app.jinja_env.filters['markup'] = make_renderer(render_classes)

    render_classes = app.pluggy.hook.flaskbb_load_nonpost_markdown_class(
        app=app
    )
    app.jinja_env.filters['nonpost_markup'] = make_renderer(render_classes)


def make_renderer(classes):
    RenderCls = type('FlaskBBRenderer', tuple(classes), {})

    markup = mistune.Markdown(renderer=RenderCls(escape=True, hard_wrap=True))
    return lambda text: Markup(markup.render(text))
