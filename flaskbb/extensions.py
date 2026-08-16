"""
flaskbb.extensions
~~~~~~~~~~~~~~~~~~

The extensions that are used by FlaskBB.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import sqlite3
from typing import Any

from celery import Celery
from flask_allows2 import Allows
from flask_babelplus import Babel
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_themes2 import Themes
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event, MetaData
from sqlalchemy.engine import Engine

from flaskbb.core.search import FlaskBBSearch
from flaskbb.exceptions import AuthorizationRequired
from flaskbb.plugins.manager import FlaskBBPluginManager
from flaskbb.utils.alembic import Alembic

# PluginManager
pluggy = FlaskBBPluginManager("flaskbb")

# Permissions Manager
allows = Allows(throws=AuthorizationRequired)

# Database
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
db = SQLAlchemy(metadata=metadata, session_options={"future": True})


def _enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    """SQLite ignores ``ON DELETE CASCADE`` unless foreign keys are enabled per
    connection, which would leave orphaned rows behind on every delete.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        # the sqlite3 driver ignores the pragma while autocommit is off
        autocommit = dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        dbapi_connection.autocommit = autocommit


event.listen(Engine, "connect", _enable_sqlite_foreign_keys)


# Search backend (pluggable full-text search; see flaskbb/core/search/)
flaskbb_search = FlaskBBSearch(pluggy)

# Login
login_manager = LoginManager()

# Mail
mail = Mail()

# Caching
cache = Cache()

# Redis
redis_store = FlaskRedis()

# Debugtoolbar
debugtoolbar = DebugToolbarExtension()

# Migrations
alembic = Alembic(command_name="", run_mkdir=False)

# Themes
themes = Themes()

# Babel
babel = Babel()

# CSRF
csrf = CSRFProtect()

# Rate Limiting
limiter = Limiter(get_remote_address)

# Celery
celery = Celery("flaskbb")
