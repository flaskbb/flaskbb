import os
import re

from flask import url_for

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


_re_emoji = re.compile(r':([a-z0-9\+\-_]+):', re.I)
_re_user = re.compile(r'@(\w+)', re.I)


def collect_emojis():
    """Returns a dictionary containing all emojis with their
    name and filename. If the folder doesn't exist it returns a empty
    dictionary.
    """
    emojis = dict()
    full_path = os.path.join(os.path.abspath("flaskbb"), "static", "emoji")
    # return an empty dictionary if the path doesn't exist
    if not os.path.exists(full_path):
        return emojis

    for emoji in os.listdir(full_path):
        emojis[emoji.split(".")[0]] = emoji

    return emojis

EMOJIS = collect_emojis()


class FlaskBBRenderer(mistune.Renderer):
    """Markdown with some syntetic sugar such as @user gets linked to the
    user's profile and emoji support.
    """
    def __init__(self, **kwargs):
        super(FlaskBBRenderer, self).__init__(**kwargs)

    def paragraph(self, text):
        """Rendering paragraph tags. Like ``<p>`` with emoji support."""

        def emojify(match):
            value = match.group(1)

            if value in EMOJIS:
                filename = url_for(
                    "static",
                    filename="emoji/{}".format(EMOJIS[value])
                )

                emoji = "<img class='{css}' alt='{alt}' src='{src}' />".format(
                    css="emoji", alt=value,
                    src=filename
                )
                return emoji
            return match.group(0)

        def userify(match):
            value = match.group(1)
            user = "<a href='{url}'>@{user}</a>".format(
                url=url_for("user.profile", username=value),
                user=value
            )
            return user

        text = _re_emoji.sub(emojify, text)
        text = _re_user.sub(userify, text)

        return '<p>%s</p>\n' % text.strip(' ')

    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)


renderer = FlaskBBRenderer()
markdown = mistune.Markdown(renderer=renderer)
