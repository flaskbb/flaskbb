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

What to mark for translation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Anything a forum user or admin might see in the browser: page text, flashed
messages, form labels/errors, emails. This includes the admin panel, not
just the public-facing forum.

CLI output (``flaskbb ...`` command help text) is **not**
translated.

Submitting your own translation alongside a string change
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're adding/changing a string and can also translate it into a
language you speak, go ahead and edit that language's ``messages.po``
directly in the same PR — run ``flaskbb translations update`` first so the
``msgid`` exists, then fill in your translation. Weblate merges against
whatever is already in the ``.po`` file rather than blindly overwriting it,
so your translation stays and simply shows up as already-translated (and
still editable) once Weblate picks up the change.

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
PRs against ``.po`` files directly. Weblate pulls :file:`messages.pot`
straight from this repository, so as soon as a PR that ran ``flaskbb
translations update`` is merged to master, the new/changed strings show up
on Weblate for translators without any separate upload step. Weblate opens
PRs back against this repository with translated ``.po`` files, so as a
developer the only thing you need to keep current is the ``.pot`` template
whenever you touch a translatable string - Weblate and its translators
handle the rest.

To sign up as a translator, create a `Weblate`_ account and join the
language you want to work on (or request a new one if it isn't listed yet).

Style and fixing existing translations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There's no formal style guide or glossary yet. FlaskBB doesn't have a
dedicated translation team, just whoever shows up on Weblate for a given
language. If you spot a string that's translated inconsistently or
incorrectly, just fix it directly in Weblate; there's no separate process
to coordinate with anyone first.

Context for ambiguous strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Weblate shows the source file and line number each ``msgid`` came from
(e.g. ``flaskbb/templates/auth/login.html:12``), which is usually enough to
tell whether e.g. "Login" is a button (verb) or a page/field label (noun).
If that's still ambiguous, the most reliable way to check is to run
FlaskBB locally and look at the string in place:

.. code-block:: console

    flaskbb translations compile
    flaskbb run

Then switch your account's language (or browser locale) to the one you're
testing so the app renders with your in-progress ``.po`` file — remember to
re-run ``flaskbb translations compile`` after every edit, since the app
only reads the compiled ``.mo`` file.

Review and release cadence
~~~~~~~~~~~~~~~~~~~~~~~~~~

FlaskBB currently has a single maintainer and no dedicated proofreading
step - translated PRs from Weblate get merged in as they come, on no fixed
schedule tied to releases. There's no deadline to hit for a given release;
translating at whatever pace works for you is fine.

Plugin translations
~~~~~~~~~~~~~~~~~~~~

The stock plugins (Portal, Conversations) aren't set up on Weblate yet.
For now, translating them means opening a PR directly against the plugin's
own ``translations/`` directory — see :ref:`plugin_translations`.


.. _Weblate: https://hosted.weblate.org/projects/flaskbb/flaskbb/
.. _Jinja: https://jinja.palletsprojects.com/en/stable/extensions/#i18n-extension

