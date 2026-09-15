.. _faq:


FAQ - Frequently Asked Questions
================================

Here we try to answer some common questions and pitfalls about FlaskBB.

* Why do I get a ``AttributeError: 'NullTranslations' object has no attribute 'add'`` exception?

  This usually happens when you forgot to compile the translations.
  To compile them, just run::

    $ flaskbb translations compile

  Relevant issue: `#389 <https://github.com/sh4nks/flaskbb/issues/389>`_
