from flask import flash
from flask_babelplus import gettext as _
from flask_login import login_user

from . import impl
from ..email import send_activation_token
from ..user.models import User
from ..utils.settings import flaskbb_config


@impl
def flaskbb_event_user_registered(username):
    user = User.query.filter_by(username=username).first()

    if flaskbb_config["ACTIVATE_ACCOUNT"]:
        send_activation_token.delay(
            user_id=user.id, username=user.username, email=user.email
        )
        flash(
            _(
                "An account activation email has been sent to "
                "%(email)s",
                email=user.email
            ), "success"
        )
    else:
        login_user(user)
        flash(_("Thanks for registering."), "success")
