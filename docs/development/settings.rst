.. _settings:

Settings
========

This part covers how FlaskBB's settings system works. This is especially
useful if you plan on developing a plugin or want to contribute to FlaskBB
itself.

Settings are not hardcoded config values - they're a registry of
declarative definitions backed by DB rows. A setting is defined once as a
:class:`~flaskbb.core.settings.definitions.SettingDefinition` grouped into a
:class:`~flaskbb.core.settings.definitions.SettingGroup`, registered into the
:class:`~flaskbb.core.settings.registry.SettingsRegistry` at startup, and its
value is persisted as a :class:`~flaskbb.core.settings.models.Setting` row.

Registering setting groups
---------------------------

Setting groups are registered via two pluggy hooks, both defined in
:mod:`flaskbb.plugins.spec`:

``flaskbb_load_internal_setting_groups``
    FlaskBB's own hook for its built-in setting groups (``general``,
    ``auth``, ``misc``, ``appearance``, ...). Plugin authors must **not**
    implement this hook.

``flaskbb_load_setting_groups``
    The hook third-party plugins implement to register their own
    :class:`~flaskbb.core.settings.definitions.SettingGroup`. See
    :ref:`plugin_developing` for a full example.

Which hook found a group determines where it shows up in the admin UI -
"FlaskBB Settings" for the internal hook, "Plugin Settings" for the plugin
hook - nothing about the group itself controls this.

Both hooks collect every implementation's return value (a single
``SettingGroup`` or a list of them); there's no ``firstresult``.

.. autoclass:: flaskbb.core.settings.definitions.SettingGroup
    :members:

Setting definitions
--------------------

A :class:`~flaskbb.core.settings.definitions.SettingDefinition` is never
used directly - pick the subclass matching the value's type. Each subclass
knows how to render itself as a WTForms field
(:meth:`~flaskbb.core.settings.definitions.SettingDefinition.wtf_field`) and
how to serialize/deserialize its value to/from the JSON text stored in the
DB.

================================================================= =========================================== =================
Definition                                                        Rendered As                                 Parsed & Saved as
================================================================= =========================================== =================
:class:`~flaskbb.core.settings.definitions.StringSetting`         :class:`wtforms.fields.StringField`         :class:`str`
:class:`~flaskbb.core.settings.definitions.IntSetting`            :class:`wtforms.fields.IntegerField`        :class:`int`
:class:`~flaskbb.core.settings.definitions.BoolSetting`           :class:`wtforms.fields.BooleanField`        :class:`bool`
:class:`~flaskbb.core.settings.definitions.SelectSetting`         :class:`wtforms.fields.SelectField`         single value
:class:`~flaskbb.core.settings.definitions.SelectMultipleSetting` :class:`wtforms.fields.SelectMultipleField` :class:`list`
================================================================= =========================================== =================

.. autoclass:: flaskbb.core.settings.definitions.SettingDefinition
    :members:

.. autoclass:: flaskbb.core.settings.definitions.StringSetting
    :members:

.. autoclass:: flaskbb.core.settings.definitions.IntSetting
    :members:

.. autoclass:: flaskbb.core.settings.definitions.BoolSetting
    :members:

.. autoclass:: flaskbb.core.settings.definitions.SelectSetting
    :members:

.. autoclass:: flaskbb.core.settings.definitions.SelectMultipleSetting
    :members:

Every definition takes ``key``, ``value`` (the default), ``name`` (human
readable label) and ``description``. ``StringSetting`` and ``IntSetting``
additionally accept optional ``min``/``max`` bounds (string length or
numeric range, validated via WTForms validators). ``SelectSetting`` and
``SelectMultipleSetting`` require a ``choices`` callable returning a list of
``(value, label)`` pairs, and accept an optional ``coerce`` type (defaults
to ``str``) to coerce the selected value(s).

Example::

    from flaskbb.core.settings import BoolSetting, IntSetting, SettingGroup

    SETTINGS = SettingGroup(
        key="my_plugin",
        name="My Plugin Settings",
        description="Settings for My Plugin.",
        settings=(
            BoolSetting(
                key="ENABLED",
                value=True,
                name="Enabled",
                description="Whether My Plugin is active.",
            ),
            IntSetting(
                key="RECENT_ITEMS",
                value=10,
                min=1,
                name="Number of Recent Items",
                description="How many items to show.",
            ),
        ),
    )

Setting keys
------------

A setting's key only has to be unique within its own group - uniqueness is
scoped to ``(group_key, key)``, not global. How a setting is exposed to the
rest of the app (config-style access, form field names) differs between
core and plugin settings, via
:func:`flaskbb.core.settings.models.display_key`:

* Core settings (registered through ``flaskbb_load_internal_setting_groups``)
  are exposed **unprefixed**: ``PROJECT_TITLE``.
* Plugin settings (registered through ``flaskbb_load_setting_groups``) are
  exposed **prefixed with their group key**, uppercased:
  ``PORTAL_FORUM_IDS`` for a setting keyed ``FORUM_IDS`` in the ``portal``
  group. This is what avoids collisions between plugins (and with core).

The registry
------------

.. autoclass:: flaskbb.core.settings.registry.SettingsRegistry
    :members:

The module-level singleton ``flaskbb.core.settings.setting_registry`` is
what every part of FlaskBB (admin forms, the settings model, the plugin
registry) queries against - plugins never construct their own registry.

Storage and the Setting model
------------------------------

.. note::
    For a full list of available methods, visit
    `Setting Model <models.html#flaskbb.core.settings.models.Setting>`__.

.. autoclass:: flaskbb.core.settings.models.Setting
    :members:
    :noindex:

Values are stored as JSON text (not ``PickleType``) - deliberately, to
avoid the arbitrary code execution risk of unpickling untrusted data, and
because every setting value type (``int``, ``bool``, ``str``, ``list[str]``)
is JSON-safe anyway.

The whole settings table is cached as a flat dict via
:meth:`~flaskbb.core.settings.models.Setting.as_dict`, keyed by each
setting's display key. Any write path
(:meth:`~flaskbb.core.settings.models.Setting.update`,
:meth:`~flaskbb.core.settings.models.Setting.install_group`,
:meth:`~flaskbb.core.settings.models.Setting.prune_group`,
:meth:`~flaskbb.core.settings.models.Setting.remove_group`) invalidates
this cache itself - never write ``Setting`` rows directly via the session
and skip these methods, or the cache will go stale.

Reading and writing settings at runtime
-----------------------------------------

Application code reads settings through the ``flaskbb_config`` proxy
(:class:`flaskbb.core.settings.proxy.FlaskBBConfigProxy`), which supports
both attribute and dict-style access against the cached values from
:meth:`~flaskbb.core.settings.models.Setting.as_dict`::

    from flaskbb.core.settings import flaskbb_config

    flaskbb_config.PROJECT_TITLE
    flaskbb_config["PROJECT_TITLE"]

Writing through the proxy (``flaskbb_config["KEY"] = value`` or
``flaskbb_config.update(...)``) resolves the display key back to its
``(group_key, key)`` pair and delegates to
:meth:`~flaskbb.core.settings.models.Setting.update`, so plugin settings
work the same way as core ones. Individual keys can't be deleted through
the proxy - a group's settings are tied to its lifecycle, removed together
via :meth:`~flaskbb.core.settings.models.Setting.remove_group` (e.g. on
plugin uninstall).
