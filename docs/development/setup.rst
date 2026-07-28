.. _development-setup:

Development Setup
==================

-  `Setup & Prerequisites`_
-  `Installation`_
-  `Useful Development Commands`_


Setup & Prerequisites
----------------------

FlaskBB requires Python 3.12 or newer and uses `uv`_ to manage its Python
environment and dependencies - there's no separate virtualenv or pip step
to do by hand. This is the same first step whether you're setting up a
local development instance or deploying to production (see
:doc:`/production/deployment`).


.. _installing-uv:

Installing uv
~~~~~~~~~~~~~~

If you don't have `uv`_ installed yet, follow the `installation instructions
<https://docs.astral.sh/uv/getting-started/installation/>`_ for your
platform, for example::

    $ curl -LsSf https://astral.sh/uv/install.sh | sh

``uv`` will transparently download and manage the correct Python version for
you, so you don't need to install Python 3.12+ yourself first.


Installing Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

Once ``uv`` is installed, set up the project's virtual environment and
install all dependencies (including the development ones, e.g. pytest and
ruff) with a single command run from the FlaskBB root folder::

    $ uv sync

This creates a ``.venv`` folder and installs everything pinned in
``uv.lock``, including the ``dev`` dependency group. From then on, prefix any
Python/FlaskBB command with ``uv run`` (e.g. ``uv run flaskbb run``) to have
it execute inside that environment - or activate it directly with
``source .venv/bin/activate`` if you'd rather not type ``uv run`` every
time.

We have one optional dependency, redis (the python package is installed
automatically). It isn't required for local development - see :ref:`redis`
in the production deployment guide if you also want to test against it
locally.


Installation
-------------

Generate a development configuration - this sets ``DEBUG = True`` and a few
other developer-friendly defaults::

    uv run flaskbb makeconfig -d

or::

    uv run flaskbb makeconfig --development

You can also point at an existing (python) config file via an import string
instead of generating one, or use one of FlaskBB's default config objects.
Be sure that it is importable from within FlaskBB, for example::

    uv run flaskbb --config flaskbb.configs.default.DefaultConfig run

Run the guided install to create the database tables, default groups, and
your admin user::

    $ make install

or::

    uv run flaskbb install

During the installation process, you will be asked to provide a username,
email address and password for your administrator user.

Now you can either use ``make`` to run the development server::

    make run

or if you like to type a little bit more, the CLI::

    uv run flaskbb --config flaskbb.cfg run

Whenever you pull new code and the database models have changed, re-run the
migrations against your local database::

    uv run flaskbb db upgrade


Useful Development Commands
-----------------------------

Running the Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~

::

    make test

or directly with pytest, to run a single module, a single test, or a subset
by keyword::

    uv run pytest tests/unit/test_forum_models.py
    uv run pytest tests/unit/test_forum_models.py::test_topic_unread
    uv run pytest -k "plugin"

The suite runs in parallel via ``pytest-xdist`` by default - pass
``-p no:xdist`` or ``-n0`` to disable that. ``--pythonwarnings
error::flaskbb.deprecation.FlaskBBDeprecation`` (also set by default) turns
any use of a deprecated FlaskBB API into a test failure.


Linting & Formatting
~~~~~~~~~~~~~~~~~~~~~~

::

    make format

Runs ``ruff`` to sort/clean up imports, fix lint issues, and reformat the
code. Type checking is done separately with basedpyright (see ``tox -e
typing`` below).


Building the Docs
~~~~~~~~~~~~~~~~~~~

::

    make docs

or directly::

    uv run sphinx-build -b html docs docs/_build/html

The built HTML is written to ``docs/_build/html/index.html``.


Translations
~~~~~~~~~~~~~~

See :ref:`localization` for the full workflow. The short version, after
adding or changing a translatable string::

    uv run flaskbb translations update
    uv run flaskbb translations compile


Frontend (Aurora theme)
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    make frontend

Runs the webpack watcher for the default Aurora theme's JS/CSS under
``flaskbb/themes/aurora``.


Running Everything with tox
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``tox`` (configured in ``pyproject.toml``'s ``[tool.tox]`` section) runs the
test suite against every supported Python version plus the style, typing,
and docs checks in isolated environments - this is what CI runs::

    uv run tox

Run a single environment instead, e.g. just the type checker or the docs
build::

    uv run tox -e typing
    uv run tox -e docs


.. _uv: https://docs.astral.sh/uv/
