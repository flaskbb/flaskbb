.. _startup_hooks:

.. currentmodule:: flaskbb.plugins.spec

Application Startup Hooks
=========================

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
.. autofunction:: flaskbb_load_post_markdown_class
.. autofunction:: flaskbb_load_nonpost_markdown_class
.. autofunction:: flaskbb_additional_setup

