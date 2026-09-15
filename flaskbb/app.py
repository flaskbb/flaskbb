"""
flaskbb.app
~~~~~~~~~~~

manages the app creation and configuration process

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import importlib.metadata
import importlib.util
import logging
import logging.config
import os
import sys
import time
import warnings
from collections.abc import Callable, Sequence
from datetime import datetime, UTC
from email.utils import formataddr
from typing import Any, cast

import sqlalchemy as sa
from celery import Celery
from flask import flash, redirect, request, url_for
from flask_allows2 import Permission
from flask_babelplus import gettext as _
from jinja2.filters import do_filesizeformat
from redis import Redis
from sqlalchemy import event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from werkzeug.exceptions import Forbidden, InternalServerError, NotFound, RequestEntityTooLarge

from flaskbb.core.app import FlaskBB
from flaskbb.extensions import (
    alembic,
    allows,
    babel,
    cache,
    celery,
    csrf,
    db,
    debugtoolbar,
    limiter,
    login_manager,
    mail,
    pluggy,
    themes,
)
from flaskbb.plugins import spec
from flaskbb.plugins.models import PluginRegistry
from flaskbb.plugins.utils import (
    get_plugins_with_pending_migrations,
    remove_zombie_plugins_from_db,
    template_hook,
)
from flaskbb.search import flaskbb_search
from flaskbb.search.service import search_snippet
from flaskbb.settings import (
    fixture as fixture,
)
from flaskbb.settings import (
    flaskbb_config,
    setting_registry,
)

# models
from flaskbb.user.models import Guest, User

# various helpers
from flaskbb.utils.helpers import (
    app_config_from_env,
    crop_title,
    format_date,
    format_datetime,
    format_time,
    forum_is_unread,
    get_alembic_locations,
    get_flaskbb_config,
    is_htmx_request,
    is_online,
    mark_online,
    render_template,
    time_since,
    time_utcnow,
    topic_is_unread,
)
from flaskbb.utils.proxies import current_user

# permission checks (here they are used for the jinja filters)
from flaskbb.utils.requirements import (
    can_ban_user,
    can_delete_topic,
    can_edit_post,
    can_edit_user,
    can_moderate,
    can_post_reply,
    can_post_topic,
    has_permission,
    IsAdmin,
    IsAtleastModerator,
    permission_with_identity,
)
from flaskbb.utils.translations import FlaskBBDomain
from flaskbb.utils.uploads import create_upload_directory

from .auth import views as auth_views  # noqa  # pyright: ignore[reportUnusedImport]
from .deprecation import FlaskBBDeprecation
from .display.navigation import NavigationContentType
from .forum import views as forum_views  # noqa  # pyright: ignore[reportUnusedImport]
from .management import views as management_views  # noqa  # pyright: ignore[reportUnusedImport]
from .management.navigation import get_management_navigation
from .search import views as search_views  # noqa  # pyright: ignore[reportUnusedImport]
from .upload import views as upload_views  # noqa  # pyright: ignore[reportUnusedImport]
from .user import views as user_views  # noqa  # pyright: ignore[reportUnusedImport]

logger = logging.getLogger(__name__)


def create_app(config: object | None = None, instance_path: str | None = None):
    """Creates the app.

    :param instance_path: An alternative instance path for the application.
                          By default the folder ``'instance'`` next to the
                          package or module is assumed to be the instance
                          path.
                          See :ref:`Instance Folders <flask:instance-folders>`.
    :param config: The configuration file or object.
                   The environment variable is weightet as the heaviest.
                   For example, if the config is specified via an file
                   and a ENVVAR, it will load the config via the file and
                   later overwrite it from the ENVVAR.
                   If no config is provided, FlaskBB will try to load the
                   config named ``flaskbb.cfg`` from the instance path.
    """

    app = FlaskBB("flaskbb", instance_path=instance_path, instance_relative_config=True)

    # instance folders are not automatically created by flask
    os.makedirs(app.instance_path, exist_ok=True)

    configure_app(app, config)
    configure_celery_app(app, celery)
    configure_extensions(app)

    load_plugins(app)

    configure_search_backend(app)

    configure_blueprints(app)
    configure_template_filters(app)
    configure_context_processors(app)
    configure_before_handlers(app)
    configure_errorhandlers(app)
    configure_migrations(app)
    configure_translations(app)

    setting_registry.load_from_internal(pluggy)
    setting_registry.load_from_plugins(pluggy)

    pluggy.hook.flaskbb_additional_setup(app=app, pluggy=pluggy)

    return app


def configure_app(app: FlaskBB, config: Any):
    """Configures FlaskBB."""
    # Use the default config and override it afterwards
    app.raw_config.from_object("flaskbb.configs.default.DefaultConfig")
    config = get_flaskbb_config(app, config)
    # Path
    if isinstance(config, str):
        app.raw_config.from_pyfile(config)
    # Module
    else:
        # try to update the config from the object
        app.raw_config.from_object(config)

    # Add the location of the config to the config
    app.config["CONFIG_PATH"] = config

    # Environment
    # Parse the env for FLASKBB_ prefixed env variables and set
    # them on the config object
    app_config_from_env(app, prefix="FLASKBB_")

    # Migrate Celery 4.x config to Celery 6.x
    old_celery_config = app.raw_config.get_namespace("CELERY_")
    celery_config = {}
    for key, value in old_celery_config.items():
        # config is the new format
        if key != "config":
            config_key = f"CELERY_{key.upper()}"
            celery_config[key] = value
            try:
                del app.raw_config[config_key]
            except KeyError:
                pass

    # merge the new config with the old one
    new_celery_config = app.config["CELERY_CONFIG"]
    new_celery_config.update(celery_config)  # pyright: ignore[reportUnknownArgumentType]
    app.config.update({"CELERY_CONFIG": new_celery_config})

    # Setting up logging as early as possible
    configure_logging(app)

    config_name: str | None
    if not isinstance(config, str) and config is not None:
        config_name = f"{config.__module__}.{config.__name__}"
    else:
        config_name = config

    logger.info(f"Using config from: {config_name}")

    deprecation_level = cast("Any", app.config.get("DEPRECATION_LEVEL", "default"))

    # never set the deprecation level during testing, pytest will handle it
    if not app.testing:  # pragma: no branch
        warnings.simplefilter(deprecation_level, FlaskBBDeprecation)

    # Filter Flask-Limiter in-memory warnings when running in debug mode oder test mode
    if app.debug or app.testing:
        warnings.filterwarnings(
            action="ignore",
            message=".*Using the in-memory storage for tracking rate limits.*",
        )

    # Fall back to SERVER_NAME for TRUSTED_HOSTS so Host header validation
    # is covered by the same setting deployments are already required to set.
    if not app.config["TRUSTED_HOSTS"] and app.config["SERVER_NAME"]:
        app.config["TRUSTED_HOSTS"] = [app.config["SERVER_NAME"]]

    if not app.debug and not app.testing and not app.config["TRUSTED_HOSTS"]:
        logger.warning(
            "Neither SERVER_NAME nor TRUSTED_HOSTS is configured. Requests "
            "where URL generation happens outside of the request context "
            "are not protected against Host Header Poisoning. "
            "Set TRUSTED_HOSTS or SERVER_NAME in your flaskbb.cfg. "
            "See https://flask.palletsprojects.com/en/stable/config/#TRUSTED_HOSTS "
            "for more information about these configuration variables."
        )

    app.config.setdefault(
        "DEBUG_TB_PANELS",
        [
            "flask_debugtoolbar.panels.versions.VersionDebugPanel",
            "flask_debugtoolbar.panels.timer.TimerDebugPanel",
            "flask_debugtoolbar.panels.headers.HeaderDebugPanel",
            "flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel",
            "flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel",
            "flask_debugtoolbar.panels.template.TemplateDebugPanel",
            "flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel",
            "flask_debugtoolbar.panels.logger.LoggingPanel",
            "flask_debugtoolbar.panels.route_list.RouteListDebugPanel",
            "flask_debugtoolbar.panels.profiler.ProfilerDebugPanel",
        ],
    )

    if all("WarningsPanel" not in p for p in app.config["DEBUG_TB_PANELS"]):
        app.config["DEBUG_TB_PANELS"].append("flask_debugtoolbar_warnings.WarningsPanel")

    create_upload_directory(app)


def configure_celery_app(app: FlaskBB, celery: Celery):
    """Configures the celery app."""
    celery.conf.update(app.config.get("CELERY_CONFIG"))  # pyright: ignore[reportUnknownMemberType]

    TaskBase = celery.Task  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    class ContextTask(TaskBase):  # type: ignore[valid-type,misc]  # pyright: ignore[reportUntypedBaseClass]
        def __call__(self, *args: Any, **kwargs: Any):  # pyright: ignore[reportUnknownParameterType]
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    celery.Task = ContextTask


def configure_blueprints(app: FlaskBB):
    pluggy.hook.flaskbb_load_blueprints(app=app)


def configure_extensions(app: FlaskBB):
    """Configures the extensions."""
    # Flask-Allows
    allows.init_app(app)
    allows.identity_loader(lambda: current_user)

    # Flask-WTF CSRF
    csrf.init_app(app)  # pyright: ignore[reportUnknownMemberType]

    # Flask-SQLAlchemy
    db.init_app(app)

    # Flask-Alembic
    alembic.init_app(app)

    # Flask-Mail
    mail.init_app(app)

    # Flask-Cache
    cache.init_app(app)

    # Flask-Debugtoolbar
    debugtoolbar.init_app(app)

    # Flask-Themes
    themes.init_themes(app, app_identifier="flaskbb")  # pyright: ignore[reportUnknownMemberType]

    # redis-py
    if app.config["REDIS_ENABLED"]:
        app.extensions["redis"] = Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
            app.config["REDIS_URL"], db=app.config["REDIS_DATABASE"]
        )

    # Flask-Limiter
    limiter.init_app(app)

    # Flask-Login
    # flask_login infers both as None from their initializers
    login_manager.login_view = app.config["LOGIN_VIEW"]  # pyright: ignore[reportAttributeAccessIssue]
    login_manager.refresh_view = app.config["REAUTH_VIEW"]  # pyright: ignore[reportAttributeAccessIssue]
    login_manager.login_message_category = app.config["LOGIN_MESSAGE_CATEGORY"]
    login_manager.needs_refresh_message_category = app.config["REFRESH_MESSAGE_CATEGORY"]
    login_manager.anonymous_user = Guest

    @login_manager.user_loader  # type: ignore[untyped-decorator]  # pyright: ignore[reportUnknownMemberType]
    def load_user(user_id: int):
        """Loads the user. Required by the `login` extension."""
        user = db.session.execute(sa.select(User).filter_by(id=user_id)).scalar_one_or_none()
        pluggy.hook.flaskbb_current_user(app=app, user=user)
        return user

    login_manager.init_app(app)  # pyright: ignore[reportUnknownMemberType]


def configure_search_backend(app: FlaskBB):
    """Resolves and initializes the configured search backend. Runs after
    load_plugins() so backends contributed by plugins via the
    flaskbb_load_search_backends hook are available for selection.
    """
    flaskbb_search.init_app(app)


def configure_template_filters(app: FlaskBB):
    """Configures the template filters."""
    filters: dict[str, Callable[..., Any]] = {}

    filters["crop_title"] = crop_title
    filters["format_date"] = format_date
    filters["format_time"] = format_time
    filters["format_datetime"] = format_datetime
    filters["forum_is_unread"] = forum_is_unread
    filters["is_online"] = is_online
    filters["search_snippet"] = search_snippet
    filters["time_since"] = time_since
    filters["topic_is_unread"] = topic_is_unread

    permissions = [
        ("is_admin", IsAdmin),
        ("is_moderator", IsAtleastModerator),
        ("is_admin_or_moderator", IsAtleastModerator),
    ]

    filters.update((name, permission_with_identity(perm, name=name)) for name, perm in permissions)

    filters["can_ban_user"] = can_ban_user
    filters["can_edit_user"] = can_edit_user
    filters["can_moderate"] = can_moderate
    filters["post_reply"] = can_post_reply
    filters["edit_post"] = can_edit_post
    filters["delete_post"] = can_edit_post
    filters["post_topic"] = can_post_topic
    filters["delete_topic"] = can_delete_topic
    filters["has_permission"] = has_permission

    app.jinja_env.filters.update(filters)

    jinja_globals: dict[str, Callable[..., Any]] = {}
    jinja_globals["run_hook"] = template_hook
    jinja_globals["NavigationContentType"] = NavigationContentType
    jinja_globals["get_management_navigation"] = get_management_navigation
    jinja_globals["is_htmx_request"] = is_htmx_request
    app.jinja_env.globals.update(jinja_globals)

    pluggy.hook.flaskbb_jinja_directives(app=app)


def configure_context_processors(app: FlaskBB):
    """Configures the context processors."""

    @app.context_processor
    def inject_flaskbb_config():
        """Injects the ``flaskbb_config`` config variable into the
        templates.
        """
        return dict(flaskbb_config=flaskbb_config, format_date=format_date)

    @app.context_processor
    def inject_now():
        """Injects the current time."""
        return dict(now=datetime.now(UTC))


def configure_before_handlers(app: FlaskBB):
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
                mark_online(current_user.id)
            elif request.remote_addr:
                mark_online(request.remote_addr, guest=True)

    pluggy.hook.flaskbb_request_processors(app=app)


def configure_errorhandlers(app: FlaskBB):
    """Configures the error handlers."""

    @app.errorhandler(403)
    def forbidden_page(error: Forbidden):
        return render_template("errors/forbidden_page.html"), 403

    @app.errorhandler(404)
    def page_not_found(error: NotFound):
        return render_template("errors/page_not_found.html"), 404

    @app.errorhandler(500)
    def server_error_page(error: InternalServerError):
        return render_template("errors/server_error.html"), 500

    @app.errorhandler(413)
    def request_entity_too_large(error: RequestEntityTooLarge):
        max_content_length = app.config.get("MAX_CONTENT_LENGTH")
        if max_content_length:
            message = _(
                "The upload is too large. A request cannot be bigger than %(size)s.",
                size=do_filesizeformat(max_content_length),
            )
        else:
            message = _("The upload is too large.")

        flash(message, "danger")
        return redirect(request.referrer or url_for("forum.index"))

    @app.errorhandler(OperationalError)
    @app.errorhandler(ProgrammingError)
    def plugin_migrations_pending(error: OperationalError | ProgrammingError):
        db.session.rollback()
        plugins = get_plugins_with_pending_migrations(error)
        if not plugins:
            raise error

        is_admin = Permission(IsAdmin, identity=current_user)
        endpoint = "management.overview" if is_admin else "forum.index"
        # the plugin can also fail on the redirect target, i.e. in a template hook
        if request.endpoint == endpoint:
            raise error

        if is_admin:
            flash(
                _(
                    "The migrations of %(plugins)s have not been applied yet. "
                    "Apply them with 'flaskbb plugins install --migrations-only <plugin>'.",
                    plugins=", ".join(plugins),
                ),
                "danger",
            )
        else:
            flash(_("This page is currently unavailable."), "danger")
        return redirect(url_for(endpoint))

    pluggy.hook.flaskbb_errorhandlers(app=app)


def configure_migrations(app: FlaskBB):
    """Configure migrations.

    Disabled plugins are never imported, so they can't answer
    ``flaskbb_load_migrations``. Their migrations are looked up next to the
    package instead, the convention ``has_migrations`` relies on as well, so
    the revisions they already applied (e.g. during ``flaskbb install``) resolve.
    """
    plugin_dirs = pluggy.hook.flaskbb_load_migrations()
    disabled_dirs: list[str] = []
    for entry_point in pluggy.list_disabled_plugins():
        package = importlib.util.find_spec(entry_point.module.split(".")[0])
        if package is None or not package.submodule_search_locations:
            continue
        migrations = os.path.join(next(iter(package.submodule_search_locations)), "migrations")
        if os.path.isdir(migrations):
            disabled_dirs.append(migrations)

    app.config["ALEMBIC"]["version_locations"] = get_alembic_locations(plugin_dirs + disabled_dirs)
    app.config["ALEMBIC"]["disabled_version_locations"] = disabled_dirs


def configure_translations(app: FlaskBB):
    """Configure translations."""

    # we have to initialize the extension after we have loaded the plugins
    # because we of the 'flaskbb_load_translations' hook
    babel.init_app(app=app, default_domain=FlaskBBDomain(app))

    @babel.localeselector
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        if current_user and current_user.is_authenticated and current_user.language:
            return current_user.language
        # otherwise we will just fallback to the default language
        return flaskbb_config["DEFAULT_LANGUAGE"]


def configure_logging(app: FlaskBB):
    """Configures logging."""
    if app.config.get("USE_DEFAULT_LOGGING"):
        configure_default_logging(app)

    log_conf_file = app.config["LOG_CONF_FILE"]
    if log_conf_file:
        logging.config.fileConfig(log_conf_file, disable_existing_loggers=False)

    if app.config["SQLALCHEMY_ECHO"]:
        # Ref: http://stackoverflow.com/a/8428546
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn: Connection,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn: Connection,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            total = time.time() - conn.info["query_start_time"].pop(-1)
            app.logger.debug("Total Time: %f", total)


def configure_default_logging(app: FlaskBB):
    # Load default logging config
    logging.config.dictConfig(app.config["LOG_DEFAULT_CONF"])

    if app.config["SEND_LOGS"]:
        configure_mail_logs(app)


def configure_mail_logs(app: FlaskBB, formatter: logging.Formatter | None = None):
    from logging.handlers import SMTPHandler

    if formatter is None:
        formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(name)-25s %(message)s")
    # MAIL_DEFAULT_SENDER may be a (name, address) pair, SMTPHandler wants a
    # single From header value
    sender = app.config["MAIL_DEFAULT_SENDER"]
    mail_handler = SMTPHandler(
        app.config["MAIL_SERVER"],
        sender if isinstance(sender, str) else formataddr(sender),
        app.config["ADMINS"],
        "application error, no admins specified",
        (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"]),
    )

    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(formatter)
    app.logger.addHandler(mail_handler)


def load_plugins(app: FlaskBB):
    pluggy.add_hookspecs(spec)

    # have to find all the flaskbb modules that are loaded this way
    # otherwise sys.modules might change while we're iterating it
    # because of imports and that makes Python very unhappy
    # we are not interested in duplicated plugins or invalid ones
    # ('None' - appears on py2) and thus using a set
    flaskbb_modules = set(
        module
        for name, module in sys.modules.items()
        if name == "flaskbb" or name.startswith("flaskbb.")
    )
    for module in flaskbb_modules:
        pluggy.register(module, internal=True)

    try:
        with app.app_context():
            plugins: Sequence[PluginRegistry] = (
                db.session.execute(sa.select(PluginRegistry)).scalars().all()
            )

    except (OperationalError, ProgrammingError) as exc:
        logger.debug(
            "Database is not setup correctly or has not been setup yet.",
            exc_info=exc,
        )
        # load plugins even though the database isn't setup correctly
        # i.e. when creating the initial database and wanting to install
        # the plugins migration as well
        pluggy.load_setuptools_entrypoints("flaskbb_plugins")
        return

    # newly installed plugins stay disabled until they are enabled explicitly
    enabled_names = {p.name for p in plugins if p.enabled}
    for entry_point in importlib.metadata.entry_points(group="flaskbb_plugins"):
        if entry_point.name not in enabled_names:
            pluggy.set_blocked(entry_point.name)

    for plugin in plugins:
        if plugin.is_updatable:
            logger.info(f"Updating installed plugin: {plugin.name}")
            plugin.add_settings()

    pluggy.load_setuptools_entrypoints("flaskbb_plugins")
    pluggy.hook.flaskbb_extensions(app=app)

    registered_names = {p.name for p in plugins}
    unregistered = [
        PluginRegistry(name=name)
        for name in pluggy.get_disabled_plugins()
        if name not in registered_names
    ]
    with app.app_context():
        db.session.add_all(unregistered)
        db.session.commit()

        removed = 0
        if app.config["REMOVE_DEAD_PLUGINS"]:
            removed = remove_zombie_plugins_from_db()
            logger.info(f"Removed Plugins: {removed}")

    # we need a copy of it because of
    # RuntimeError: dictionary changed size during iteration
    tasks = celery.tasks.copy()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    disabled_plugins = [ep.module.split(".")[0] for ep in pluggy.list_disabled_plugins()]
    for task_name, task in tasks.items():  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if task.__module__.split(".")[0] in disabled_plugins:  # pyright: ignore[reportUnknownMemberType]
            logger.debug(f"Unregistering task: '{task}'")
            celery.tasks.unregister(task_name)  # pyright: ignore[reportUnknownMemberType]
