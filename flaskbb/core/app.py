"""
flaskbb.core.app
~~~~~~~~~~~~~~~~

The application class FlaskBB with its typed config.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from datetime import timedelta
from typing import Any, cast, NotRequired

from flask import Flask
from flask.config import Config
from typing_extensions import TypedDict


# mypy 2.3 has no PEP 728 support
class AppConfig(TypedDict, extra_items=Any):  # type: ignore[call-arg]
    # Flask
    DEBUG: bool
    TESTING: bool
    SERVER_NAME: str | None
    PREFERRED_URL_SCHEME: str
    ALLOWED_HOSTS: list[str] | None
    TRUSTED_HOSTS: list[str] | None
    MAX_CONTENT_LENGTH: int | None

    # Logging
    LOG_CONF_FILE: str | None
    LOG_PATH: str
    LOG_DEFAULT_CONF: dict[str, Any]
    USE_DEFAULT_LOGGING: bool
    SEND_LOGS: bool

    # Database
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool
    SQLALCHEMY_ECHO: bool
    ALEMBIC: dict[str, Any]
    ALEMBIC_CONTEXT: dict[str, Any]

    # Security
    SECRET_KEY: str
    WTF_CSRF_ENABLED: bool
    WTF_CSRF_SECRET_KEY: str

    # Search
    SEARCH_BACKEND: str

    # Forms
    WTF_I18N_ENABLED: bool

    # Auth
    LOGIN_VIEW: str
    REAUTH_VIEW: str
    LOGIN_MESSAGE_CATEGORY: str
    REFRESH_MESSAGE_CATEGORY: str
    REMEMBER_COOKIE_NAME: str
    REMEMBER_COOKIE_DURATION: timedelta
    REMEMBER_COOKIE_DOMAIN: str | None
    REMEMBER_COOKIE_PATH: str
    REMEMBER_COOKIE_SECURE: bool | None
    REMEMBER_COOKIE_HTTPONLY: bool

    # Caching
    CACHE_TYPE: str
    CACHE_DEFAULT_TIMEOUT: int

    # Mail
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USE_SSL: bool
    MAIL_USE_TLS: bool
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_DEFAULT_SENDER: str | tuple[str, str]
    ADMINS: list[str]

    # Redis
    REDIS_ENABLED: bool
    REDIS_URL: str
    REDIS_DATABASE: int

    # Celery
    CELERY_CONFIG: dict[str, Any]

    # URL prefixes
    FORUM_URL_PREFIX: str
    USER_URL_PREFIX: str
    UPLOAD_URL_PREFIX: str
    MESSAGE_URL_PREFIX: str
    AUTH_URL_PREFIX: str
    ADMIN_URL_PREFIX: str

    # Plugins
    REMOVE_DEAD_PLUGINS: bool

    # Uploads
    AVATAR_EXTENSIONS: list[str]
    AVATAR_UPLOAD_PATH: str | None
    ATTACHMENT_UPLOAD_PATH: str | None

    # Set by configure_app() rather than by DefaultConfig
    CONFIG_PATH: object
    DEBUG_TB_PANELS: list[str]
    DEPRECATION_LEVEL: NotRequired[str]


class FlaskBB(Flask):
    """Exists only to give ``app.config`` a static type.

    At runtime the config is still an ordinary :class:`flask.Config`;
    :class:`AppConfig` just describes what is in it. Use
    :data:`flaskbb.utils.proxies.current_app` to get the same typing off
    the context local.
    """

    config: AppConfig  # type: ignore[assignment]

    @property
    def raw_config(self) -> Config:
        """``app.config`` as the :class:`flask.Config` it actually is.

        :class:`AppConfig` describes the keys the config holds, not the
        loader API around them, so code that needs ``from_object``,
        ``from_pyfile``, ``get_namespace`` or writes under a key that isn't
        known statically has to go through this.
        """
        return cast(Config, self.config)  # pyright: ignore[reportInvalidCast]
