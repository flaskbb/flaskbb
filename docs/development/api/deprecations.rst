.. _deprecations:

Deprecation Helpers
===================

FlaskBB publicly provides tools for handling deprecations and are open to use
by plugins or other extensions to FlaskBB. For example if a plugin wants to
deprecate a particular function it could do::

    from flaskbb.deprecation import FlaskBBDeprecation, deprecated

    class RemovedInPluginV2(FlaskBBDeprecation):
        version = (2, 0, 0)


    @deprecated(category=RemovedInPluginV2)
    def thing_removed_in_plugin_v2():
        ...


When used in live code, a warning will be issue like::

    warning: RemovedInPluginV2: thing_removed_in_plugin_v2 and will be removed
        in version 2.0.0.

Optionally, a message can be provided to give further information about the
warning::

    @deprecated(message="Use plugin.frobinator instead.", category=RemovedInPluginV2)
    def thing_also_removed_in_plugin_v2():
        ...

This will produce a warning like::

    warning: RemovedInPluginV2: thing_removed_in_plugin_v2 and will be removed
        in version 2.0.0. Use plugin.frobinator instead.


If a decorated function has a docstring, the entire warning message will be
appended to it for introspection and documentation purposes.

Helpers
~~~~~~~

.. module:: flaskbb.deprecation

.. autoclass:: FlaskBBWarning
.. autoclass:: FlaskBBDeprecation
.. autoclass:: RemovedInFlaskBB3
.. autofunction:: deprecated
