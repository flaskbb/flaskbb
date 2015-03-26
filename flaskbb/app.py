# -*- coding: utf-8 -*-
"""
    flaskbb.app
    ~~~~~~~~~~~~~~~~~~~~

    manages the app creation and configuration process

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import logging
import datetime
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine

from flask import Flask, request
from flask_login import current_user
from flask_whooshalchemy import whoosh_index

# Import the user blueprint
from flaskbb.user.views import user
from flaskbb.user.models import User, Guest
# Import the (private) message blueprint
from flaskbb.message.views import message
from flaskbb.message.models import Conversation
# Import the auth blueprint
from flaskbb.auth.views import auth
# Import the admin blueprint
from flaskbb.management.views import management
# Import the forum blueprint
from flaskbb.forum.views import forum
from flaskbb.forum.models import Post, Topic, Category, Forum
# extensions
from flaskbb.extensions import db, login_manager, mail, cache, redis_store, \
    debugtoolbar, migrate, themes, plugin_manager, babel, csrf
# various helpers
from flaskbb.utils.helpers import format_date, time_since, crop_title, \
    is_online, render_markup, mark_online, forum_is_unread, topic_is_unread, \
    render_template
from flaskbb.utils.translations import FlaskBBDomain
# permission checks (here they are used for the jinja filters)
from flaskbb.utils.permissions import can_post_reply, can_post_topic, \
    can_delete_topic, can_delete_post, can_edit_post, can_edit_user, \
    can_ban_user, can_moderate, is_admin, is_moderator, is_admin_or_moderator
# app specific configurations
from flaskbb.utils.settings import flaskbb_config


def create_app(config=None):
    """Creates the app."""

    # Initialize the app
    app = Flask("flaskbb")

    # Use the default config and override it afterwards
    app.config.from_object('flaskbb.configs.default.DefaultConfig')
    # Update the config
    app.config.from_object(config)
    # try to update the config via the environment variable
    app.config.from_envvar("FLASKBB_SETTINGS", silent=True)

    configure_blueprints(app)
    configure_extensions(app)
    configure_template_filters(app)
    configure_context_processors(app)
    configure_before_handlers(app)
    configure_errorhandlers(app)
    configure_logging(app)

    return app


def configure_blueprints(app):
    app.register_blueprint(forum, url_prefix=app.config["FORUM_URL_PREFIX"])
    app.register_blueprint(user, url_prefix=app.config["USER_URL_PREFIX"])
    app.register_blueprint(auth, url_prefix=app.config["AUTH_URL_PREFIX"])
    app.register_blueprint(
        management, url_prefix=app.config["ADMIN_URL_PREFIX"]
    )
    app.register_blueprint(
        message, url_prefix=app.config["MESSAGE_URL_PREFIX"]
    )


def configure_extensions(app):
    """Configures the extensions."""

    # Flask-WTF CSRF
    csrf.init_app(app)

    # Flask-Plugins
    plugin_manager.init_app(app)

    # Flask-SQLAlchemy
    db.init_app(app)

    # Flask-Migrate
    migrate.init_app(app, db)

    # Flask-Mail
    mail.init_app(app)

    # Flask-Cache
    cache.init_app(app)

    # Flask-Debugtoolbar
    debugtoolbar.init_app(app)

    # Flask-Themes
    themes.init_themes(app, app_identifier="flaskbb")

    # Flask-And-Redis
    redis_store.init_app(app)

    # Flask-WhooshAlchemy
    with app.app_context():
        whoosh_index(app, Post)
        whoosh_index(app, Topic)
        whoosh_index(app, Forum)
        whoosh_index(app, Category)
        whoosh_index(app, User)

    # Flask-Login
    login_manager.login_view = app.config["LOGIN_VIEW"]
    login_manager.refresh_view = app.config["REAUTH_VIEW"]
    login_manager.anonymous_user = Guest

    @login_manager.user_loader
    def load_user(user_id):
        """Loads the user. Required by the `login` extension."""

        unread_count = db.session.query(db.func.count(Conversation.id)).\
            filter(Conversation.unread,
                   Conversation.user_id == user_id).subquery()
        u = db.session.query(User, unread_count).filter(User.id == user_id).\
            first()

        if u:
            user_instance, user_instance.pm_unread = u
            return user_instance
        else:
            return None

    login_manager.init_app(app)

    # Flask-BabelEx
    babel.init_app(app=app, default_domain=FlaskBBDomain(app))

    @babel.localeselector
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        if current_user.is_authenticated() and current_user.language:
            return current_user.language
        # otherwise we will just fallback to the default language
        return flaskbb_config["DEFAULT_LANGUAGE"]


def configure_template_filters(app):
    """Configures the template filters."""

    app.jinja_env.filters['markup'] = render_markup
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['time_since'] = time_since
    app.jinja_env.filters['is_online'] = is_online
    app.jinja_env.filters['crop_title'] = crop_title
    app.jinja_env.filters['forum_is_unread'] = forum_is_unread
    app.jinja_env.filters['topic_is_unread'] = topic_is_unread
    # Permission filters
    app.jinja_env.filters['edit_post'] = can_edit_post
    app.jinja_env.filters['delete_post'] = can_delete_post
    app.jinja_env.filters['delete_topic'] = can_delete_topic
    app.jinja_env.filters['post_reply'] = can_post_reply
    app.jinja_env.filters['post_topic'] = can_post_topic
    # Moderator permission filters
    app.jinja_env.filters['is_admin'] = is_admin
    app.jinja_env.filters['is_moderator'] = is_moderator
    app.jinja_env.filters['is_admin_or_moderator'] = is_admin_or_moderator
    app.jinja_env.filters['can_moderate'] = can_moderate

    app.jinja_env.filters['can_edit_user'] = can_edit_user
    app.jinja_env.filters['can_ban_user'] = can_ban_user


def configure_context_processors(app):
    """Configures the context processors."""

    @app.context_processor
    def inject_flaskbb_config():
        """Injects the ``flaskbb_config`` config variable into the
        templates.
        """

        return dict(flaskbb_config=flaskbb_config)


def configure_before_handlers(app):
    """Configures the before request handlers."""

    @app.before_request
    def update_lastseen():
        """Updates `lastseen` before every reguest if the user is
        authenticated."""

        if current_user.is_authenticated():
            current_user.lastseen = datetime.datetime.utcnow()
            db.session.add(current_user)
            db.session.commit()

    if app.config["REDIS_ENABLED"]:
        @app.before_request
        def mark_current_user_online():
            if current_user.is_authenticated():
                mark_online(current_user.username)
            else:
                mark_online(request.remote_addr, guest=True)


def configure_errorhandlers(app):
    """Configures the error handlers."""

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/forbidden_page.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/page_not_found.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/server_error.html"), 500


def configure_logging(app):
    """Configures logging."""

    logs_folder = os.path.join(app.root_path, os.pardir, "logs")
    from logging.handlers import SMTPHandler
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')

    info_log = os.path.join(logs_folder, app.config['INFO_LOG'])

    info_file_handler = logging.handlers.RotatingFileHandler(
        info_log,
        maxBytes=100000,
        backupCount=10
    )

    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(formatter)
    app.logger.addHandler(info_file_handler)

    error_log = os.path.join(logs_folder, app.config['ERROR_LOG'])

    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log,
        maxBytes=100000,
        backupCount=10
    )

    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    app.logger.addHandler(error_file_handler)

    if app.config["SEND_LOGS"]:
        mail_handler = \
            SMTPHandler(
                app.config['MAIL_SERVER'],
                app.config['MAIL_DEFAULT_SENDER'],
                app.config['ADMINS'],
                'application error, no admins specified',
                (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            )

        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(formatter)
        app.logger.addHandler(mail_handler)

    if app.config["SQLALCHEMY_ECHO"]:
        # Ref: http://stackoverflow.com/a/8428546
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement,
                                  parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement,
                                 parameters, context, executemany):
            total = time.time() - context._query_start_time

            # Modification for StackOverflow: times in milliseconds
            app.logger.debug("Total Time: %.02fms" % (total * 1000))
