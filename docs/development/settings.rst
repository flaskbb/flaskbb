.. _settings:

Settings
========

This part covers which setting fields are available.
This is especially useful if you plan on develop a plugin a want to contribute
to FlaskBB.



The available fields are shown below.

.. note::
    For a full list of available methods, visit
    `Settings Model <models.html#flaskbb.management.models.Setting>`__.


.. autoclass:: flaskbb.utils.forms.SettingValueType
    :members:
    :undoc-members:


    ======================================== =========================================== =====================================
    Value Type                               Rendered As                                 Parsed & Saved as
    ======================================== =========================================== =====================================
    :attr:`~SettingValueType.string`         :class:`wtforms.fields.StringField`         :class:`str`
    :attr:`~SettingValueType.integer`        :class:`wtforms.fields.IntegerField`        :class:`int`
    :attr:`~SettingValueType.float`          :class:`wtforms.fields.FloatField`          :class:`float`
    :attr:`~SettingValueType.boolean`        :class:`wtforms.fields.BooleanField`        :class:`bool`
    :attr:`~SettingValueType.select`         :class:`wtforms.fields.SelectField`         :class:`list`
    :attr:`~SettingValueType.selectmultiple` :class:`wtforms.fields.SelectMultipleField` :class:`list`
    ======================================== =========================================== =====================================

    TODO

.. autoclass:: flaskbb.management.models
    :noindex:

    .. attribute:: key

    **TODO**

    .. attribute:: value

    **TODO**

    .. attribute:: settingsgroup

    **TODO**

    .. attribute:: name

    **TODO**

    .. attribute:: description

    **TODO**

    .. attribute:: value_type

    **TODO**
    string
    integer
    float
    boolean
    select          # 1 value
    selectmultiple  # multiple values

    .. attribute:: extra

    **TODO**
    min
    max
    choices with or without coerce
