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

Be sure to also check out the :ref:`api` documentation for interfaces that
interact with these plugins in interesting ways.


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

These hooks are only invoked when using the ``flaskbb``
CLI.

.. autofunction:: flaskbb_cli
.. autofunction:: flaskbb_shell_context


FlaskBB Event Hooks
~~~~~~~~~~~~~~~~~~~

.. autofunction:: flaskbb_event_post_save_before
.. autofunction:: flaskbb_event_post_save_after
.. autofunction:: flaskbb_event_topic_save_before
.. autofunction:: flaskbb_event_topic_save_after
.. autofunction:: flaskbb_event_user_registered
.. autofunction:: flaskbb_authenticate
.. autofunction:: flaskbb_post_authenticate
.. autofunction:: flaskbb_authentication_failed
.. autofunction:: flaskbb_reauth_attempt
.. autofunction:: flaskbb_post_reauth
.. autofunction:: flaskbb_reauth_failed


FlaskBB Form Hooks
~~~~~~~~~~~~~~~~~~

.. autofunction:: flaskbb_form_new_post_save
.. autofunction:: flaskbb_form_new_post
.. autofunction:: flaskbb_form_new_topic
.. autofunction:: flaskbb_form_new_topic_save
.. autofunction:: flaskbb_form_registration


Template Hooks
--------------

.. note::

    Template hooks, which are used in forms, are usually rendered after the
    hidden CSRF token field and before an submit field.


.. autofunction:: flaskbb_tpl_navigation_before
.. autofunction:: flaskbb_tpl_navigation_after
.. autofunction:: flaskbb_tpl_user_nav_loggedin_before
.. autofunction:: flaskbb_tpl_user_nav_loggedin_after
.. autofunction:: flaskbb_tpl_form_registration_before
.. autofunction:: flaskbb_tpl_form_registration_after
.. autofunction:: flaskbb_tpl_form_user_details_before
.. autofunction:: flaskbb_tpl_form_user_details_after
.. autofunction:: flaskbb_tpl_form_new_post_before
.. autofunction:: flaskbb_tpl_form_new_post_after
.. autofunction:: flaskbb_tpl_form_new_topic_before
.. autofunction:: flaskbb_tpl_form_new_topic_after
.. autofunction:: flaskbb_tpl_profile_settings_menu
.. autofunction:: flaskbb_tpl_profile_sidebar_stats
.. autofunction:: flaskbb_tpl_post_author_info_before
.. autofunction:: flaskbb_tpl_post_author_info_after
.. autofunction:: flaskbb_tpl_post_content_before
.. autofunction:: flaskbb_tpl_post_content_after
.. autofunction:: flaskbb_tpl_post_menu_before
.. autofunction:: flaskbb_tpl_post_menu_after
.. autofunction:: flaskbb_tpl_topic_controls
.. autofunction:: flaskbb_tpl_admin_settings_menu
