from flask import flash
from flask_babelplus import gettext as _
from flask_login import login_user

from . import impl
from ..user.models import User
from ..utils.settings import flaskbb_config
from .services.factories import account_activator_factory


@impl
def flaskbb_event_user_registered(username):
    user = User.query.filter_by(username=username).first()

    if flaskbb_config["ACTIVATE_ACCOUNT"]:
        service = account_activator_factory()
        service.initiate_account_activation(user.email)
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
