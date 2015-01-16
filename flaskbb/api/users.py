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

from flask_restful import Resource, reqparse, fields, marshal, abort

from flaskbb.api import auth
from flaskbb.user.models import User

# CREATE NEW USER
# curl -u test:test1 -i -H "Content-Type: application/json" -X POST -d '{"username":"test6", "password": "test", "email": "test6@example.org"}' http://localhost:8080/api/users

# UPDATE USER
# curl -u test1:test -i -H "Content-Type: application/json" -X PUT -d '{"email": "test7@example.org"}' http://localhost:8080/api/users/5

# GET USER
# curl -i http://localhost:8080/api/users

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
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', type=str, required=True,
                                   location="json")
        self.reqparse.add_argument('email', type=str, required=True,
                                   location='json')
        self.reqparse.add_argument('password', type=str, required=True,
                                   location='json')
        self.user_fields = user_fields
        super(UserListAPI, self).__init__()

    def get(self):
        users = {'users': [marshal(user, user_fields)
                           for user in User.query.all()]}
        return users

    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        user = User(username=args['username'],
                    password=args['password'],
                    email=args['email'],
                    date_joined=datetime.utcnow(),
                    primary_group_id=4)
        user.save()

        return {'user': marshal(user, user_fields)}, 201


class UserAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email', type=str, location='json')
        self.reqparse.add_argument('birthday', type=str, location='json')
        self.reqparse.add_argument('gender', type=str, location='json')
        self.reqparse.add_argument('website', type=str, location='json')
        self.reqparse.add_argument('location', type=str, location='json')
        self.reqparse.add_argument('signature', type=str, location='json')
        self.reqparse.add_argument('notes', type=str, location='json')
        self.reqparse.add_argument('theme', type=str, location='json')
        self.reqparse.add_argument('language', type=str, location='json')

        super(UserAPI, self).__init__()

    def get(self, id):
        user = User.query.filter_by(id=id).first()

        if not user:
            abort(404)

        return {'user': marshal(user, user_fields)}

    @auth.login_required
    def put(self, id):
        user = User.query.filter_by(id=id).first()

        if not user:
            abort(404)

        args = self.reqparse.parse_args()
        for k, v in args.items():
            if v is not None:
                setattr(user, k, v)
        user.save()
        return {'user': marshal(user, user_fields)}

    @auth.login_required
    def delete(self, id):
        user = User.query.filter_by(id=id).first()

        if not user:
            abort(404)

        user.delete()
        return {'result': True}
