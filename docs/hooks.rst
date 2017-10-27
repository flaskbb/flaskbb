.. _hooks:

Hooks
=====

In order to extend FlaskBB you will need to connect your callbacks with
events.

.. admonition:: Additional hooks

    If you miss a hook, feel free to open a new issue or create a pull
    request. The pull request should always contain a entry in this document
    with a small example.

    A hook needs a hook specification which are defined in
    :mod:`flaskbb.plugins.spec`. All hooks have to be prefixed with
    ``flaskbb_`` and template hooks with ``flaskbb_tpl_``.


.. currentmodule:: flaskbb.plugins.spec

.. autofunction:: flaskbb_extensions
.. autofunction:: flaskbb_load_translations
.. autofunction:: flaskbb_load_migrations
.. autofunction:: flaskbb_load_blueprints
.. autofunction:: flaskbb_request_processors
.. autofunction:: flaskbb_errorhandlers
.. autofunction:: flaskbb_jinja_directives
.. autofunction:: flaskbb_additional_setup
.. autofunction:: flaskbb_cli


Template Hooks
--------------

.. note::

    Template events, which are used in forms, are usually rendered after the
    hidden CSRF token field and before an submit field.


.. autofunction:: flaskbb_tpl_before_navigation
.. autofunction:: flaskbb_tpl_after_navigation
.. autofunction:: flaskbb_tpl_before_registration_form
.. autofunction:: flaskbb_tpl_after_registration_form
.. autofunction:: flaskbb_tpl_before_update_user_details
.. autofunction:: flaskbb_tpl_after_update_user_details
