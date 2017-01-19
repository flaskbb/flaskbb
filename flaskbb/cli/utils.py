# -*- coding: utf-8 -*-
"""
    flaskbb.cli.utils
    ~~~~~~~~~~~~~~~~~

    This module contains some utility helpers that are used across
    commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import re
import binascii

import click

from flask import current_app, __version__ as flask_version
from flask_themes2 import get_theme

from flaskbb import __version__
from flaskbb.extensions import plugin_manager
from flaskbb.utils.populate import create_user, update_user


cookiecutter_available = False
try:
    from cookiecutter.main import cookiecutter
    cookiecutter_available = True
except ImportError:
    pass

_email_regex = r"[^@]+@[^@]+\.[^@]+"


class FlaskBBCLIError(click.ClickException):
    """An exception that signals a usage error including color support.
    This aborts any further handling.

    :param styles: The style kwargs which should be forwarded to click.secho.
    """

    def __init__(self, message, **styles):
        click.ClickException.__init__(self, message)
        self.styles = styles

    def show(self, file=None):
        if file is None:
            file = click._compat.get_text_stderr()
        click.secho("[-] Error: %s" % self.format_message(), file=file,
                    **self.styles)


class EmailType(click.ParamType):
    """The choice type allows a value to be checked against a fixed set of
    supported values.  All of these values have to be strings.
    See :ref:`choice-opts` for an example.
    """
    name = "email"

    def convert(self, value, param, ctx):
        # Exact match
        if re.match(_email_regex, value):
            return value
        else:
            self.fail(("invalid email: %s" % value), param, ctx)

    def __repr__(self):
        return "email"


def save_user_prompt(username, email, password, group, only_update=False):
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"), type=str,
            default=os.environ.get("USER", "")
        )
    if not email:
        email = click.prompt(
            click.style("Email address", fg="magenta"), type=EmailType()
        )
    if not password:
        password = click.prompt(
            click.style("Password", fg="magenta"), hide_input=True,
            confirmation_prompt=True
        )
    if not group:
        group = click.prompt(
            click.style("Group", fg="magenta"),
            type=click.Choice(["admin", "super_mod", "mod", "member"]),
            default="admin"
        )

    if only_update:
        return update_user(username, password, email, group)
    return create_user(username, password, email, group)


def validate_plugin(plugin):
    """Checks if a plugin is installed.
    TODO: Figure out how to use this in a callback. Doesn't work because
          the appcontext can't be found and using with_appcontext doesn't
          help either.
    """
    if plugin not in plugin_manager.all_plugins.keys():
        raise FlaskBBCLIError("Plugin {} not found.".format(plugin), fg="red")
    return True


def validate_theme(theme):
    """Checks if a theme is installed."""
    try:
        get_theme(theme)
    except KeyError:
        raise FlaskBBCLIError("Theme {} not found.".format(theme), fg="red")


def check_cookiecutter(ctx, param, value):
    if not cookiecutter_available:
        raise FlaskBBCLIError(
            "Can't create {} because cookiecutter is not installed. "
            "You can install it with 'pip install cookiecutter'.".
            format(value), fg="red"
        )
    return value


def get_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    message = ("FlaskBB %(version)s using Flask %(flask_version)s on "
               "Python %(python_version)s")
    click.echo(message % {
        'version': __version__,
        'flask_version': flask_version,
        'python_version': sys.version.split("\n")[0]
    }, color=ctx.color)
    ctx.exit()


CONFIG_TEMPLATE = """
import os
import datetime
from flaskbb.configs.default import DefaultConfig

# Flask Settings
# ------------------------------
# There is a whole bunch of more settings available here:
# http://flask.pocoo.org/docs/0.11/config/#builtin-configuration-values
DEBUG = {is_debug}
TESTING = False

# Server Name - REQUIRED for Celery/Mailing
# The name and port number of the server.
# Required for subdomain support (e.g.: 'myapp.dev:5000') and
# URL generation without a request context but with an application context
# which we need in order to generate URLs (with the celery application)
# Note that localhost does not support subdomains so setting this to
# “localhost” does not help.
# Example for the FlaskBB forums: SERVER_NAME = "forums.flaskbb.org"
SERVER_NAME = {server_name}

# Prefer HTTPS over HTTP
PREFERRED_URL_SCHEME = "{url_scheme}"

# If SEND_LOGS is set to True, the admins (see the mail configuration) will
# recieve the error logs per email.
SEND_LOGS = False

# The filename for the info and error logs. The logfiles are stored at
# flaskbb/logs
INFO_LOG = "info.log"
ERROR_LOG = "error.log"

# Database
# ------------------------------
#SQLALCHEMY_DATABASE_URI = "{database_url}"

# This option will be removed as soon as Flask-SQLAlchemy removes it.
# At the moment it is just used to suppress the super annoying warning
SQLALCHEMY_TRACK_MODIFICATIONS = False
# This will print all SQL statements
SQLALCHEMY_ECHO = False

# Security - IMPORTANT
# ------------------------------
# This is the secret key that is used for session signing.
# You can generate a secure key with os.urandom(24)
SECRET_KEY = "{secret_key}"

# You can generate the WTF_CSRF_SECRET_KEY the same way as you have
# generated the SECRET_KEY. If no WTF_CSRF_SECRET_KEY is provided, it will
# use the SECRET_KEY.
WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = "{csrf_secret_key}"

# Full-Text-Search
# ------------------------------
# This will use the "whoosh_index" directory to store the search indexes
WHOOSHEE_DIR = os.path.join(DefaultConfig._basedir, "whoosh_index", DefaultConfig._version_str)
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
# Default: 365 days (1 non-leap Gregorian year)
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

# Redis
# ------------------------------
# If redis is enabled, it can be used for:
#   - Sending non blocking emails via Celery (Task Queue)
#   - Caching
#   - Rate Limiting
REDIS_ENABLED = {use_redis}
REDIS_URL = {redis_url}
REDIS_DATABASE = 0

# Celery
# ------------------------------
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

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
RATELIMIT_STORAGE_URL = REDIS_URL

# Caching
# ------------------------------
# For all available caching types, have a look at the Flask-Cache docs
# https://pythonhosted.org/Flask-Caching/#configuring-flask-caching
CACHE_TYPE = "simple" if not REDIS_ENABLED else "redis"
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
MAIL_SERVER = "{mail_server}"
MAIL_PORT = {mail_port}
MAIL_USE_SSL = {mail_use_ssl}
MAIL_USE_TLS = {mail_use_tls}
MAIL_USERNAME = "{mail_username}"
MAIL_PASSWORD = "{mail_password}"
MAIL_DEFAULT_SENDER = ("{mail_sender_name}", "{mail_sender_address}")
# Where to logger should send the emails to
ADMINS = ["{mail_admin_address}"]

# FlaskBB Settings
# ------------------------------ #
# URL Prefixes
FORUM_URL_PREFIX = ""
USER_URL_PREFIX = "/user"
MESSAGE_URL_PREFIX = "/message"
AUTH_URL_PREFIX = "/auth"
ADMIN_URL_PREFIX = "/admin"
"""
