# -*- coding: utf-8 -*-
"""
    flaskbb.auth.views
    ~~~~~~~~~~~~~~~~~~

    This view provides user authentication, registration and a view for
    resetting the password of a user if he has lost his password

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flask import Blueprint, flash, g, redirect, request, url_for
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_login import (confirm_login, current_user, login_fresh,
                         login_required, login_user, logout_user)

from flaskbb.auth.forms import (AccountActivationForm, ForgotPasswordForm,
                                LoginForm, LoginRecaptchaForm, ReauthForm,
                                RegisterForm, RequestActivationForm,
                                ResetPasswordForm)
from flaskbb.email import send_activation_token, send_reset_token
from flaskbb.exceptions import AuthenticationError
from flaskbb.extensions import limiter
from flaskbb.user.models import User
from flaskbb.utils.helpers import (anonymous_required, enforce_recaptcha,
                                   format_timedelta, get_available_languages,
                                   redirect_or_next, registration_enabled,
                                   render_template, requires_unactivated)
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.tokens import get_token_status

auth = Blueprint("auth", __name__)


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
    return render_template("errors/too_many_logins.html", timeout=error.description)


def login_rate_limit():
    """Dynamically load the rate limiting config from the database."""
    # [count] [per|/] [n (optional)] [second|minute|hour|day|month|year]
    return "{count}/{timeout}minutes".format(
        count=flaskbb_config["AUTH_REQUESTS"], timeout=flaskbb_config["AUTH_TIMEOUT"]
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


# Activate rate limiting on the whole blueprint
limiter.limit(login_rate_limit, error_message=login_rate_limit_message)(auth)


@auth.route("/logout")
@limiter.exempt
@login_required
def logout():
    """Logs the user out."""
    logout_user()
    flash(_("Logged out"), "success")
    return redirect(url_for("forum.index"))


class Login(MethodView):
    decorators = [anonymous_required]

    def form(self):
        if enforce_recaptcha(limiter):
            return LoginRecaptchaForm()
        return LoginForm()

    def get(self):
        return render_template("auth/login.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            try:
                user = User.authenticate(form.login.data, form.password.data)
                if not login_user(user, remember=form.remember_me.data):
                    flash(
                        _(
                            "In order to use your account you have to activate it "
                            "through the link we have sent to your email "
                            "address."
                        ), "danger"
                    )
                return redirect_or_next(url_for("forum.index"))
            except AuthenticationError:
                flash(_("Wrong username or password."), "danger")

        return render_template("auth/login.html", form=form)


class Reauth(MethodView):
    decorators = [login_required, limiter.exempt]
    form = ReauthForm

    def get(self):
        if not login_fresh():
            return render_template("auth/reauth.html", form=self.form())
        return redirect_or_next(current_user.url)

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            if current_user.check_password(form.password.data):
                confirm_login()
                flash(_("Reauthenticated."), "success")
                return redirect_or_next(current_user.url)

            flash(_("Wrong password."), "danger")
        return render_template("auth/reauth.html", form=form)


class Register(MethodView):
    decorators = [anonymous_required, registration_enabled]

    def form(self):
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
            user = form.save()

            if flaskbb_config["ACTIVATE_ACCOUNT"]:
                # Any call to an expired model requires a database hit, so
                # accessing user.id would cause an DetachedInstanceError.
                # This happens because the `user`'s session does no longer exist.
                # So we just fire up another query to make sure that the session
                # for the newly created user is fresh.
                # PS: `db.session.merge(user)` did not work for me.
                user = User.query.filter_by(email=user.email).first()
                send_activation_token.delay(user)
                flash(
                    _("An account activation email has been sent to %(email)s", email=user.email),
                    "success"
                )
            else:
                login_user(user)
                flash(_("Thanks for registering."), "success")

            return redirect_or_next(url_for('forum.index'))

        return render_template("auth/register.html", form=form)


class ForgotPassword(MethodView):
    decorators = [anonymous_required]
    form = ForgotPasswordForm

    def get(self):
        return render_template("auth/forgot_password.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()

            if user:
                send_reset_token.delay(user)
                flash(_("Email sent! Please check your inbox."), "info")
                return redirect(url_for("auth.forgot_password"))
            else:
                flash(
                    _(
                        "You have entered an username or email address that is "
                        "not linked with your account."
                    ), "danger"
                )
        return render_template("auth/forgot_password.html", form=form)


class ResetPassword(MethodView):
    decorators = [anonymous_required]
    form = ResetPasswordForm

    def get(self, token):
        form = self.form()
        form.token.data = token
        return render_template("auth/reset_password.html", form=form)

    def post(self, token):
        form = self.form()
        if form.validate_on_submit():
            expired, invalid, user = get_token_status(form.token.data, "reset_password")

            if invalid:
                flash(_("Your password token is invalid."), "danger")
                return redirect(url_for("auth.forgot_password"))

            if expired:
                flash(_("Your password token is expired."), "danger")
                return redirect(url_for("auth.forgot_password"))

            if user:
                user.password = form.password.data
                user.save()
                flash(_("Your password has been updated."), "success")
                return redirect(url_for("auth.login"))

        form.token.data = token
        return render_template("auth/reset_password.html", form=form)


class RequestActivationToken(MethodView):
    decorators = [requires_unactivated]
    form = RequestActivationForm

    def get(self):
        return render_template("auth/request_account_activation.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            send_activation_token.delay(user)
            flash(
                _("A new account activation token has been sent to "
                  "your email address."), "success"
            )
            return redirect(url_for("auth.activate_account"))

        return render_template("auth/request_account_activation.html", form=form)


class ActivateAccount(MethodView):
    form = AccountActivationForm
    decorators = [requires_unactivated]

    def get(self, token=None):
        expired = invalid = user = None
        if token is not None:
            expired, invalid, user = get_token_status(token, "activate_account")

        if invalid:
            flash(_("Your account activation token is invalid."), "danger")
            return redirect(url_for("auth.request_activation_token"))

        if expired:
            flash(_("Your account activation token is expired."), "danger")
            return redirect(url_for("auth.request_activation_token"))

        if user:
            user.activated = True
            user.save()

            if current_user != user:
                logout_user()
                login_user(user)

            flash(_("Your account has been activated."), "success")
            return redirect(url_for("forum.index"))

        return render_template("auth/account_activation.html", form=self.form())

    def post(self, token=None):
        expired = invalid = user = None
        form = self.form()

        if token is not None:
            expired, invalid, user = get_token_status(token, "activate_account")

        elif form.validate_on_submit():
            expired, invalid, user = get_token_status(form.token.data, "activate_account")

        if invalid:
            flash(_("Your account activation token is invalid."), "danger")
            return redirect(url_for("auth.request_activation_token"))

        if expired:
            flash(_("Your account activation token is expired."), "danger")
            return redirect(url_for("auth.request_activation_token"))

        if user:
            user.activated = True
            user.save()

            if current_user != user:
                logout_user()
                login_user(user)

            flash(_("Your account has been activated."), "success")
            return redirect(url_for("forum.index"))

        return render_template("auth/account_activation.html", form=form)


auth.add_url_rule("/login", view_func=Login.as_view('login'))
auth.add_url_rule("/reauth", view_func=Reauth.as_view('reauth'))
auth.add_url_rule("/register", view_func=Register.as_view('register'))
auth.add_url_rule("/reset-password", view_func=ForgotPassword.as_view('forgot_password'))
auth.add_url_rule("/reset-password/<token>", view_func=ResetPassword.as_view('reset_password'))
auth.add_url_rule(
    "/activate", view_func=RequestActivationToken.as_view('request_activation_token')
)

# need to register this one specially because Flask complains otherwise
_activate = ActivateAccount.as_view('activate_account')
auth.add_url_rule("/activate/confirm", view_func=_activate)
auth.add_url_rule("/activate/confirm/<token>", view_func=_activate)
del _activate
