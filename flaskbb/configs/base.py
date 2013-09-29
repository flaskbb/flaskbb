# -*- coding: utf-8 -*-
"""
    flaskbb.configs.base
    ~~~~~~~~~~~~~~~~~~~~

    This is the base configuration for FlaskBB that every site should have.
    You can override these configuration variables in another class.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os


class BaseConfig(object):

    # Get the app root path
    #            <_basedir>
    # ../../ -->  flaskbb/flaskbb/configs/base.py
    _basedir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
                            os.path.dirname(__file__)))))

    PROJECT = "flaskbb"
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

    # This is the secret key that is used for session signing.
    # You can generate a secure key with os.urandom(24)
    SECRET_KEY = 'secret key'

    # SQLAlchemy connection options
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + _basedir + '/' + \
                              PROJECT + ".sqlite"
    # sqlite for testing/debug.
    SQLALCHEMY_ECHO = True

    # Protection against form post fraud
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SESSION_KEY = "reallyhardtoguess"

    # Auth
    LOGIN_VIEW = "auth.login"
    REAUTH_VIEW = "auth.reauth"

    # Caching
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 60

    # Recaptcha
    RECAPTCHA_ENABLE = False

    # Pagination
    POSTS_PER_PAGE = 10
    TOPICS_PER_PAGE = 10
    USERS_PER_PAGE = 10

    LAST_SEEN = 15
