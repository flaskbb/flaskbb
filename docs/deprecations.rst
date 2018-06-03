.. _deprecations:

Deprecation Policy
==================

A release of FlaskBB may deprecate existing features and begin emitting
:class:`~flaskbb.deprecation.FlaskBBDeprecation` warnings.

These warnings are on by default and will announce for the first time each
deprecated usage is detected. If you want to ignore these warnings, this
behavior can be modified by setting ``DEPRECATION_LEVEL`` in your configuration
file or setting ``FLASKBB_DEPRECATION_LEVEL`` in your environment to a level
from the builtin warnings module.

For more details on interacting with warnings see
`the official documentation on warnings <https://docs.python.org/3/library/warnings.html>`_.


.. note::

    If you are developing on FlaskBB the level for FlaskBBDeprecation warnings
    is always set to ``error`` when running tests to ensure that deprecated
    behavior isn't being relied upon. If you absolutely need to downgrade to a
    non-exception level, use pytest's recwarn fixture and set the level with
    warnings.simplefilter


-- Insert Details of deprecation timeline --

I suggest following something like Django's policy of at least 2 feature
versions. But semvar suggests that backwards incompatible changes are a major
version bump. :shrug:


Deprecation Helpers
~~~~~~~~~~~~~~~~~~~

FlaskBB also publicly provides tools for handling deprecations as well and are
open to use by plugins or other extensions to FlaskBB.

.. module:: flaskbb.deprecation

.. autoclass:: FlaskBBWarning
.. autoclass:: FlaskBBDeprecation
.. autoclass:: RemovedInFlaskBB3
.. autofunction:: deprecated
