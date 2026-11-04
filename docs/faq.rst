.. _faq:


FAQ - Frequently Asked Questions
================================

Here we try to answer some common questions and pitfalls about FlaskBB.

* Why do I get a ``AttributeError: 'NullTranslations' object has no attribute 'add'`` exception?

  This usually happens when you forgot to compile the translations.
  To compile them, just run::

    $ flaskbb translations compile

  Relevant issue: `#389 <https://github.com/sh4nks/flaskbb/issues/389>`_

* Does FlaskBB support sub-categories (nested forums)?

  No. Forums and categories in FlaskBB are intentionally flat: a forum
  belongs directly to a category, and categories cannot be nested inside
  other categories. If you need a deeper hierarchy, organize it with
  separate categories and descriptive forum names.

  Relevant issue: `#450 <https://github.com/flaskbb/flaskbb/issues/450>`_
