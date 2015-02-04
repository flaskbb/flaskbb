"""
    flaskbb.configs.example
    ~~~~~~~~~~~~~~~~~~~~

    This is how a production configuration can look like.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.configs.default import DefaultConfig


class ProductionConfig(DefaultConfig):

    ## Database
    # If no SQL service is choosen, it will fallback to sqlite
    # For PostgresSQL:
    #SQLALCHEMY_DATABASE_URI = "postgresql://localhost/example"
    # For SQLite:
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DefaultConfig._basedir + '/' + \
    #                          'flaskbb.sqlite'

    ## Security
    # This is the secret key that is used for session signing.
    # You can generate a secure key with os.urandom(24)
    SECRET_KEY = 'secret key'

    # You can generate the WTF_CSRF_SECRET_KEY the same way as you have
    # generated the SECRET_KEY. If no WTF_CSRF_SECRET_KEY is provided, it will
    # use the SECRET_KEY.
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "reallyhardtoguess"


    ## Caching
    # For all available caching types, take a look at the Flask-Cache docs
    # https://pythonhosted.org/Flask-Cache/#configuring-flask-cache
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 60


    ## Captcha
    # To get recaptcha, visit the link below:
    # https://www.google.com/recaptcha/admin/create
    RECAPTCHA_ENABLED = False
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = "your_public_recaptcha_key"
    RECAPTCHA_PRIVATE_KEY = "your_private_recaptcha_key"
    RECAPTCHA_OPTIONS = {"theme": "white"}


    ## Mail
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


    ## Error/Info Logging
    # If SEND_LOGS is set to True, the admins (see the mail configuration) will
    # recieve the error logs per email.
    SEND_LOGS = False

    # The filename for the info and error logs. The logfiles are stored at
    # flaskbb/logs
    INFO_LOG = "info.log"
    ERROR_LOG = "error.log"

    # Flask-Redis
    REDIS_ENABLED = False
    REDIS_URL = "redis://:password@localhost:6379"
    REDIS_DATABASE = 0

    # URL Prefixes. Only change it when you know what you are doing.
    FORUM_URL_PREFIX = ""
    USER_URL_PREFIX = "/user"
    AUTH_URL_PREFIX = "/auth"
    ADMIN_URL_PREFIX = "/admin"
