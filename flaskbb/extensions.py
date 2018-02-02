# -*- coding: utf-8 -*-
"""
    flaskbb.extensions
    ~~~~~~~~~~~~~~~~~~

    The extensions that are used by FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from inspect import isclass

from celery import Celery
from flask_alembic import Alembic
from flask_allows import Allows
from flask_babelplus import Babel
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_redis import FlaskRedis
from flask_sqlalchemy import BaseQuery, SQLAlchemy
from flask_themes2 import Themes
from flask_whooshee import (DELETE_KWD, INSERT_KWD, UPDATE_KWD, Whooshee,
                            WhoosheeQuery)
from flask_wtf.csrf import CSRFProtect
from flaskbb.exceptions import AuthorizationRequired
from sqlalchemy import MetaData, event
from sqlalchemy.orm import Query as SQLAQuery


class FlaskBBWhooshee(Whooshee):

    def register_whoosheer(self, wh):
        """This will register the given whoosher on `whoosheers`, create the
        neccessary SQLAlchemy event listeners, replace the `query_class` with
        our own query class which will provide the search functionality
        and store the app on the whoosheer, so that we can always work
        with that.
        :param wh: The whoosher which should be registered.
        """
        self.whoosheers.append(wh)
        for model in wh.models:
            event.listen(model, 'after_{0}'.format(INSERT_KWD), self.after_insert)
            event.listen(model, 'after_{0}'.format(UPDATE_KWD), self.after_update)
            event.listen(model, 'after_{0}'.format(DELETE_KWD), self.after_delete)
            query_class = getattr(model, 'query_class', None)

            if query_class is not None and isclass(query_class):
                # already a subclass, ignore it
                if issubclass(query_class, self.query):
                    pass

                # ensure there can be a stable MRO
                elif query_class not in (BaseQuery, SQLAQuery, WhoosheeQuery):
                    query_class_name = query_class.__name__
                    model.query_class = type(
                        "Whooshee{}".format(query_class_name), (query_class, self.query), {}
                    )
                else:
                    model.query_class = self.query
            else:
                model.query_class = self.query

        if self.app:
            wh.app = self.app
        return wh


# Permissions Manager
allows = Allows(throws=AuthorizationRequired)

# Database
metadata = MetaData(
    naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)
db = SQLAlchemy(metadata=metadata)

# Whooshee (Full Text Search)
whooshee = FlaskBBWhooshee()

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
alembic = Alembic()

# Themes
themes = Themes()

# Babel
babel = Babel()

# CSRF
csrf = CSRFProtect()

# Rate Limiting
limiter = Limiter(auto_check=False, key_func=get_remote_address)

# Celery
celery = Celery("flaskbb")
