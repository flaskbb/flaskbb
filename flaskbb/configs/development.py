"""
    flaskbb.configs.development
    ~~~~~~~~~~~~~~~~~~~~

    This is the FlaskBB's development config.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.configs.base import BaseConfig


class DevelopmentConfig(BaseConfig):

    # Indicates that it is a dev environment
    DEBUG = True
    SECRET_KEY = "SecretKeyForSessionSigning"

    # SQLAlchemy connection options
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + BaseConfig._basedir + '/' + \
                              BaseConfig.PROJECT + ".sqlite"
    SQLALCHEMY_ECHO = True

    # Protection against form post fraud
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = "reallyhardtoguess"

    # Caching
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 60

    # Recaptcha
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = "6LfUZ9YSAAAAANtDdyew22z2lnjz-K0Dx8M-gkey"
    RECAPTCHA_PRIVATE_KEY = "6LfUZ9YSAAAAAHgDBflMFQTVdlTA3__yYx8CBGII"
    RECAPTCHA_OPTIONS = {"theme": "white"}
