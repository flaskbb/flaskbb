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


# Setup Hooks

@spec
def flaskbb_extensions(app):
    """Hook for initializing any plugin loaded extensions."""


@spec
def flaskbb_load_translations():
    """Hook for registering translation folders."""


@spec
def flaskbb_load_migrations():
    """Hook for registering additional migrations."""


@spec
def flaskbb_load_blueprints(app):
    """Hook for registering blueprints."""


@spec
def flaskbb_request_processors(app):
    """Hook for registering pre/post request processors."""


@spec
def flaskbb_errorhandlers(app):
    """Hook for registering error handlers."""


@spec
def flaskbb_jinja_directives(app):
    """Hook for registering jinja filters, context processors, etc."""


@spec
def flaskbb_additional_setup(app, pluggy):
    """Hook for any additional setup a plugin wants to do after all other
    application setup has finished.
    """


@spec
def flaskbb_cli(cli):
    """Hook for registering CLI commands."""


# Template Hooks

@spec
def flaskbb_tpl_before_navigation():
    """Hook for registering additional navigation items.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_after_navigation():
    """Hook for registering additional navigation items.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_before_registration_form():
    """This hook is emitted in the Registration form **before** the first
    input field but after the hidden CSRF token field.

    in :file:`templates/auth/register.html`.
    """


@spec
def flaskbb_tpl_after_registration_form():
    """This hook is emitted in the Registration form **after** the last
    input field but before the submit field.

    in :file:`templates/auth/register.html`.
    """


@spec
def flaskbb_tpl_before_update_user_details():
    """This event is emitted in the Change User Details form **before** an
    input field is rendered.

    in :file:`templates/user/change_user_details.html`.
    """


@spec
def flaskbb_tpl_after_update_user_details():
    """This hook is emitted in the Change User Details form **after** the last
    input field has been rendered but before the submit field.

    in :file:`templates/user/change_user_details.html`.
    """
