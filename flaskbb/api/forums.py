# -*- coding: utf-8 -*-
"""
    flaskbb.api.forums
    ~~~~~~~~~~~~~~~~~~

    The Forum API.
    TODO: Permission checks.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flask_restful import Resource, reqparse, fields, marshal, abort

from flaskbb.api import auth
from flaskbb.forum.models import Category, Forum, Topic, Post


class CategoryListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(CategoryListAPI, self).__init__()

    def get(self):
        pass

    @auth.login_required
    def post(self):
        pass


class CategoryAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(CategoryAPI, self).__init__()

    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass


class ForumListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ForumListAPI, self).__init__()

    def get(self):
        pass

    @auth.login_required
    def post(self):
        pass


class ForumAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ForumAPI, self).__init__()

    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass


class TopicListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(TopicListAPI, self).__init__()

    def get(self):
        pass

    @auth.login_required
    def post(self):
        pass


class TopicAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(TopicAPI, self).__init__()

    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass


class PostListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(PostListAPI, self).__init__()

    def get(self):
        pass

    @auth.login_required
    def post(self):
        pass


class PostAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(PostAPI, self).__init__()

    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass
