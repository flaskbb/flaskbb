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


.. module:: flaskbb.management.models


.. autoclass:: Setting
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
