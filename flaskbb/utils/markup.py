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

from flask import url_for

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound


logger = logging.getLogger(__name__)


_re_user = re.compile(r'@(\w+)', re.I)


class FlaskBBRenderer(mistune.Renderer):
    """Markdown with some syntactic sugar, such as @user gettting linked
    to the user's profile.
    """
    def __init__(self, **kwargs):
        super(FlaskBBRenderer, self).__init__(**kwargs)

    def paragraph(self, text):
        """Render paragraph tags, autolinking user handles."""

        def userify(match):
            value = match.group(1)
            user = "<a href='{url}'>@{user}</a>".format(
                url=url_for("user.profile", username=value, _external=False),
                user=value
            )
            return user

        text = _re_user.sub(userify, text)

        return '<p>%s</p>\n' % text.strip(' ')

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


renderer = FlaskBBRenderer(escape=True, hard_wrap=True)
markdown = mistune.Markdown(renderer=renderer)
