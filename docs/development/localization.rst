.. _localization:

Localization
============

FlaskBB's uses `Weblate`_ for crowdsourced translations.

There are two separate audiences for this workflow:

* **Translators** who just want to translate existing strings into a
  language they speak. These contributors should use Weblate directly and
  never need to touch the CLI or a local checkout.
* **Developers** who add or change translatable strings in the code, or who
  need to add support for a language that doesn't have a translation yet.
* **Plugin Developers** see the dedicated translations page :ref:`plugin_translations`.


Getting Started
---------------

Which files Babel scans, and how, is configured in :file:`babel.cfg` at the
project root:

.. code-block:: ini

    [python: **/flaskbb/**.py]
    [jinja2: **/templates/**.html]

In Python code, wrap user-facing strings in ``gettext``/``lazy_gettext``
from ``flask_babelplus`` (conventionally aliased to ``_``):

.. code-block:: python

    from flask_babelplus import gettext as _

    flash(_("You have been logged in."), "success")

Use ``lazy_gettext`` instead of ``gettext`` for strings evaluated outside of
a request context (e.g. form labels defined at class-body scope), since it
defers translation until the string is actually rendered.

In Jinja templates, the ``gettext``/``ngettext`` helpers  or the
``{% trans %}{% endtrans %}`` blocks. See the `Jinja`_ documentation to see a complete
list of available translation functions.

.. code-block:: jinja

    <button>{{ gettext("Submit") }}</button>
    <button>{% trans "Submit" endtrans%}</button>

Plugins register their own translation directories via the
:func:`flaskbb_load_translations
<flaskbb.plugins.spec.flaskbb_load_translations>` hook so their strings are
merged into the active locale alongside core FlaskBB's. See
:ref:`plugin_translations` for the plugin-specific workflow.

Adding new Languages
--------------------

Core translations live under :file:`flaskbb/translations/<lang>/LC_MESSAGES`,
one directory per language code (e.g. ``de``, ``pt_BR``). A plugin's
translations live the same way under its own ``translations/`` directory.
The ``flaskbb translations`` CLI group (see :ref:`the CLI reference
<commandline>`) drives the underlying ``pybabel`` calls:

``flaskbb translations new LANG``
    Extracts all marked strings into :file:`messages.pot` and creates a new
    :file:`LANG/LC_MESSAGES/messages.po` for translators to fill in. Only
    needed once per language. Pass ``--plugin NAME`` to add a language to a
    plugin instead of core.

``flaskbb translations update [--all] [--plugin NAME]``
    Re-extracts strings from the source and merges any new/changed/removed
    ``msgid``\ s into every existing ``.po`` file. Run this after adding or
    changing translatable strings in code, before compiling. ``--all`` also
    updates every installed plugin's translations; ``--plugin NAME`` updates
    just one plugin.

``flaskbb translations compile [--all] [--plugin NAME]``
    Compiles every ``.po`` file into the binary ``.mo`` format Flask-BabelPlus
    actually loads at runtime. Run this after editing a ``.po`` file, or the
    changes won't show up in the app.

A typical loop while adding a new string is::

    flaskbb translations update
    # edit flaskbb/translations/<lang>/LC_MESSAGES/messages.po by hand, or
    # let Weblate pick up the new msgid from messages.pot
    flaskbb translations compile

Weblate
-------

Translators contribute through `Weblate`_ instead of opening
PRs against ``.po`` files directly. Weblate tracks :file:`messages.pot` and
opens PRs back against this repository with translated ``.po`` files, so as
a developer the only thing you need to keep current is the ``.pot``
template (via ``flaskbb translations update``) whenever you touch a
translatable string — Weblate and its translators handle the rest.


.. _Weblate: https://hosted.weblate.org/projects/flaskbb/flaskbb/
.. _Jinja: https://jinja.palletsprojects.com/en/stable/extensions/#i18n-extension

