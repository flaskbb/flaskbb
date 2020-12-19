# -*- coding: utf-8 -*-
"""
    flaskbb.auth.views
    ~~~~~~~~~~~~~~~~~~

    This view provides user authentication, registration and a view for
    resetting the password of a user if he has lost his password

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from datetime import datetime

from flask import Blueprint, current_app, flash, g, redirect, request, url_for
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_login import (
    confirm_login,
    current_user,
    login_fresh,
    login_required,
    login_user,
    logout_user,
)

from flaskbb.auth.forms import (
    AccountActivationForm,
    ForgotPasswordForm,
    LoginForm,
    LoginRecaptchaForm,
    ReauthForm,
    RegisterForm,
    RequestActivationForm,
    ResetPasswordForm,
)
from flaskbb.extensions import db, limiter
from flaskbb.utils.helpers import (
    anonymous_required,
    enforce_recaptcha,
    format_timedelta,
    get_available_languages,
    redirect_or_next,
    register_view,
    registration_enabled,
    render_template,
    requires_unactivated,
)
from flaskbb.utils.settings import flaskbb_config

from ..core.auth.authentication import StopAuthentication
from ..core.auth.registration import UserRegistrationInfo
from ..core.exceptions import PersistenceError, StopValidation, ValidationError
from ..core.tokens import TokenError
from .plugins import impl
from .services import (
    account_activator_factory,
    authentication_manager_factory,
    reauthentication_manager_factory,
    registration_service_factory,
    reset_service_factory,
)

logger = logging.getLogger(__name__)


class Logout(MethodView):
    decorators = [limiter.exempt, login_required]

    def get(self):
        logout_user()
        flash(_("Logged out"), "success")
        return redirect(url_for("forum.index"))


class Login(MethodView):
    decorators = [anonymous_required]

    def __init__(self, authentication_manager_factory):
        self.authentication_manager_factory = authentication_manager_factory

    def form(self):
        if enforce_recaptcha(limiter):
            return LoginRecaptchaForm()
        return LoginForm()

    def get(self):
        return render_template("auth/login.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            auth_manager = self.authentication_manager_factory()
            try:
                user = auth_manager.authenticate(
                    identifier=form.login.data, secret=form.password.data
                )
                login_user(user, remember=form.remember_me.data)
                return redirect_or_next(url_for("forum.index"), False)
            except StopAuthentication as e:
                flash(e.reason, "danger")
            except Exception:
                flash(_("Unrecoverable error while handling login"))

        return render_template("auth/login.html", form=form)


class Reauth(MethodView):
    decorators = [login_required, limiter.exempt]
    form = ReauthForm

    def __init__(self, reauthentication_factory):
        self.reauthentication_factory = reauthentication_factory

    def get(self):
        if not login_fresh():
            return render_template("auth/reauth.html", form=self.form())
        return redirect_or_next(current_user.url)

    def post(self):
        form = self.form()
        if form.validate_on_submit():

            reauth_manager = self.reauthentication_factory()
            try:
                reauth_manager.reauthenticate(
                    user=current_user, secret=form.password.data
                )
                confirm_login()
                flash(_("Reauthenticated."), "success")
                return redirect_or_next(current_user.url)
            except StopAuthentication as e:
                flash(e.reason, "danger")
            except Exception:
                flash(_("Unrecoverable error while handling reauthentication"))
                raise

        return render_template("auth/reauth.html", form=form)


class Register(MethodView):
    decorators = [anonymous_required, registration_enabled]

    def __init__(self, registration_service_factory):
        self.registration_service_factory = registration_service_factory

    def form(self):
        current_app.pluggy.hook.flaskbb_form_registration(form=RegisterForm)
        form = RegisterForm()

        form.language.choices = get_available_languages()
        form.language.default = flaskbb_config['DEFAULT_LANGUAGE']
        form.process(request.form)  # needed because a default is overriden
        return form

    def get(self):
        return render_template("auth/register.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            registration_info = UserRegistrationInfo(
                username=form.username.data,
                password=form.password.data,
                group=4,
                email=form.email.data,
                language=form.language.data
            )

            service = self.registration_service_factory()
            try:
                service.register(registration_info)
            except StopValidation as e:
                form.populate_errors(e.reasons)
                return render_template("auth/register.html", form=form)
            except PersistenceError:
                    logger.exception("Database error while persisting user")
                    flash(
                        _(
                            "Could not process registration due"
                            "to an unrecoverable error"
                        ), "danger"
                    )

                    return render_template("auth/register.html", form=form)

            current_app.pluggy.hook.flaskbb_event_user_registered(
                username=registration_info.username
            )
            return redirect_or_next(url_for('forum.index'))

        return render_template("auth/register.html", form=form)


class ForgotPassword(MethodView):
    decorators = [anonymous_required]
    form = ForgotPasswordForm

    def __init__(self, password_reset_service_factory):
        self.password_reset_service_factory = password_reset_service_factory

    def get(self):
        return render_template("auth/forgot_password.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():

            try:
                service = self.password_reset_service_factory()
                service.initiate_password_reset(form.email.data)
            except ValidationError:
                flash(
                    _(
                        "You have entered an username or email address that "
                        "is not linked with your account."
                    ), "danger"
                )
            else:
                flash(_("Email sent! Please check your inbox."), "info")
                return redirect(url_for("auth.forgot_password"))

        return render_template("auth/forgot_password.html", form=form)


class ResetPassword(MethodView):
    decorators = [anonymous_required]
    form = ResetPasswordForm

    def __init__(self, password_reset_service_factory):
        self.password_reset_service_factory = password_reset_service_factory

    def get(self, token):
        form = self.form()
        form.token.data = token
        return render_template("auth/reset_password.html", form=form)

    def post(self, token):
        form = self.form()
        if form.validate_on_submit():
            try:
                service = self.password_reset_service_factory()
                service.reset_password(
                    token, form.email.data, form.password.data
                )
            except TokenError as e:
                flash(e.reason, 'danger')
                return redirect(url_for('auth.forgot_password'))
            except StopValidation as e:
                form.populate_errors(e.reasons)
                form.token.data = token
                return render_template("auth/reset_password.html", form=form)
            except Exception:
                logger.exception("Error when resetting password")
                flash(_('Error when resetting password'))
                return redirect(url_for('auth.forgot_password'))
            finally:
                try:
                    db.session.commit()
                except Exception:
                    logger.exception(
                        "Error while finalizing database when resetting password"  # noqa
                    )
                    db.session.rollback()

            flash(_("Your password has been updated."), "success")
            return redirect(url_for("auth.login"))

        form.token.data = token
        return render_template("auth/reset_password.html", form=form)


class RequestActivationToken(MethodView):
    decorators = [requires_unactivated]
    form = RequestActivationForm

    def __init__(self, account_activator_factory):
        self.account_activator_factory = account_activator_factory

    def get(self):
        return render_template(
            "auth/request_account_activation.html", form=self.form()
        )

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            activator = self.account_activator_factory()
            try:
                activator.initiate_account_activation(form.email.data)
            except ValidationError as e:
                form.populate_errors([(e.attribute, e.reason)])
            else:
                flash(
                    _(
                        "A new account activation token has been sent to "
                        "your email address."
                    ), "success"
                )
                return redirect(url_for('forum.index'))

        return render_template(
            "auth/request_account_activation.html", form=form
        )


class AutoActivateAccount(MethodView):
    decorators = [requires_unactivated]

    def __init__(self, account_activator_factory):
        self.account_activator_factory = account_activator_factory

    def get(self, token):
        activator = self.account_activator_factory()

        try:
            activator.activate_account(token)
        except TokenError as e:
            flash(e.reason, 'danger')
        except ValidationError as e:
            flash(e.reason, 'danger')
            return redirect(url_for('forum.index'))

        else:
            try:
                db.session.commit()
            except Exception:  # noqa
                logger.exception("Database error while activating account")
                db.session.rollback()
                flash(
                    _(
                        "Could not activate account due to an unrecoverable error"  # noqa
                    ), "danger"
                )

                return redirect(url_for('auth.request_activation_token'))

            flash(
                _("Your account has been activated and you can now login."),
                "success"
            )
            return redirect(url_for("forum.index"))

        return redirect(url_for('auth.activate_account'))


class ActivateAccount(MethodView):
    decorators = [requires_unactivated]
    form = AccountActivationForm

    def __init__(self, account_activator_factory):
        self.account_activator_factory = account_activator_factory

    def get(self):
        return render_template(
            "auth/account_activation.html",
            form=self.form()
        )

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            token = form.token.data
            activator = self.account_activator_factory()
            try:
                activator.activate_account(token)
            except TokenError as e:
                form.populate_errors([('token', e.reason)])
            except ValidationError as e:
                flash(e.reason, 'danger')
                return redirect(url_for('forum.index'))

            else:
                try:
                    db.session.commit()
                except Exception:  # noqa
                    logger.exception("Database error while activating account")
                    db.session.rollback()
                    flash(
                        _(
                            "Could not activate account due to an unrecoverable error"  # noqa
                        ), "danger"
                    )

                    return redirect(url_for('auth.request_activation_token'))

                flash(
                    _("Your account has been activated and you can now login."),
                    "success"
                )
                return redirect(url_for("forum.index"))

        return render_template("auth/account_activation.html", form=form)


@impl(tryfirst=True)
def flaskbb_load_blueprints(app):
    auth = Blueprint("auth", __name__)

    def login_rate_limit():
        """Dynamically load the rate limiting config from the database."""
        # [count] [per|/] [n (optional)] [second|minute|hour|day|month|year]
        return "{count}/{timeout}minutes".format(
            count=flaskbb_config["AUTH_REQUESTS"],
            timeout=flaskbb_config["AUTH_TIMEOUT"]
        )

    def login_rate_limit_message():
        """Display the amount of time left until the user can access the requested
        resource again."""
        current_limit = getattr(g, 'view_rate_limit', None)
        if current_limit is not None:
            window_stats = limiter.limiter.get_window_stats(*current_limit)
            reset_time = datetime.utcfromtimestamp(window_stats[0])
            timeout = reset_time - datetime.utcnow()
        return "{timeout}".format(timeout=format_timedelta(timeout))

    @auth.before_request
    def check_rate_limiting():
        """Check the the rate limits for each request for this blueprint."""
        if not flaskbb_config["AUTH_RATELIMIT_ENABLED"]:
            return None
        return limiter.check()

    @auth.errorhandler(429)
    def login_rate_limit_error(error):
        """Register a custom error handler for a 'Too Many Requests'
        (HTTP CODE 429) error."""
        return render_template(
            "errors/too_many_logins.html", timeout=error.description
        )

    # Activate rate limiting on the whole blueprint
    limiter.limit(
        login_rate_limit, error_message=login_rate_limit_message
    )(auth)

    register_view(auth, routes=['/logout'], view_func=Logout.as_view('logout'))
    register_view(
        auth,
        routes=['/login'],
        view_func=Login.as_view(
            'login',
            authentication_manager_factory=authentication_manager_factory
        )
    )
    register_view(
        auth,
        routes=['/reauth'],
        view_func=Reauth.as_view(
            'reauth',
            reauthentication_factory=reauthentication_manager_factory
        )
    )
    register_view(
        auth,
        routes=['/register'],
        view_func=Register.as_view(
            'register',
            registration_service_factory=registration_service_factory
        )
    )

    register_view(
        auth,
        routes=['/reset-password'],
        view_func=ForgotPassword.as_view(
            'forgot_password',
            password_reset_service_factory=reset_service_factory
        )
    )

    register_view(
        auth,
        routes=['/reset-password/<token>'],
        view_func=ResetPassword.as_view(
            'reset_password',
            password_reset_service_factory=reset_service_factory
        )
    )

    register_view(
        auth,
        routes=['/activate'],
        view_func=RequestActivationToken.as_view(
            'request_activation_token',
            account_activator_factory=account_activator_factory
        )
    )
    register_view(
        auth,
        routes=['/activate/confirm'],
        view_func=ActivateAccount.as_view(
            'activate_account',
            account_activator_factory=account_activator_factory
        )
    )

    register_view(
        auth,
        routes=['/activate/confirm/<token>'],
        view_func=AutoActivateAccount.as_view(
            'autoactivate_account',
            account_activator_factory=account_activator_factory
        )
    )

    app.register_blueprint(auth, url_prefix=app.config['AUTH_URL_PREFIX'])
