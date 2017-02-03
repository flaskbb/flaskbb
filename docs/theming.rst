.. _theming:

Theming
=======

FlaskBB uses the `Flask-Themes2`_ extension for theming.


Quickstart
----------

1. Create a new folder within the ``themes/`` folder and give it the name
   of your theme.
2. Copy the content of the ``aurora/`` folder into your folder theme's folder.
3. Create **2** new folders called ``static/`` and ``templates/`` in your
   themes folder.
4. Copy ``layout.html`` from FlaskBB's ``templates/`` into your themes
   ``templates/`` folder and modified to your liking. Feel free to copy
   other templates over into your themes. Just make sure that they have the
   same name and directory structure to overwrite them.
5. Add some information about your theme using the ``info.json`` file.
6. Edit the ``package.json`` to your needs.
7. Happy theming!

In the end your folder structure should look like this::

    ── example_theme/
        ├── node_modules
        │   └── ...
        ├── src
        │   ├── img
        │   │   └── ...
        │   ├── js
        │   │   └── ...
        │   └── scss
        │       └── ...
        ├── static
        │   ├── img
        │   ├── css
        │   ├── fonts
        │   └── js
        ├── templates
        │   ├── ...
        │   └── layout.html
        ├── tools
        │   ├── build_css
        │   ├── build_fonts
        │   └── build_js
        ├── info.json
        ├── LICENSE
        ├── package.json
        └── README.md


Getting Started
---------------

A theme is simply a folder containing static media (like CSS files, images,
and JavaScript) and Jinja2 templates, with some metadata.
A theme folder should look something like this::

    my_theme
    ├── info.json
    ├── LICENSE
    ├── static
    │   └── style.css
    └── templates
        └── layout.html

Every theme needs to have a file called **info.json**. The info.json file
contains the theme’s metadata, so that the application can provide a nice
switching interface if necessary. For example, the info.json file for the
aurora theme looks like this:

.. sourcecode:: json

    {
        "application": "flaskbb",
        "identifier": "aurora",
        "name": "Aurora",
        "author": "Peter Justin",
        "license": "BSD 3-Clause",
        "website": "https://flaskbb.org",
        "description": "The default theme for FlaskBB.",
        "preview": "preview.png",
        "version": "1.0.0"
    }

Field Explanation
~~~~~~~~~~~~~~~~~

**application**
    The name of the application, in our case this should always be **flaskbb**.

**identifier**
    The unique name of your theme. This identifier should match the themes
    folder name!

**name**
    Human readable name of the theme.

**author**
    The name of the author.

**license**
    A short phrase describing the license, like "GPL", "BSD", "Public Domain",
    or "Creative Commons BY-SA 3.0". Every theme should define a license
    under which terms the theme can be used. You should also put a copy
    of the license in your themes directory (e.g. in a LICENSE file).

**description**
    A short description about your theme.
    For example: "A minimalistic blue theme".

**website**
    The URL of the theme’s Web site. This can be a Web site specifically
    for this theme, Web site for a collection of themes that includes
    this theme, or just the author’s Web site.

**preview**
    The theme's preview image, within the static folder.

**version**
    The version of the theme.


Templates
~~~~~~~~~

`Flask`_ and therefore also FlaskBB uses the `Jinja2`_ templating engine,
so you should read `its documentation <http://jinja.pocoo.org/docs/templates>`_
to learn about the actual syntax of the templates.

All templates are by default loaded from FlaskBB's ``templates/`` folder. In
order to create your own theme, you have to create a ``templates/`` folder in
your themes directory and optionally also copy the ``layout.html`` file from
FlaskBB's template folder over to yours. This ``layout.html`` file is your
starting point. Every template will extend it. If you want to overwrite other
templates, just copy them over from the templates folder and modify them
to your liking.

Each loaded template will have a global function named `theme`
available to look up the theme's templates. For example, if you want to
extend, import, or include another template from your theme, you can use
``theme(template_name)``, like this:

.. sourcecode:: html+jinja

    {% extends theme('layout.html') %}
    {% from theme('macros.html') import horizontal_field %}

.. note::

    If the template you requested **doesn't** exist within the theme, it will
    **fallback** to using the application's template.

If you pass `false` as the second parameter, it will only return the theme's template.

.. sourcecode:: html+jinja

    {# This template, for example, does not exist in FlaskBB #}
    {% include theme('header.html', false) %}

You can also explicitly import/include templates from FlaskBB. Just use the
tag without calling `theme`.

.. sourcecode:: html+jinja

    {% from 'macros.html' import topnav %}

You can also get the URL for the theme's media files with the `theme_static`
function:

.. sourcecode:: html+jinja

    <link rel=stylesheet href="{{ theme_static('style.css') }}">

To include the static files that FlaskBB ships with, you just proceed as
normal:

.. sourcecode:: html+jinja

    <link rel="stylesheet" href="{{ url_for('static', filename='css/pygments.css') }}">

If you want to get information about the currently active theme, you can do
that with the `theme_get_info` function:

.. sourcecode:: html+jinja

    This theme is <a href="{{ theme_get_info('website'}}">
      <b>{{ theme_get_info('name') }}</b>
    </a>


Advanced Example
-----------------

A more advanced example of a theme, is our own default theme called
**Aurora**. We do not have a ``layout.html`` file because we want to avoid code
duplication and are just falling back to the one that FlaskBB ships with in
its ``templates/`` folder. In order to use your own stylesheets you have to
create a ``layout.html`` file. It's probably the easiest to just copy the
``layout.html`` from FlaskBB's ``templates/`` folder into your themes
``templates/`` folder.

For example, the `forums <https://forums.flaskbb.org>`_ on FlaskBB are using
a slightly modified version of the Aurora theme. It is available on GitHub
here: `Aurora Mod <https://github.com/sh4nks/flaskbb-theme-aurora-mod>`_.
The modified version just adds a top navigation and uses a different footer.


Prerequisites
~~~~~~~~~~~~~

To use the same build tools, which we also use to develop the Aurora theme,
you have to make sure that you have npm installed. You can install npm by
following the official
`installation guide <https://docs.npmjs.com/getting-started/installing-node>`_.

The theme also uses `SASS <https://sass-lang.com/libsass>`_,
a CSS preprocessor, to make development easier. If you are not familar with
SASS but want to use it, which I can really recommend, follow this
`guide <http://sass-lang.com/guide>`_ to get a basic understanding of it.

As explained in `Field Explanation <#field-explanation>`_, each theme must
have a unique theme **identifier** - so open up ``info.json`` (from your
themes folder) with your favorite editor and adjust all the fields properly.

Next, do the same thing for the ``package.json`` file. This file is used by
npm to install some libraries like Bootstrap. A detailed explanation about
all the fields is available from `package.json documentation page`_.

To install the stated requirements in ``package.json`` just run the
``npm install`` command in the directory where the ``package.json`` file is
located. Now you have set up the toolchain which is used for the Aurora theme.


Toolchain Commands
~~~~~~~~~~~~~~~~~~

For the build, minify, etc. process we use npm's task runner. Just hit up
``npm run`` to get a list with all available commands. Following commands are
used::

    Usage
      npm run [TASK]

    Available tasks
      clean
        rm -f node_modules
      autoprefixer
        postcss -u autoprefixer -r static/css/*
      scss
        ./tools/build_css
      uglify
        ./tools/build_js
      imagemin
        imagemin src/img/* -o static/img
      fonts
        ./tools/build_fonts
      build:css
        npm run scss && npm run autoprefixer
      build:js
        npm run uglify
      build:images
        npm run imagemin && npm run fonts
      build:all
        npm run build:css && npm run build:js && npm run build:images
      watch:css
        onchange 'src/scss' -- npm run build:css
      watch:js
        onchange 'src/js' -- npm run build:js
      watch:all
        npm-run-all -p watch:css watch:js


For example, to watch for changes in our JS and SCSS files,
you just have to run::

    npm run watch:all

and upon changes it will automatically rebuild the files.


.. _Jinja2: http://jinja.pocoo.org/
.. _Flask: http://flask.pocoo.org/
.. _Flask-Themes2: https://flask-themes2.readthedocs.io/en/latest/
.. _package.json documentation page: https://docs.npmjs.com/files/package.json
