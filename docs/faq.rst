.. _faq:


FAQ - Frequently Asked Questions
================================

Here we try to answer some common questions and pitfalls about FlaskBB.

* Why do I get a ``AttributeError: 'NullTranslations' object has no attribute 'add'`` exception?

  This usually happens when you forgot to compile the translations.
  To compile them, just run::

    $ flaskbb translations compile

  Relevant issue: `#389 <https://github.com/sh4nks/flaskbb/issues/389>`_

* Why isn't the cache (Flask-Caching) using the configured ``REDIS_URL``?

  You have to set the ``CACHE_REDIS_HOST`` to the ``REDIS_URL``. This is
  inconvenience is caused because you are not limited to redis as the caching
  backend. See the
  `Flask-Caching <https://pythonhosted.org/Flask-Caching/#configuring-flask-caching>`_
  documentation for a full list of caching backends.

  Relevant issue: `#372 <https://github.com/sh4nks/flaskbb/issues/372>`_
