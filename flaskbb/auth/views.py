# -*- coding: utf-8 -*-
"""
    flaskbb.auth.views
    ~~~~~~~~~~~~~~~~~~~~

    This view provides user authentication, registration and a view for
    resetting the password of a user if he has lost his password

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, url_for, request
from flask_login import (current_user, login_user, login_required,
                         logout_user, confirm_login, login_fresh)
from flask_babelplus import gettext as _

from flaskbb.utils.helpers import render_template, redirect_or_next
from flaskbb.email import send_reset_token, send_activation_token
from flaskbb.exceptions import AuthenticationError, LoginAttemptsExceeded
from flaskbb.auth.forms import (LoginForm, ReauthForm, ForgotPasswordForm,
                                ResetPasswordForm, RegisterForm,
                                AccountActivationForm, RequestActivationForm)
from flaskbb.user.models import User
from flaskbb.fixtures.settings import available_languages
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.tokens import get_token_status, make_token

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Logs the user in."""
    if current_user is not None and current_user.is_authenticated:
        return redirect(current_user.url)

    form = LoginForm(request.form)
    if form.validate_on_submit():
        try:
            user = User.authenticate(form.login.data, form.password.data)
            login_user(user, remember=form.remember_me.data)
            return redirect_or_next(url_for("forum.index"))
        except AuthenticationError:
            flash(_("Wrong Username or Password."), "danger")
        except LoginAttemptsExceeded:
            #timeout = (user.last_failed_login +
            #           timedelta(minutes=flaskbb_config["LOGIN_TIMEOUT"]))
            #timeout_left = datetime.utcnow() - timeout

            flash(_("Your account has been locked for %(minutes)s minutes "
                    "for too many failed login attempts.",
                    minutes=flaskbb_config["LOGIN_TIMEOUT"]), "warning")

    return render_template("auth/login.html", form=form)


@auth.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    """Reauthenticates a user."""
    if not login_fresh():
        form = ReauthForm(request.form)
        if form.validate_on_submit():
            if current_user.check_password(form.password.data):
                confirm_login()
                flash(_("Reauthenticated."), "success")
                return redirect_or_next(current_user.url)

            flash(_("Wrong password."), "danger")
        return render_template("auth/reauth.html", form=form)
    return redirect(request.args.get("next") or current_user.url)


@auth.route("/logout")
@login_required
def logout():
    """Logs the user out."""
    logout_user()
    flash(("Logged out"), "success")
    return redirect(url_for("forum.index"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""
    if current_user is not None and current_user.is_authenticated:
        return redirect_or_next(current_user.url)

    if not flaskbb_config["REGISTRATION_ENABLED"]:
        flash(_("The registration has been disabled."), "info")
        return redirect(url_for("forum.index"))

    form = RegisterForm(request.form)

    form.language.choices = available_languages()
    form.language.default = flaskbb_config['DEFAULT_LANGUAGE']
    form.process(request.form)  # needed because a default is overriden

    if form.validate_on_submit():
        user = form.save()

        if flaskbb_config["ACTIVATE_ACCOUNT"]:
            send_activation_token(user)
            flash(_("An account activation email has been sent to %(email)s",
                    email=user.email), "success")
        else:
            login_user(user)
            flash(_("Thanks for registering."), "success")

        return redirect_or_next(current_user.url)

    return render_template("auth/register.html", form=form)


@auth.route('/reset-password', methods=["GET", "POST"])
def forgot_password():
    """Sends a reset password token to the user."""
    if not current_user.is_anonymous:
        return redirect(url_for("forum.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            token = make_token(user, "reset_password")
            send_reset_token(user, token=token)

            flash(_("E-Mail sent! Please check your inbox."), "info")
            return redirect(url_for("auth.forgot_password"))
        else:
            flash(_("You have entered a Username or E-Mail Address that is "
                    "not linked with your account."), "danger")
    return render_template("auth/forgot_password.html", form=form)


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handles the reset password process."""
    if not current_user.is_anonymous:
        return redirect(url_for("forum.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        expired, invalid, user = get_token_status(form.token.data,
                                                  "reset_password")

        if invalid:
            flash(_("Your Password Token is invalid."), "danger")
            return redirect(url_for("auth.forgot_password"))

        if expired:
            flash(_("Your Password Token is expired."), "danger")
            return redirect(url_for("auth.forgot_password"))

        if user:
            user.password = form.password.data
            user.save()
            flash(_("Your Password has been updated."), "success")
            return redirect(url_for("auth.login"))

    form.token.data = token
    return render_template("auth/reset_password.html", form=form)


@auth.route("/activate", methods=["GET", "POST"])
def request_activation_token(token=None):
    """Requests a new account activation token."""
    if current_user.is_active or not flaskbb_config["ACTIVATE_ACCOUNT"]:
        flash(_("This account is already activated."), "info")
        return redirect(url_for('forum.index'))

    form = RequestActivationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_activation_token(user)
        flash(_("A new account activation token has been sent to "
                "your email address."), "success")
        return redirect(url_for("auth.activate_account"))

    return render_template("auth/request_account_activation.html", form=form)


@auth.route("/activate/<token>", methods=["GET", "POST"])
def activate_account(token=None):
    """Handles the account activation process."""
    if current_user.is_active or not flaskbb_config["ACTIVATE_ACCOUNT"]:
        flash(_("This account is already activated."), "info")
        return redirect(url_for('forum.index'))

    form = None
    if token is not None:
        expired, invalid, user = get_token_status(token, "activate_account")
    else:
        form = AccountActivationForm()
        if form.validate_on_submit():
            expired, invalid, user = get_token_status(form.token.data,
                                                      "activate_account")

    if invalid:
        flash(_("Your account activation token is invalid."), "danger")
        return redirect(url_for("auth.request_email_confirmation"))

    if expired:
        flash(_("Your account activation token is expired."), "danger")
        return redirect(url_for("auth.request_activation_token"))

    if user:
        user.activated = datetime.utcnow()
        user.save()

        if current_user != user:
            logout_user()
            login_user(user)

        flash(_("Your Account has been activated.", "success"))
        return redirect(url_for("forum.index"))

    return render_template("auth/account_activation.html", form=form)
