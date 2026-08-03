.. _plugin_development_editor:

Extending the Markdown Editor
=============================

A plugin that adds a markdown directive through
:func:`~flaskbb.plugins.spec.flaskbb_load_post_markdown_class` or
:func:`~flaskbb.plugins.spec.flaskbb_load_post_markdown_plugins` usually
wants two more things: an entry in the editor's cheatsheet so users can find
out the directive exists, and a button on the editor's toolbar. There is one
hook for each.

Both hooks return an HTML fragment which is inserted into the page as-is.
Escaping is the plugin's job; rendering the fragment through
:func:`~flask.render_template` or
:func:`~flask.render_template_string` takes care of it.


Documenting a directive
-----------------------

:func:`~flaskbb.plugins.spec.flaskbb_tpl_markdown_cheatsheet` appends to the
cheatsheet modal that the editor's question mark button opens. The fragment
should bring its own heading:

.. sourcecode:: python

    @hookimpl
    def flaskbb_tpl_markdown_cheatsheet():
        return render_template("spoiler/cheatsheet.html")

.. sourcecode:: html+jinja

    <h2>Spoilers</h2>
    <p class="text-center">||<span class="spoiler">hidden text</span>||</p>


Adding a toolbar button
-----------------------

:func:`~flaskbb.plugins.spec.flaskbb_tpl_markdown_toolbar_buttons` inserts
into the ``<markdown-toolbar>`` element, after FlaskBB's own buttons. What
the fragment has to contain depends on how complicated the button is.


Wrapping the selection in fixed text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the common case and needs no JavaScript at all. The ``<md-custom>``
element, which ships with FlaskBB's markdown toolbar component, is
configured entirely from markup:

.. sourcecode:: python

    @hookimpl
    def flaskbb_tpl_markdown_toolbar_buttons():
        return render_template("spoiler/toolbar_button.html")

.. sourcecode:: html+jinja

    <div class="btn-group btn-group-sm me-2">
        <md-custom class="btn btn-white"
                   data-md-prefix="||"
                   data-md-placeholder="{{ _('spoiler') }}"
                   data-tooltip="tooltip" title="{{ _('Spoiler') }}">
            <span class="fas fa-eye-slash"></span>
        </md-custom>
    </div>

``<md-custom>`` reads these attributes:

``data-md-prefix``
    Text inserted before the selection.

``data-md-suffix``
    Text inserted after the selection. Defaults to ``data-md-prefix``, so a
    symmetric directive only needs the prefix. Set it to ``""`` for a
    directive that has no closing marker.

``data-md-insert``
    Insert this text as a block of its own instead of wrapping the
    selection, for directives that do not take content (``[TOC]``, a
    horizontal rule, a table skeleton). Blank lines are added around it as
    needed, and it overrides prefix and suffix.

``data-md-placeholder``
    Inserted between prefix and suffix, and left selected, when the button
    is clicked without a selection. Without it, an empty selection produces
    just the prefix and suffix with the cursor between them - which is how
    the built-in bold and italic buttons behave.

Clicking the button again on text it already wrapped removes the markup, the
same way ``<md-bold>`` does.


Anything more involved
~~~~~~~~~~~~~~~~~~~~~~

A button that prefixes every selected line, or that opens a dialog before
inserting anything, needs its own custom element subclassing
``MarkdownButtonElement``. Ship it as a static file of your plugin:

.. sourcecode:: javascript

    class SpoilerCalloutElement extends window.MarkdownButtonElement {
      connectedCallback() {
        super.connectedCallback()
        this.markdownStyle = {
          prefix: '!> ',
          multiline: true,
          surroundWithNewlines: true
        }
      }
    }

    customElements.define('spoiler-callout', SpoilerCalloutElement)

Two things a subclass must do:

* Assign ``this.markdownStyle``. A button with no style assigned does
  nothing when clicked. ``connectedCallback()`` is the right place -
  attributes are readable there.
* Call ``super.connectedCallback()``. That sets ``role="button"`` and
  enrolls the element in the toolbar's keyboard navigation. If for some
  reason you cannot, put ``data-md-toolbar-button`` on the element in your
  markup instead.

The available ``markdownStyle`` fields are documented in the
`markdown-toolbar-element README
<https://github.com/flaskbb/markdown-toolbar-element#custom-buttons>`_.

Custom element names are global to the page, and
``customElements.define`` throws if a name is already taken. Prefix yours
with your plugin's name - ``spoiler-callout``, not ``callout`` - so two
plugins cannot collide. Do not use the ``md-`` prefix, that namespace
belongs to the toolbar component.

The element is registered by a script, which the plugin loads through
:func:`~flaskbb.plugins.spec.flaskbb_tpl_scripts`:

.. sourcecode:: python

    @hookimpl
    def flaskbb_load_blueprints(app):
        app.register_blueprint(spoiler, url_prefix="/spoiler")


    @hookimpl
    def flaskbb_tpl_scripts():
        return render_template_string(
            '<script src="{{ url_for("spoiler.static", '
            'filename="spoiler.js") }}"></script>'
        )

.. sourcecode:: python

    spoiler = Blueprint(
        "spoiler", __name__, template_folder="templates", static_folder="static"
    )

:func:`~flaskbb.plugins.spec.flaskbb_tpl_scripts` renders at the end of the
``<body>``, after the toolbar markup has been parsed. That is not a problem:
a custom element already in the document is upgraded as soon as
``customElements.define`` runs for its tag name. Until then - and permanently,
if the script fails to load - the button is inert, and the toolbar's
keyboard navigation skips over it instead of stopping on a button that
cannot do anything.


A complete example
------------------

Putting all of it together, a plugin that adds a ``||spoiler||`` directive
with both kinds of button:

.. sourcecode:: text

    flaskbb_plugin_spoiler
    |-- pyproject.toml
    |-- flaskbb_plugin_spoiler
        |-- __init__.py
        |-- views.py
        |-- static
        |   |-- spoiler.js
        |-- templates
            |-- spoiler
                |-- cheatsheet.html
                |-- toolbar_buttons.html

``views.py``:

.. sourcecode:: python

    from flask import Blueprint

    spoiler = Blueprint(
        "spoiler", __name__, template_folder="templates", static_folder="static"
    )

``__init__.py``:

.. sourcecode:: python

    from flask import render_template, render_template_string
    from pluggy import HookimplMarker

    from .views import spoiler

    hookimpl = HookimplMarker("flaskbb")


    @hookimpl
    def flaskbb_load_blueprints(app):
        app.register_blueprint(spoiler, url_prefix="/spoiler")


    @hookimpl
    def flaskbb_tpl_markdown_cheatsheet():
        return render_template("spoiler/cheatsheet.html")


    @hookimpl
    def flaskbb_tpl_markdown_toolbar_buttons():
        return render_template("spoiler/toolbar_buttons.html")


    @hookimpl
    def flaskbb_tpl_scripts():
        return render_template_string(
            '<script src="{{ url_for("spoiler.static", '
            'filename="spoiler.js") }}"></script>'
        )

``templates/spoiler/cheatsheet.html``:

.. sourcecode:: html+jinja

    <h2>{{ _("Spoilers") }}</h2>
    <p class="text-center">||{{ _("hidden inline text") }}||</p>
    <p class="text-center">!> {{ _("a hidden paragraph") }}</p>

``templates/spoiler/toolbar_buttons.html``:

.. sourcecode:: html+jinja

    <div class="btn-group btn-group-sm me-2">
        <md-custom class="btn btn-white"
                   data-md-prefix="||"
                   data-md-placeholder="{{ _('spoiler') }}"
                   data-tooltip="tooltip" title="{{ _('Spoiler') }}">
            <span class="fas fa-eye-slash"></span>
        </md-custom>
        <spoiler-callout class="btn btn-white"
                         data-tooltip="tooltip" title="{{ _('Spoiler block') }}">
            <span class="fas fa-eye-slash"></span>
        </spoiler-callout>
    </div>

``static/spoiler.js``:

.. sourcecode:: javascript

    class SpoilerCalloutElement extends window.MarkdownButtonElement {
      connectedCallback() {
        super.connectedCallback()
        this.markdownStyle = {
          prefix: '!> ',
          multiline: true,
          surroundWithNewlines: true
        }
      }
    }

    customElements.define('spoiler-callout', SpoilerCalloutElement)

Rendering the directive itself is a separate concern - see
:func:`~flaskbb.plugins.spec.flaskbb_load_post_markdown_class` and
:func:`~flaskbb.plugins.spec.flaskbb_load_post_markdown_plugins`.
