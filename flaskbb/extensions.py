# -*- coding: utf-8 -*-
"""
    flaskbb.extensions
    ~~~~~~~~~~~~~~~~~~~~

    The extensions that are used by FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.cache import Cache
from flask.ext.debugtoolbar import DebugToolbarExtension
from flask.ext.redis import Redis
from flask.ext.migrate import Migrate
from flask.ext.themes2 import Themes

# Database
db = SQLAlchemy()

# Login
login_manager = LoginManager()

# Mail
mail = Mail()

# Caching
cache = Cache()

# Redis
redis = Redis()

# Debugtoolbar
debugtoolbar = DebugToolbarExtension()

# Migrations
migrate = Migrate()

# Themes
themes = Themes()
