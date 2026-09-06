"""
flaskbb.cli
~~~~~~~~~~~

FlaskBB's Command Line Interface.
To make it work, you have to install FlaskBB via ``pip install -e .``.

Plugin and Theme templates are generated via cookiecutter.
In order to generate those project templates you have to
cookiecutter first::

    pip install cookiecutter

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from flaskbb.cli.db import db
from flaskbb.cli.groups import groups
from flaskbb.cli.main import flaskbb
from flaskbb.cli.permissions import permissions
from flaskbb.cli.plugins import plugins
from flaskbb.cli.themes import themes
from flaskbb.cli.translations import translations
from flaskbb.cli.users import users

__all__ = [
    "db",
    "flaskbb",
    "groups",
    "permissions",
    "plugins",
    "themes",
    "translations",
    "users",
]
