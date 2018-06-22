.. _releasing:

Releases
========

Releases for FlaskBB can be found on `pypi <https://pypi.org/project/FlaskBB>`_
as well as on `github <https://github.com/flaskbb/flaskbb>`_.

FlaskBB loosely follows semantic versioning (semver) where all releases in each
major version strive to be backwards compatible, though sometimes this will
be broken in order to apply a bugfix or security patch. When this occurs the
release notes will contain information about this.

Releases follow no particular cadence.


Branching and Tagging
~~~~~~~~~~~~~~~~~~~~~

Each release of FlaskBB will have a git tag such as ``v2.0.0`` as well as a
branch such as ``2.0.0``. Minor releases and patches reside in their major
version branch (e.g. version 2.0.1 resides in the 2.0.0 branch).

The ``master`` branch is always the latest version of FlaskBB and versions are
cut from this branch.

Feature and example branches may also be found in the official FlaskBB repo
but these are not considered release ready and may be unstable.

Deprecation Policy
~~~~~~~~~~~~~~~~~~

A release of FlaskBB may deprecate existing features and begin emitting
:class:`~flaskbb.deprecation.FlaskBBDeprecation` warnings.


These warnings are on by default and will announce for the first time each
deprecated usage is detected. If you want to ignore these warnings, this
behavior can be modified by setting ``DEPRECATION_LEVEL`` in your configuration
file or setting ``FLASKBB_DEPRECATION_LEVEL`` in your environment to a level
from the builtin warnings module.

For more details on interacting with warnings see
`the official documentation on warnings <https://docs.python.org/3/library/warnings.html>`_.


In general, a feature deprecated in a release will not be fully removed until
the next major version. For example, a feature deprecated in 2.1.0 would not
be removed until 3.0.0. There may be exceptions to this, such as if a deprecated
feature is found to be a security risk.

.. note::

    If you are developing on FlaskBB the level for FlaskBBDeprecation warnings
    is always set to ``error`` when running tests to ensure that deprecated
    behavior isn't being relied upon. If you absolutely need to downgrade to a
    non-exception level, use pytest's recwarn fixture and set the level with
    warnings.simplefilter


For more details on using deprecations in plugins or extensions, see :ref:`deprecations`.
