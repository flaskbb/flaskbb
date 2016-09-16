"""
    flaskbb.configs.development
    ~~~~~~~~~~~~~~~~~~~~

    This is the FlaskBB's development config.
    An extensive description for all those settings values
    is available in ``default.py``.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.configs.default import DefaultConfig


class DevelopmentConfig(DefaultConfig):

    # Indicates that it is a dev environment
    DEBUG = True

    # Prefer HTTP for development
    PREFERRED_URL_SCHEME = "http"

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DefaultConfig._basedir + '/' + \
                              'flaskbb.sqlite'

    # This will print all SQL statements
    SQLALCHEMY_ECHO = True

    # Security
    SECRET_KEY = "SecretKeyForSessionSigning"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "reallyhardtoguess"

    # Redis
    REDIS_ENABLED = False
    REDIS_URL = "redis://localhost:6379"

    # Local SMTP Server
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = ("FlaskBB Mailer", "noreply@example.org")

    ADMINS = ["your_admin_user@gmail.com"]
