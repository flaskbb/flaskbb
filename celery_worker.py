#!/usr/bin/env python
"""
    flaskbb.celery_worker
    ~~~~~~~~~~~~~~~~~~~~~

    Prepares the celery app for the celery worker.
    To start celery, enter this in the console::

        celery -A celery_worker.celery --loglevel=info worker

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
try:
    from flaskbb.configs.production import ProductionConfig as Config
except ImportError:
    from flaskbb.configs.default import DefaultConfig as Config
from flaskbb.app import create_app
from flaskbb.extensions import celery

app = create_app(Config)
