.. _hooks:

Hooks
=====

In FlaskBB we distinguish from `Python Hooks <#python-hooks>`_ and
`Template Hooks <#template-hooks>`_.
Python Hooks are prefixed with ``flaskbb_`` and called are called in Python
files whereas Template Hooks have to be prefixed with ``flaskbb_tpl_`` and are
executed in the templates.

If you miss a hook, feel free to open a new issue or create a pull
request. The pull request should always contain a entry in this document
with a small example.

A hook needs a hook specification which are defined in
:mod:`flaskbb.plugins.spec`. All hooks have to be prefixed with
``flaskbb_`` and template hooks with ``flaskbb_tpl_``.

Be sure to also check out the :ref:`api` documentation for interfaces that
interact with these plugins in interesting ways.


.. toctree::
   :maxdepth: 1

   startup
   cli
   event
   forms
   template
