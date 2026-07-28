.. _hooks_plugin_lifecycle:

.. currentmodule:: flaskbb.plugins.spec

Plugin Lifecycle Hooks
=======================

These hooks fire around a plugin's install/uninstall/upgrade lifecycle and
around changes to its setting values. Unlike other FlaskBB hooks they are
**not** prefixed with ``flaskbb_`` - they're named after the event instead
(``on_plugin_*``).

Every implementation of these hooks is called for every plugin's lifecycle
event, not just the plugin that implements it - since pluggy has no way to
route a hook call to only one plugin, implementations must check
``plugin_name`` themselves and no-op if it isn't the one they care about.

.. autofunction:: on_plugin_install
.. autofunction:: on_plugin_uninstall
.. autofunction:: on_plugin_upgrade
.. autofunction:: on_plugin_settings_changed
