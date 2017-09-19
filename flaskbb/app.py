# -*- coding: utf-8 -*-
"""
    flaskbb.app
    ~~~~~~~~~~~

    manages the app creation and configuration process

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import logging
import time
from functools import partial

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from flask import Flask, request
from flask_login import current_user

from flaskbb._compat import string_types
# views
from flaskbb.user.views import user
from flaskbb.message.views import message
from flaskbb.auth.views import auth
from flaskbb.management.views import management
from flaskbb.forum.views import forum
# models
from flaskbb.user.models import User, Guest
# extensions
from flaskbb.extensions import (alembic, allows, babel, cache, celery, csrf,
                                db, debugtoolbar, limiter, login_manager, mail,
                                redis_store, themes, whooshee)

# various helpers
from flaskbb.utils.helpers import (time_utcnow, format_date, time_since,
                                   crop_title, is_online, mark_online,
                                   forum_is_unread, topic_is_unread,
                                   render_template, render_markup,
                                   app_config_from_env)
from flaskbb.utils.translations import FlaskBBDomain
# permission checks (here they are used for the jinja filters)
from flaskbb.utils.requirements import (IsAdmin, IsAtleastModerator,
                                        CanBanUser, CanEditUser,
                                        TplCanModerate, TplCanDeletePost,
                                        TplCanDeleteTopic, TplCanEditPost,
                                        TplCanPostTopic, TplCanPostReply)
# whooshees
from flaskbb.utils.search import (PostWhoosheer, TopicWhoosheer,
                                  ForumWhoosheer, UserWhoosheer)
# app specific configurations
from flaskbb.utils.settings import flaskbb_config

from flaskbb.plugins.models import PluginRegistry
from flaskbb.plugins.manager import FlaskBBPluginManager
from flaskbb.plugins import spec


def create_app(config=None):
    """Creates the app.

    :param config: The configuration file or object.
                   The environment variable is weightet as the heaviest.
                   For example, if the config is specified via an file
                   and a ENVVAR, it will load the config via the file and
                   later overwrite it from the ENVVAR.
    """
    app = Flask("flaskbb")
    configure_app(app, config)
    configure_celery_app(app, celery)
    configure_extensions(app)
    load_plugins(app)
    configure_blueprints(app)
    configure_template_filters(app)
    configure_context_processors(app)
    configure_before_handlers(app)
    configure_errorhandlers(app)
    configure_logging(app)
    app.pluggy.hook.flaskbb_additional_setup(app=app, pluggy=app.pluggy)

    return app


def configure_app(app, config):
    """Configures FlaskBB."""
    # Use the default config and override it afterwards
    app.config.from_object('flaskbb.configs.default.DefaultConfig')

    if isinstance(config, string_types) and \
            os.path.exists(os.path.abspath(config)):
        config = os.path.abspath(config)
        app.config.from_pyfile(config)
    else:
        # try to update the config from the object
        app.config.from_object(config)
    # Add the location of the config to the config
    app.config["CONFIG_PATH"] = config

    # try to update the config via the environment variable
    app.config.from_envvar("FLASKBB_SETTINGS", silent=True)

    # Parse the env for FLASKBB_ prefixed env variables and set
    # them on the config object
    app_config_from_env(app, prefix="FLASKBB_")
    app.pluggy = FlaskBBPluginManager('flaskbb', implprefix='flaskbb_')


def configure_celery_app(app, celery):
    """Configures the celery app."""
    app.config.update({'BROKER_URL': app.config["CELERY_BROKER_URL"]})
    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask


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

    app.pluggy.hook.flaskbb_load_blueprints(app=app)


def configure_extensions(app):
    """Configures the extensions."""

    # Flask-WTF CSRF
    csrf.init_app(app)

    # Flask-SQLAlchemy
    db.init_app(app)

    # Flask-Alembic
    alembic.init_app(app, command_name="db")

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

    # Flask-Limiter
    limiter.init_app(app)

    # Flask-Whooshee
    whooshee.init_app(app)
    # not needed for unittests - and it will speed up testing A LOT
    if not app.testing:
        whooshee.register_whoosheer(PostWhoosheer)
        whooshee.register_whoosheer(TopicWhoosheer)
        whooshee.register_whoosheer(ForumWhoosheer)
        whooshee.register_whoosheer(UserWhoosheer)

    # Flask-Login
    login_manager.login_view = app.config["LOGIN_VIEW"]
    login_manager.refresh_view = app.config["REAUTH_VIEW"]
    login_manager.login_message_category = app.config["LOGIN_MESSAGE_CATEGORY"]
    login_manager.needs_refresh_message_category = \
        app.config["REFRESH_MESSAGE_CATEGORY"]
    login_manager.anonymous_user = Guest

    @login_manager.user_loader
    def load_user(user_id):
        """Loads the user. Required by the `login` extension."""

        user_instance = User.query.filter_by(id=user_id).first()
        if user_instance:
            return user_instance
        else:
            return None

    login_manager.init_app(app)

    # Flask-BabelEx
    babel.init_app(app=app, default_domain=FlaskBBDomain(app))

    @babel.localeselector
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        if current_user and \
                current_user.is_authenticated and current_user.language:
            return current_user.language
        # otherwise we will just fallback to the default language
        return flaskbb_config["DEFAULT_LANGUAGE"]

    # Flask-Allows
    allows.init_app(app)
    allows.identity_loader(lambda: current_user)


def configure_template_filters(app):
    """Configures the template filters."""
    filters = {}

    filters['markup'] = render_markup
    filters['format_date'] = format_date
    filters['time_since'] = time_since
    filters['is_online'] = is_online
    filters['crop_title'] = crop_title
    filters['forum_is_unread'] = forum_is_unread
    filters['topic_is_unread'] = topic_is_unread

    permissions = [
        ('is_admin', IsAdmin),
        ('is_moderator', IsAtleastModerator),
        ('is_admin_or_moderator', IsAtleastModerator),
        ('can_edit_user', CanEditUser),
        ('can_ban_user', CanBanUser),
    ]

    filters.update([
        (name, partial(perm, request=request)) for name, perm in permissions
    ])

    # these create closures
    filters['can_moderate'] = TplCanModerate(request)
    filters['post_reply'] = TplCanPostReply(request)
    filters['edit_post'] = TplCanEditPost(request)
    filters['delete_post'] = TplCanDeletePost(request)
    filters['post_topic'] = TplCanPostTopic(request)
    filters['delete_topic'] = TplCanDeleteTopic(request)

    app.jinja_env.filters.update(filters)

    app.pluggy.hook.flaskbb_jinja_directives(app=app)


def configure_context_processors(app):
    """Configures the context processors."""

    @app.context_processor
    def inject_flaskbb_config():
        """Injects the ``flaskbb_config`` config variable into the
        templates.
        """

        return dict(flaskbb_config=flaskbb_config, format_date=format_date)


def configure_before_handlers(app):
    """Configures the before request handlers."""

    @app.before_request
    def update_lastseen():
        """Updates `lastseen` before every reguest if the user is
        authenticated."""

        if current_user.is_authenticated:
            current_user.lastseen = time_utcnow()
            db.session.add(current_user)
            db.session.commit()

    if app.config["REDIS_ENABLED"]:
        @app.before_request
        def mark_current_user_online():
            if current_user.is_authenticated:
                mark_online(current_user.username)
            else:
                mark_online(request.remote_addr, guest=True)

    app.pluggy.hook.flaskbb_request_processors(app=app)


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

    app.pluggy.hook.flaskbb_errorhandlers(app=app)


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
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement,
                                 parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            app.logger.debug("Total Time: %f", total)


def load_plugins(app):
    app.pluggy.add_hookspecs(spec)
    try:
        with app.app_context():
            plugins = PluginRegistry.query.all()

    except (OperationalError, ProgrammingError):
        return

    for plugin in plugins:
        if not plugin.enabled:
            app.pluggy.set_blocked(plugin.name)

    app.pluggy.load_setuptools_entrypoints('flaskbb_plugins')
    app.pluggy.hook.flaskbb_extensions(app=app)

    loaded_names = set([p[0] for p in app.pluggy.list_name_plugin()])
    registered_names = set([p.name for p in plugins])
    unregistered = [
        PluginRegistry(name=name) for name in loaded_names - registered_names
    ]

    with app.app_context():
        db.session.add_all(unregistered)
        db.session.commit()

    app.logger.debug(
        "Plugins Found: {}".format(app.pluggy.list_name_plugin())
    )
    app.logger.debug(
        "Disabled Plugins: {}".format(app.pluggy.list_disabled_plugins())
    )
