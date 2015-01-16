# -*- coding: utf-8 -*-
"""
    flaskbb.api
    ~~~~~~~~~~~

    The API provides the possibility to get the data in JSON format
    for the views.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import jsonify, make_response

from flask_httpauth import HTTPBasicAuth

from flaskbb.user.models import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    user, authenticated = User.authenticate(username, password)
    if user and authenticated:
        return True
    return False


@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)
