"""
flaskbb
~~~~~~~

FlaskBB is a forum software written in python using the
microframework Flask.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging

from flaskbb._version import __version__ as __version__
from flaskbb.app import create_app as create_app

logger = logging.getLogger(__name__)
