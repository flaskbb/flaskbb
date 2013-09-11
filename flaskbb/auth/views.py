# -*- coding: utf-8 -*-
"""
    flaskbb.auth.views
    ~~~~~~~~~~~~~~~~~~~~

    This view provides user authentication, registration and a view for
    resetting the password of a user if he has lost his password

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug import generate_password_hash
from flask import (Blueprint, flash, redirect, render_template,
                   url_for, request)
from flask.ext.login import (current_user, login_user, login_required,
                             logout_user, confirm_login, login_fresh)
from flaskbb.extensions import db
from flaskbb.utils import generate_random_pass
from flaskbb.email import send_new_password
from flaskbb.auth.forms import (LoginForm, ReauthForm, RegisterForm,
                                ResetPasswordForm)
from flaskbb.user.models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Logs the user in
    """

    if current_user is not None and current_user.is_authenticated():
        return redirect(url_for("user.profile"))

    form = LoginForm(request.form)
    if form.validate_on_submit():
        user, authenticated = User.authenticate(form.login.data,
                                                form.password.data)

        if user and authenticated:
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get("next") or
                            url_for("forum.index"))

        flash(("Wrong username or password"), "danger")
    return render_template("auth/login.html", form=form)


@auth.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    """
    Reauthenticates a user
    """

    if not login_fresh():
        form = ReauthForm(request.form)
        if form.validate_on_submit():
            confirm_login()
            flash(("Reauthenticated"), "success")
            return redirect(request.args.get("next") or
                            url_for("user.profile"))
        return render_template("auth/reauth.html", form=form)
    return redirect(request.args.get("next") or
                    url_for("user.profile", username=current_user.username))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash(("Logged out"), "success")
    return redirect(url_for("forum.index"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new user
    """

    if current_user is not None and current_user.is_authenticated():
        return redirect(url_for("user.profile"))

    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = form.save()
        login_user(user)

        flash(("Thanks for registering"), "success")
        return redirect(url_for("user.profile", username=current_user.username))
    return render_template("auth/register.html", form=form)


@auth.route("/resetpassword", methods=["GET", "POST"])
def reset_password():
    """
    Resets the password from a user
    """

    form = ResetPasswordForm(request.form)
    if form.validate_on_submit():
        user1 = User.query.filter_by(email=form.email.data).first()
        user2 = User.query.filter_by(username=form.username.data).first()

        if user1.email == user2.email:
            password = generate_random_pass()
            user1.password = generate_password_hash(password)
            db.session.commit()

            send_new_password(user1, password)

            flash(("E-Mail sent! Please check your inbox."), "info")
            return redirect(url_for("auth.login"))
        else:
            flash(("You have entered an username or email that is not linked \
                with your account"), "danger")

    return render_template("auth/reset_password.html", form=form)
