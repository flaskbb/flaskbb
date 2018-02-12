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
def flaskbb_tpl_before_user_nav_loggedin():
    """Hook for registering additional user navigational items
    which are only shown when a user is logged in.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_after_user_nav_loggedin():
    """Hook for registering additional user navigational items
    which are only shown when a user is logged in.

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
def flaskbb_tpl_before_user_details_form():
    """This hook is emitted in the Change User Details form **before** an
    input field is rendered.

    in :file:`templates/user/change_user_details.html`.
    """


@spec
def flaskbb_tpl_after_user_details_form():
    """This hook is emitted in the Change User Details form **after** the last
    input field has been rendered but before the submit field.

    in :file:`templates/user/change_user_details.html`.
    """

@spec
def flaskbb_tpl_profile_settings_menu():
    """This hook is emitted on the user settings page in order to populate the
    side bar menu. Implementations of this hook should return a list of tuples
    that are view name and display text. The display text will be provided to
    the translation service so it is unnecessary to supply translated text.

    A plugin can declare a new block by setting the view to None. If this is
    done, consider marking the hook implementation with `trylast=True` to
    avoid capturing plugins that do not create new blocks.

    For example::

        @impl(trylast=True)
        def flaskbb_tpl_profile_settings_menu():
            return [
                (None, 'Account Settings'),
                ('user.settings', 'General Settings'),
                ('user.change_user_details', 'Change User Details'),
                ('user.change_email', 'Change E-Mail Address'),
                ('user.change_password', 'Change Password')
            ]

    Hookwrappers for this spec should not be registered as FlaskBB
    supplies its own hookwrapper to flatten all the lists into a single list.

    in :file:`templates/user/settings_layout.html`
    """
