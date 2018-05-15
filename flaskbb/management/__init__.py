# -*- coding: utf-8 -*-
"""
    flaskbb.management
    ~~~~~~~~~~~~~~~~~~

    This module contains models, forms and views relevant
    for managing FlaskBB

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

# force plugins to be loaded
from . import plugins

__all__ = ('plugins', )

logger = logging.getLogger(__name__)
