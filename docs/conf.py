# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("_themes"))


# -- Project information -----------------------------------------------------
project = u'FlaskBB'
copyright = u'2021, Peter Justin'
author = u'Peter Justin'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

html_theme_options = {
    'logo': 'logo-full.png',
    'github_banner': True,
    'github_user': 'sh4nks',
    'github_repo': 'flaskbb',
    'github_type': 'star',
    'description': ("FlaskBB is a simple and extensible forum software "
                    "for building communities."),
    'fixed_sidebar': True,
    'show_related': True
}

# The name for this set of Sphinx documents.
# "<project> v<release> documentation" by default.
#
html_title = u'FlaskBB Documentation'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    'index': [
        'about.html',
        'sidebarintro.html',
        'sourcelink.html',
        'searchbox.html'
    ],
    '**': [
        'about.html',
        'localtoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html'
    ]
}
html_show_sourcelink = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'flask': ('https://flask.palletsprojects.com/en/latest/', None),
    'werkzeug': ('https://werkzeug.palletsprojects.com/en/latest/', None),
    'click': ('https://click.palletsprojects.com/en/latest/', None),
    'jinja': ('https://jinja.palletsprojects.com/en/latest/', None),
    'wtforms': ('https://wtforms.readthedocs.io/en/master/', None),
}

autodoc_member_order = 'bysource'
