.. _hooks:

Hooks
=====

In FlaskBB we distinguish from `Python Hooks <#python-hooks>`_ and
`Template Hooks <#template-hooks>`_.
Python Hooks are prefixed with ``flaskbb_`` and called are called in Python
files whereas Template Hooks have to be prefixed with ``flaskbb_tpl_`` and are
executed in the templates.

If you miss a hook, feel free to open a new issue or create a pull
request. The pull request should always contain a entry in this document
with a small example.

A hook needs a hook specification which are defined in
:mod:`flaskbb.plugins.spec`. All hooks have to be prefixed with
``flaskbb_`` and template hooks with ``flaskbb_tpl_``.


Python Hooks
------------

.. currentmodule:: flaskbb.plugins.spec

Application Startup Hooks
~~~~~~~~~~~~~~~~~~~~~~~~~

Application startup hooks are called when the application is created,
either through a WSGI server (uWSGI or gunicorn for example) or by
the ``flaskbb`` command.

Unless noted, all FlaskBB hooks are called after the relevant builtin
FlaskBB setup has run (e.g. ``flaskbb_load_blueprints`` is called after
all standard FlaskBB blueprints have been loaded).

The hooks below are listed in the order they are called.

.. autofunction:: flaskbb_extensions
.. autofunction:: flaskbb_load_blueprints
.. autofunction:: flaskbb_jinja_directives
.. autofunction:: flaskbb_request_processors
.. autofunction:: flaskbb_errorhandlers
.. autofunction:: flaskbb_load_migrations
.. autofunction:: flaskbb_load_translations
.. autofunction:: flaskbb_additional_setup

FlaskBB CLI Hooks
~~~~~~~~~~~~~~~~~

These are hooks are only invoked when using the ``flaskbb``
CLI.

.. autofunction:: flaskbb_cli


Template Hooks
--------------

.. note::

    Template hooks, which are used in forms, are usually rendered after the
    hidden CSRF token field and before an submit field.


.. autofunction:: flaskbb_tpl_before_navigation
.. autofunction:: flaskbb_tpl_after_navigation
.. autofunction:: flaskbb_tpl_before_registration_form
.. autofunction:: flaskbb_tpl_after_registration_form
.. autofunction:: flaskbb_tpl_before_user_details_form
.. autofunction:: flaskbb_tpl_after_user_details_form
.. autofunction:: flaskbb_tpl_profile_settings_menu
