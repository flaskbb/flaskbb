# -*- coding: utf-8 -*-
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
from flaskbb.cli.main import flaskbb  # noqa
from flaskbb.cli.plugins import plugins  # noqa
from flaskbb.cli.themes import themes  # noqa
from flaskbb.cli.translations import translations  # noqa
from flaskbb.cli.users import users  # noqa
