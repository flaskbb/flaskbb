.. _plugin_development_hooks:

Using Hooks
===========

Hooks are invoked based on an event occurring within FlaskBB. This makes it
possible to change the behavior of certain actions without modifying the
actual source code of FlaskBB.

For your plugin to actually do something useful, you probably want to 'hook'
your code into FlaskBB. This can be done throughout a lot of places in the
code. FlaskBB loads and calls the hook calls hook functions from registered
plugins for any given hook specification.

Each hook specification has a corresponding hook implementation. By default,
all hooks that are prefix with ``flaskbb_`` will be marked as a standard
hook implementation. It is possible to modify the behavior of hooks.
For example, default hooks are called in LIFO registered order.
Although, registration order might not be deterministic. A hookimpl
can influence its call-time invocation position using special attributes. If
marked with a "tryfirst" or "trylast" option it will be executed first or last
respectively in the hook call loop::

    hookimpl = HookimplMarker('flaskbb')

    @hookimpl(trylast=True)
    def flaskbb_additional_setup(app):
        return "save the best for last"


In order to extend FlaskBB with your Plugin you will need to connect your
callbacks to the hooks.

Let's look at an actually piece of `used code`_.

.. sourcecode:: python

    def flaskbb_load_blueprints(app):
        app.register_blueprint(portal, url_prefix="/portal")

By defining a function called ``flaskbb_load_blueprints``, which has a
corresponding hook specification under the same name. FlaskBB will pass
in an ``app`` object as specified in the hook spec, which we will use to
register a new blueprint. It is also possible to completely omit the ``app``
argument from the function where it is **not possible** to add new arguments to
the hook implemention.

For a complete list of all available hooks in FlaskBB see the
:ref:`hooks` section.

pytest and pluggy are good resources to get better understanding on how to
write `hook functions`_ using `pluggy`_.

.. _`used code`: https://github.com/sh4nks/flaskbb-plugins/blob/master/portal/portal/__init__.py#L31
.. _`hook functions`: https://docs.pytest.org/en/latest/writing_plugins.html#writing-hook-functions
.. _`pluggy`: https://pluggy.readthedocs.io/en/latest/#defining-and-collecting-hooks

