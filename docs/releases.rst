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

.. _making-a-release:

Making a Release
~~~~~~~~~~~~~~~~

A release is cut by pushing a version tag. Everything after the push is done
by the ``Publish`` workflow in ``.github/workflows/publish.yaml``, see
:ref:`publish-workflow`.

1. Check that the ``Tests``, ``Typing`` and ``pre-commit`` workflows are green
   on the commit you are about to tag. ``Publish`` does not run any of them.

2. Rebuild both themes and commit ``flaskbb/static`` and
   ``flaskbb/themes/aurora_dark/static`` if anything changed:

   .. code-block:: bash

       make frontend-build

   The wheel ships the compiled theme assets from the repository, the
   workflow does not build them. ``make frontend`` writes development builds,
   don't release those.

3. In ``CHANGES.md``, replace ``Unreleased`` below the version's heading with
   the release date, e.g. ``Released October 15th, 2026``.

4. Set ``__version__`` in ``flaskbb/_version.py`` to the new version. Hatchling
   reads the package version from this file.

5. Commit both files and create an annotated tag. The tag is the version with
   a ``v`` prefix and must match ``__version__``:

   .. code-block:: bash

       git commit -m "release version v3.0.0" CHANGES.md flaskbb/_version.py
       git tag -a v3.0.0 -m "release version v3.0.0"

6. Push the branch and the tag together, so that neither arrives without the
   other:

   .. code-block:: bash

       git push --atomic origin master v3.0.0

7. Follow the ``Publish`` run in the Actions tab of the repository. If the
   ``publish`` environment requires a reviewer, approve the deployment when
   the run waits for it.

8. When the run has finished, open the draft release the workflow created on
   GitHub, write the release notes and publish it. Mark release candidates as
   pre-releases.

.. warning::

    ``Publish`` runs for every tag that is pushed, not only version tags, and
    it does not compare the tag with ``__version__``. PyPI receives the version
    from ``flaskbb/_version.py``, while the Docker job derives the wheel's file
    name from the tag. If they differ, the Docker job fails after the upload
    to PyPI has already happened.

PyPI never accepts the same version twice. If something is wrong with a
release after it has been uploaded, fix it and release the next version
instead of moving the tag.

.. _publish-workflow:

The Publish Workflow
~~~~~~~~~~~~~~~~~~~~

``build``
    Builds the sdist and the wheel with ``uv build``. ``SOURCE_DATE_EPOCH`` is
    set to the commit date so that the build is reproducible. The build hook
    in ``hatch_build.py`` compiles the translations into the wheel.

``create-release``
    Creates a draft GitHub release for the tag and attaches the sdist and the
    wheel.

``publish-pypi``
    Uploads the sdist and the wheel to PyPI with trusted publishing, there is
    no API token. PyPI trusts the workflow by its file name ``publish.yaml``
    and the environment ``publish``, renaming either one requires updating the
    trusted publisher on PyPI.

``publish-docker``
    Runs after the upload to PyPI. Builds the release image
    (``docker/Dockerfile``) from the wheel for ``linux/amd64`` and
    ``linux/arm64`` and pushes it to ``ghcr.io/flaskbb/flaskbb``, once as it is
    and once with the ``plugins`` extra, which contains all official plugins.

The image tags follow the version. Pre-releases only get their exact version:

.. list-table::
   :header-rows: 1

   * - Tag
     - Image tags
   * - ``v3.0.0``
     - ``3.0.0``, ``3.0``, ``latest``, ``3.0.0-plugins``, ``3.0-plugins``,
       ``latest-plugins``
   * - ``v3.0.0rc4``
     - ``3.0.0rc4``, ``3.0.0rc4-plugins``

See :ref:`docker-deployment` for how the images are used.

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
