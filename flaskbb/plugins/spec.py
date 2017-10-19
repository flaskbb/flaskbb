# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.spec
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the core FlaskBB plugin hook definitions

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from pluggy import HookspecMarker

spec = HookspecMarker('flaskbb')


@spec
def flaskbb_extensions(app):
    """
    Hook for initializing any plugin loaded extensions
    """


@spec
def flaskbb_load_translations():
    """
    Hook for registering translation folders.
    """


@spec
def flaskbb_load_migrations():
    """
    Hook for registering additional migrations
    """


@spec
def flaskbb_load_blueprints(app):
    """
    Hook for registering blueprints
    """


@spec
def flaskbb_request_processors(app):
    """
    Hook for registering pre/post request processors
    """


@spec
def flaskbb_errorhandlers(app):
    """
    Hook for registering error handlers
    """


@spec
def flaskbb_jinja_directives(app):
    """
    Hook for registering jinja filters, context processors, etc
    """


@spec
def flaskbb_additional_setup(app, pluggy):
    """
    Hook for any additional setup a plugin wants to do after all other application
    setup has finished
    """


@spec
def flaskbb_cli(cli):
    """
    Hook for registering CLI commands
    """


@spec
def flaskbb_tpl_before_navigation():
    """Hook for registering additional navigation items."""
