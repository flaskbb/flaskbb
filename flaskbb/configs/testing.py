"""
    flaskbb.configs.testing
    ~~~~~~~~~~~~~~~~~~~~

    This is the FlaskBB's testing config.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.configs.default import DefaultConfig


class TestingConfig(DefaultConfig):

    # Indicates that it is a testing environment
    DEBUG = False
    TESTING = True

    SQLALCHEMY_DATABASE_URI = (
        'sqlite://'
    )

    SERVER_NAME = "localhost:5000"

    # This will print all SQL statements
    SQLALCHEMY_ECHO = False

    # Use the in-memory storage
    WHOOSHEE_MEMORY_STORAGE = True

    CELERY_ALWAYS_EAGER = True
    CELERY_RESULT_BACKEND = "cache"
    CELERY_CACHE_BACKEND = "memory"
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

    LOG_DEFAULT_CONF = {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)-7s %(name)-25s %(message)s'
            },
        },

        'handlers': {
            'console': {
                'level': 'NOTSET',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
        },

        # TESTING: Log to console only
        'loggers': {
            'flask.app': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            },
            'flaskbb': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False
            },
        }
    }
