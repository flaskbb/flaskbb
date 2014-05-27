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


class DefaultConfig(object):

    # Get the app root path
    #            <_basedir>
    # ../../ -->  flaskbb/flaskbb/configs/base.py
    _basedir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
                            os.path.dirname(__file__)))))

    DEBUG = False
    TESTING = False

    # Logs
    # If SEND_LOGS is set to True, the admins (see the mail configuration) will
    # recieve the error logs per email.
    SEND_LOGS = False

    # The filename for the info and error logs. The logfiles are stored at
    # flaskbb/logs
    INFO_LOG = "info.log"
    ERROR_LOG = "error.log"

    # Default Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + _basedir + '/' + \
                              'flaskbb.sqlite'
    # sqlite for testing/debug.
    SQLALCHEMY_ECHO = False

    # Security
    # This is the secret key that is used for session signing.
    # You can generate a secure key with os.urandom(24)
    SECRET_KEY = 'secret key'

    # Protection against form post fraud
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "reallyhardtoguess"

    # Auth
    LOGIN_VIEW = "auth.login"
    REAUTH_VIEW = "auth.reauth"
    LOGIN_MESSAGE_CATEGORY = "error"

    # Caching
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 60

    ## Captcha
    RECAPTCHA_ENABLED = False
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = "your_public_recaptcha_key"
    RECAPTCHA_PRIVATE_KEY = "your_private_recaptcha_key"
    RECAPTCHA_OPTIONS = {"theme": "white"}

    ## Mail
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USE_TLS = False
    MAIL_USERNAME = "noreply@example.org"
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = ("Default Sender", "noreply@example.org")
    # Where to logger should send the emails to
    ADMINS = ["admin@example.org"]

    ## Flask-And-Redis
    REDIS_ENABLED = False
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    ## App specific configs
    # Pagination
    # How many posts per page are displayed
    POSTS_PER_PAGE = 10
    # How many topics per page are displayed
    TOPICS_PER_PAGE = 10
    # How many users per page are displayed.
    # This affects mainly the memberlist
    USERS_PER_PAGE = 10

    # How long the use can be inactive before he is marked as offline
    ONLINE_LAST_MINUTES = 15
    # The length of the topic title in characters on the index
    TITLE_LENGTH = 15

    # The days for how long the forum should deal with unread topics
    # 0 - Disable it
    TRACKER_LENGTH = 7

    FORUM_URL_PREFIX = ""
    USER_URL_PREFIX = "/user"
    AUTH_URL_PREFIX = "/auth"
    ADMIN_URL_PREFIX = "/admin"

    # Default style
    DEFAULT_THEME = "bootstrap3"

    # Your project name with a subtitle
    PROJECT_TITLE = "FlaskBB"
    PROJECT_SUBTITLE = "A lightweight forum software in flask"
