# -*- coding: utf-8 -*-
"""
    flaskbb.extensions
    ~~~~~~~~~~~~~~~~~~~~

    The extensions that are used by FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_redis import Redis
from flask_migrate import Migrate
from flask_themes2 import Themes
from flask_plugins import PluginManager
from flask_babelex import Babel
from flask_wtf.csrf import CsrfProtect
from flask_principal import Principal


# Database
db = SQLAlchemy()

# Login
login_manager = LoginManager()

# Mail
mail = Mail()

# Caching
cache = Cache()

# Redis
redis_store = Redis()

# Debugtoolbar
debugtoolbar = DebugToolbarExtension()

# Migrations
migrate = Migrate()

# Themes
themes = Themes()

# PluginManager
plugin_manager = PluginManager()

# Babel
babel = Babel()

# CSRF
csrf = CsrfProtect()

# Principal
principal = Principal()
