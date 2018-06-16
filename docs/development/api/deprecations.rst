.. _deprecations:

Deprecation Helpers
===================

FlaskBB publicly provides tools for handling deprecations and are open to use
by plugins or other extensions to FlaskBB. For example if a plugin wants to
deprecate a particular function it could do::

    from flaskbb.deprecation import FlaskBBDeprecation, deprecated

    class RemovedInPluginV2(FlaskBBDeprecation):
        version = (2, 0, 0)


    @deprecated
    def thing_removed_in_plugin_v2():
        ...


Now the plugin will issue deprecation warnings in the same fashion as the rest
of FlaskBB.

.. module:: flaskbb.deprecation

.. autoclass:: FlaskBBWarning
.. autoclass:: FlaskBBDeprecation
.. autoclass:: RemovedInFlaskBB3
.. autofunction:: deprecated
