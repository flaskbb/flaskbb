"""
flaskbb.configs.docker
~~~~~~~~~~~~~~~~~~~~~~

Configuration for the FlaskBB container images.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import os

from flaskbb.configs.default import DefaultConfig


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name) or default


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} has to be set, see docker/.env.example")
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


def _env_list(name: str) -> list[str] | None:
    return [item.strip() for item in _env(name).split(",") if item.strip()] or None


class DockerConfig(DefaultConfig):
    DEBUG = _env_bool("DEBUG", False)
    TESTING = False

    SERVER_NAME = _env("SERVER_NAME") or None
    TRUSTED_HOSTS = _env_list("TRUSTED_HOSTS")
    PREFERRED_URL_SCHEME = _env("URL_SCHEME", "http")
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", PREFERRED_URL_SCHEME == "https")
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True

    SECRET_KEY = _required_env("SECRET_KEY")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = _env("CSRF_SECRET_KEY", SECRET_KEY)

    SQLALCHEMY_DATABASE_URI = _required_env("DATABASE_URI")
    SQLALCHEMY_ECHO = _env_bool("SQLALCHEMY_ECHO", False)

    SEARCH_BACKEND = _env("SEARCH_BACKEND", "postgresql")

    _redis_enabled = _env_bool("REDIS_ENABLED", True)
    _redis_url = _env("REDIS_URL", "redis://redis:6379")

    CELERY_CONFIG = {
        "broker_url": _redis_url,
        "result_backend": _redis_url,
        "broker_transport_options": {"max_retries": 1},
    }

    CACHE_TYPE = "RedisCache" if _redis_enabled else "SimpleCache"
    CACHE_REDIS_URL = _redis_url
    CACHE_DEFAULT_TIMEOUT = 60

    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = _redis_url if _redis_enabled else "memory://"

    MAIL_SERVER = _env("MAIL_SERVER", "localhost")
    MAIL_PORT = _env_int("MAIL_PORT", 25)
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", False)
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = _env("MAIL_USERNAME")
    MAIL_PASSWORD = _env("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = (
        _env("MAIL_SENDER_NAME", "FlaskBB Mailer"),
        _env("MAIL_SENDER_ADDRESS", "noreply@example.org"),
    )
    ADMINS = [_env("MAIL_ADMIN_ADDRESS", "admin@example.org")]

    AVATAR_UPLOAD_PATH = _env("AVATAR_UPLOAD_PATH", "/var/lib/flaskbb/avatars")
    ATTACHMENT_UPLOAD_PATH = _env("ATTACHMENT_UPLOAD_PATH", "/var/lib/flaskbb/attachments")

    USE_DEFAULT_LOGGING = True
    LOG_CONF_FILE = None
    LOG_DEFAULT_CONF = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s %(levelname)-7s %(name)-25s %(message)s"},
        },
        "handlers": {
            "console": {
                "level": "NOTSET",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "flask.app": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True,
            },
            "flaskbb": {
                "handlers": ["console"],
                "level": _env("LOG_LEVEL", "WARNING"),
                "propagate": True,
            },
        },
    }

    DEPRECATION_LEVEL = _env("DEPRECATION_LEVEL", "default")
