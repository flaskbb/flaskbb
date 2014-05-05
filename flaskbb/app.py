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

from flask import Flask, request
from flask.ext.login import current_user

# Import the user blueprint
from flaskbb.user.views import user
from flaskbb.user.models import User, Guest, PrivateMessage
# Import the auth blueprint
from flaskbb.auth.views import auth
# Import the admin blueprint
from flaskbb.admin.views import admin
# Import the forum blueprint
from flaskbb.forum.views import forum
from flaskbb.forum.models import Post, Topic, Category, Forum
# extenesions
from flaskbb.extensions import db, login_manager, mail, cache, redis, \
    debugtoolbar, migrate, themes
from flask.ext.whooshalchemy import whoosh_index
# various helpers
from flaskbb.utils.helpers import format_date, time_since, crop_title, \
    is_online, render_markup, mark_online, forum_is_unread, topic_is_unread, \
    render_template
# permission checks (here they are used for the jinja filters)
from flaskbb.utils.permissions import can_post_reply, can_post_topic, \
    can_delete_topic, can_delete_post, can_edit_post, can_lock_topic, \
    can_move_topic
from flaskbb.plugins.manager import PluginManager
from flaskbb.plugins import hooks


def create_app(config=None):
    """
    Creates the app.
    """
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
    configure_before_handlers(app)
    configure_errorhandlers(app)
    configure_logging(app)

    app.logger.debug("Loading plugins...")

    plugin_manager = PluginManager(app)

    # Just a temporary solution to enable the plugins.
    plugin_manager.enable_plugins()

    app.logger.debug(
        "({}) {} Plugins loaded."
        .format(len(plugin_manager.plugins),
                plugin_manager.plugins)
    )

    app.jinja_env.globals.update(hooks=hooks)

    return app


def configure_blueprints(app):
    app.register_blueprint(forum, url_prefix=app.config["FORUM_URL_PREFIX"])
    app.register_blueprint(user, url_prefix=app.config["USER_URL_PREFIX"])
    app.register_blueprint(auth, url_prefix=app.config["AUTH_URL_PREFIX"])
    app.register_blueprint(admin, url_prefix=app.config["ADMIN_URL_PREFIX"])


def configure_extensions(app):
    """
    Configures the extensions
    """

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
    redis.init_app(app)

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
    def load_user(id):
        """
        Loads the user. Required by the `login` extension
        """
        unread_count = db.session.query(db.func.count(PrivateMessage.id)).\
            filter(PrivateMessage.unread == True,
                   PrivateMessage.user_id == id).subquery()
        u = db.session.query(User, unread_count).filter(User.id == id).first()

        if u:
            user, user.pm_unread = u
            return user
        else:
            return None

    login_manager.init_app(app)


def configure_template_filters(app):
    """
    Configures the template filters
    """
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
    app.jinja_env.filters['move_topic'] = can_move_topic
    app.jinja_env.filters['lock_topic'] = can_lock_topic
    app.jinja_env.filters['post_reply'] = can_post_reply
    app.jinja_env.filters['post_topic'] = can_post_topic


def configure_before_handlers(app):
    """
    Configures the before request handlers
    """

    @app.before_request
    def update_lastseen():
        """
        Updates `lastseen` before every reguest if the user is authenticated
        """
        if current_user.is_authenticated():
            current_user.lastseen = datetime.datetime.utcnow()
            db.session.add(current_user)
            db.session.commit()

    @app.before_request
    def get_user_permissions():
        current_user.permissions = current_user.get_permissions()

    if app.config["REDIS_ENABLED"]:
        @app.before_request
        def mark_current_user_online():
            if current_user.is_authenticated():
                mark_online(current_user.username)
            else:
                mark_online(request.remote_addr, guest=True)


def configure_errorhandlers(app):
    """
    Configures the error handlers
    """

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
    """
    Configures logging.
    """

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
            SMTPHandler(app.config['MAIL_SERVER'],
                        app.config['MAIL_DEFAULT_SENDER'],
                        app.config['ADMINS'],
                        'application error, no admins specified',
                        (
                            app.config['MAIL_USERNAME'],
                            app.config['MAIL_PASSWORD'],
                        ))

        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(formatter)
        app.logger.addHandler(mail_handler)
