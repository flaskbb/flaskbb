# -*- coding: utf-8 -*-
"""
    flaskbb.configs.default
    ~~~~~~~~~~~~~~~~~~~~~~~

    This is the default configuration for FlaskBB that every site should have.
    You can override these configuration variables in another class.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import datetime


class DefaultConfig(object):

    # Get the app root path
    #            <_basedir>
    # ../../ -->  flaskbb/flaskbb/configs/base.py
    basedir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
                           os.path.dirname(__file__)))))

    # Python version
    py_version = '{0.major}{0.minor}'.format(sys.version_info)

    # Flask Settings
    # ------------------------------
    # There is a whole bunch of more settings available here:
    # http://flask.pocoo.org/docs/0.11/config/#builtin-configuration-values
    DEBUG = False
    TESTING = False

    # Server Name
    # The name and port number of the server.
    # Required for subdomain support (e.g.: 'myapp.dev:5000') and
    # URL generation without a request context but with an application context
    # which we need in order to generate URLs (with the celery application)
    # Note that localhost does not support subdomains so setting this to
    # “localhost” does not help.
    # Example for the FlaskBB forums: SERVER_NAME = "forums.flaskbb.org"
    #SERVER_NAME =

    # The preferred url scheme. In a productive environment it is highly
    # recommended to use 'https'.
    # This only affects the url generation with 'url_for'.
    PREFERRED_URL_SCHEME = "http"

    # Logging Settings
    # ------------------------------
    # This config section will deal with the logging settings
    # for FlaskBB, adjust as needed.

    # Logging Config Path
    # see https://docs.python.org/library/logging.config.html#logging.config.fileConfig
    # for more details. Should either be None or a path to a file
    # If this is set to a path, consider setting USE_DEFAULT_LOGGING to False
    # otherwise there may be interactions between the log configuration file
    # and the default logging setting.
    #
    # If set to a file path, this should be an absolute file path
    LOG_CONF_FILE = None

    # Path to store the INFO and ERROR logs
    # If None this defaults to flaskbb/logs
    #
    # If set to a file path, this should be an absolute path
    LOG_PATH = os.path.join(basedir, 'logs')

    LOG_DEFAULT_CONF = {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)-7s %(name)-25s %(message)s'
            },
            'advanced': {
                'format': '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            }
        },

        'handlers': {
            'console': {
                'level': 'NOTSET',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'flaskbb': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_PATH, 'flaskbb.log'),
                'mode': 'a',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
            },

            'infolog': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_PATH, 'info.log'),
                'mode': 'a',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
            },
            'errorlog': {
                'level': 'ERROR',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_PATH, 'error.log'),
                'mode': 'a',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
            }
        },

        'loggers': {
            'flask.app': {
                'handlers': ['infolog', 'errorlog'],
                'level': 'INFO',
                'propagate': True
            },
            'flaskbb': {
                'handlers': ['console', 'flaskbb'],
                'level': 'WARNING',
                'propagate': True
            },
        }
    }

    # When set to True this will enable the default
    # FlaskBB logging configuration which uses the settings
    # below to determine logging
    USE_DEFAULT_LOGGING = True

    # If SEND_LOGS is set to True, the admins (see the mail configuration) will
    # recieve the error logs per email.
    SEND_LOGS = False

    # Database
    # ------------------------------
    # For PostgresSQL:
    #SQLALCHEMY_DATABASE_URI = "postgresql://flaskbb@localhost:5432/flaskbb"
    # For SQLite:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + basedir + '/' + \
                              'flaskbb.sqlite'

    # This option will be removed as soon as Flask-SQLAlchemy removes it.
    # At the moment it is just used to suppress the super annoying warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # This will print all SQL statements
    SQLALCHEMY_ECHO = False

    ALEMBIC = {
        'script_location': os.path.join(basedir, "migrations"),
        'version_locations': '',
        'file_template': '%%(year)d%%(month).2d%%(day).2d%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s'
    }
    ALEMBIC_CONTEXT = {
        'render_as_batch': True
    }

    # Security
    # ------------------------------
    # This is the secret key that is used for session signing.
    # You can generate a secure key with os.urandom(24)
    SECRET_KEY = 'secret key'

    # You can generate the WTF_CSRF_SECRET_KEY the same way as you have
    # generated the SECRET_KEY. If no WTF_CSRF_SECRET_KEY is provided, it will
    # use the SECRET_KEY.
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "reallyhardtoguess"

    # Full-Text-Search
    # ------------------------------
    # This will use the "whoosh_index" directory to store the search indexes
    WHOOSHEE_DIR = os.path.join(basedir, "whoosh_index", py_version)
    # How long should whooshee try to acquire write lock? (defaults to 2)
    WHOOSHEE_WRITER_TIMEOUT = 2
    # Minimum number of characters for the search (defaults to 3)
    WHOOSHEE_MIN_STRING_LEN = 3

    # Auth
    # ------------------------------
    LOGIN_VIEW = "auth.login"
    REAUTH_VIEW = "auth.reauth"
    LOGIN_MESSAGE_CATEGORY = "info"
    REFRESH_MESSAGE_CATEGORY = "info"

    # The name of the cookie to store the “remember me” information in.
    REMEMBER_COOKIE_NAME = "remember_token"
    # The amount of time before the cookie expires, as a datetime.timedelta object.
    REMEMBER_COOKIE_DURATION = datetime.timedelta(days=365)
    # If the “Remember Me” cookie should cross domains,
    # set the domain value here (i.e. .example.com would allow the cookie
    # to be used on all subdomains of example.com).
    REMEMBER_COOKIE_DOMAIN = None
    # Limits the “Remember Me” cookie to a certain path.
    REMEMBER_COOKIE_PATH = "/"
    # Restricts the “Remember Me” cookie’s scope to secure channels (typically HTTPS).
    REMEMBER_COOKIE_SECURE = None
    # Prevents the “Remember Me” cookie from being accessed by client-side scripts.
    REMEMBER_COOKIE_HTTPONLY = False

    # Rate Limiting via Flask-Limiter
    # -------------------------------
    # A full list with configuration values is available at the flask-limiter
    # docs, but you actually just need those settings below.
    # You can disabled the Rate Limiter here as well - it will overwrite
    # the setting from the admin panel!
    # RATELIMIT_ENABLED = True
    # You can choose from:
    #   memory:// (default)
    #   redis://host:port
    #   memcached://host:port
    # Using the redis storage requires the installation of the redis package,
    # which will be installed if you enable REDIS_ENABLE while memcached
    # relies on the pymemcache package.
    #RATELIMIT_STORAGE_URL = "redis://localhost:6379"

    # Caching
    # ------------------------------
    # For all available caching types, have a look at the Flask-Cache docs
    # https://pythonhosted.org/Flask-Caching/#configuring-flask-caching
    CACHE_TYPE = "simple"
    # For redis:
    #CACHE_TYPE = "redis"
    CACHE_DEFAULT_TIMEOUT = 60

    # Mail
    # ------------------------------
    # Google Mail Example
    #MAIL_SERVER = "smtp.gmail.com"
    #MAIL_PORT = 465
    #MAIL_USE_SSL = True
    #MAIL_USERNAME = "your_username@gmail.com"
    #MAIL_PASSWORD = "your_password"
    #MAIL_DEFAULT_SENDER = ("Your Name", "your_username@gmail.com")

    # Local SMTP Server
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USE_TLS = False
    MAIL_USERNAME = "noreply@example.org"
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = ("Default Sender", "noreply@example.org")
    # Where to logger should send the emails to
    ADMINS = ["admin@example.org"]

    # Redis
    # ------------------------------ #
    # If redis is enabled, it can be used for:
    #   - Sending non blocking emails via Celery (Task Queue)
    #   - Caching
    #   - Rate Limiting
    REDIS_ENABLED = False
    REDIS_URL = "redis://localhost:6379"  # or with a password: "redis://:password@localhost:6379"
    REDIS_DATABASE = 0

    # Celery
    CELERY_BROKER_URL = 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379'
    BROKER_TRANSPORT_OPTIONS = {'max_retries': 1}  # necessary as there's no default


    # FlaskBB Settings
    # ------------------------------ #
    # URL Prefixes
    FORUM_URL_PREFIX = ""
    USER_URL_PREFIX = "/user"
    MESSAGE_URL_PREFIX = "/message"
    AUTH_URL_PREFIX = "/auth"
    ADMIN_URL_PREFIX = "/admin"


    # Remove dead plugins - useful if you want to migrate your instance
    # somewhere else and forgot to reinstall the plugins.
    # If set to `False` it will NOT remove plugins that are NOT installed on
    # the filesystem (virtualenv, site-packages).
    REMOVE_DEAD_PLUGINS = False
