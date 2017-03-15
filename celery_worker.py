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
import os
from flaskbb.app import create_app
from flaskbb.extensions import celery  # noqa

_basepath = os.path.dirname(os.path.abspath(__file__))
app = create_app(config=os.path.join(_basepath, 'flaskbb.cfg'))
