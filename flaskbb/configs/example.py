"""
    flaskbb.configs.example
    ~~~~~~~~~~~~~~~~~~~~

    This is how a production configuration can look like.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.configs.base import BaseConfig


class ProductionConfig(BaseConfig):
    # Logs
    # If SEND_LOGS is set to True, the admins (see the mail configuration) will
    # recieve the error logs per email.
    SEND_LOGS = True

    # The filename for the info and error logs. The logfiles are stored at
    # flaskbb/logs
    INFO_LOG = "info.log"
    ERROR_LOG = "error.log"

    # This is the secret key that is used for session signing.
    # You can generate a secure key with os.urandom(24)
    SECRET_KEY = 'secret key'

    # SQLAlchemy connection options
    # If you want to use an other SQL service, gidf.
    #SQLALCHEMY_DATABASE_URI = "postgresql://localhost/example"

    # Protection against form post fraud
    # You can generate the CSRF_SESSION_KEY the same way as you have
    # generated the SECRET_KEY
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = "reallyhardtoguess"

    # Caching
    # See the Flask-Cache docs for more caching types
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 60

    # Recaptcha
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = "your_public_recaptcha_key"
    RECAPTCHA_PRIVATE_KEY = "your_private_recaptcha_key"
    RECAPTCHA_OPTIONS = {"theme": "white"}

    # Mail
    MAIL_SERVER = "yourmailserver"
    MAIL_PORT = 25
    MAIL_USERNAME = "Your Mailusername"
    MAIL_PASSWORD = ""
    DEFAULT_MAIL_SENDER = "your@emailadress.org"
    ADMINS = ["admin@example.org"]
