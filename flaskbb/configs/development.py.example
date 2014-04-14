"""
    flaskbb.configs.development
    ~~~~~~~~~~~~~~~~~~~~

    This is the FlaskBB's development config.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.configs.default import DefaultConfig


class DevelopmentConfig(DefaultConfig):

    # Indicates that it is a dev environment
    DEBUG = True

    # SQLAlchemy connection options
    # This will create in the applications folder (where manage.py is)
    # a database named flaskbb.sqlite.
    #SQLALCHEMY_DATABASE_URI = "postgresql://flaskbb@localhost:5432/flaskbb"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DefaultConfig._basedir + '/' + \
                              'flaskbb.sqlite'

    # This will print all SQL statements
    SQLALCHEMY_ECHO = True

    # Security
    SECRET_KEY = "SecretKeyForSessionSigning"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "reallyhardtoguess"

    # Recaptcha
    # To get recaptcha, visit the link below:
    # https://www.google.com/recaptcha/admin/create
    # Those keys are only going to work on localhost!
    RECAPTCHA_ENABLED = True
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = "6LcZB-0SAAAAAGIddBuSFU9aBpHKDa16p5gSqnxK"
    RECAPTCHA_PRIVATE_KEY = "6LcZB-0SAAAAAPuPHhazscMJYa2mBe7MJSoWXrUu"
    RECAPTCHA_OPTIONS = {"theme": "white"}

    # Mail
    # Local SMTP Server
    #MAIL_SERVER = "localhost"
    #MAIL_PORT = 25
    #MAIL_USE_SSL = False
    #MAIL_USERNAME = ""
    #MAIL_PASSWORD = ""
    #MAIL_DEFAULT_SENDER = "noreply@example.org"

    # Google Mail Example
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = "your_username@gmail.com"
    MAIL_PASSWORD = "your_password"
    MAIL_DEFAULT_SENDER = ("Your Name", "your_username@gmail.com")

    # The user who should recieve the error logs
    ADMINS = ["your_admin_user@gmail.com"]
