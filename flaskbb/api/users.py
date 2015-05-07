# -*- coding: utf-8 -*-
"""
    flaskbb.api.users
    ~~~~~~~~~~~~~~~~~

    The User API.
    TODO: Permission checks.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flask_restful import Resource, reqparse, fields, marshal

from flaskbb.extensions import oauth_provider
from flaskbb.utils.helpers import populate_model
from flaskbb.user.models import User

# request parsers
addparser = reqparse.RequestParser()
addparser.add_argument('username', type=str, required=True, location="json")
addparser.add_argument('email', type=str, required=True, location='json')
addparser.add_argument('password', type=str, required=True, location='json')

updateparser = reqparse.RequestParser()
updateparser.add_argument('email', type=str, location='json')
updateparser.add_argument('birthday', type=str, location='json')
updateparser.add_argument('gender', type=str, location='json')
updateparser.add_argument('website', type=str, location='json')
updateparser.add_argument('location', type=str, location='json')
updateparser.add_argument('signature', type=str, location='json')
updateparser.add_argument('notes', type=str, location='json')
updateparser.add_argument('theme', type=str, location='json')
updateparser.add_argument('language', type=str, location='json')


# fields
user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'date_joined': fields.DateTime,
    'lastseen': fields.DateTime,
    'birthday': fields.DateTime,
    'gender': fields.String,
    'website': fields.String,
    'location': fields.String,
    'signature': fields.String,
    'notes': fields.String,
    'theme': fields.String,
    'language': fields.String,
    'post_count': fields.Integer,
    'primary_group': fields.String(attribute="primary_group.name")
}


class UserListAPI(Resource):

    def __init__(self):
        super(UserListAPI, self).__init__()

    def get(self):
        users = {'users': [marshal(user, user_fields)
                           for user in User.query.all()]}
        return users

    @oauth_provider.require_oauth("admin")
    def post(self):
        args = addparser.parse_args()
        user = User(username=args['username'],
                    password=args['password'],
                    email=args['email'],
                    date_joined=datetime.utcnow(),
                    primary_group_id=4)
        user.save()

        return {'user': marshal(user, user_fields)}, 201


class UserAPI(Resource):

    def __init__(self):
        super(UserAPI, self).__init__()

    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first_or_404()

        return {'user': marshal(user, user_fields)}

    @oauth_provider.require_oauth("user")
    def put(self, user_id):
        """Updates a user."""
        user = User.query.filter_by(id=user_id).first_or_404()

        args = updateparser.parse_args()
        user = populate_model(user, args, commit=True)
        return {'user': marshal(user, user_fields)}

    @oauth_provider.require_oauth("admin")
    def delete(self, user_id):
        user = User.query.filter_by(id=user_id).first_or_404()

        user.delete()
        return {'result': True}
