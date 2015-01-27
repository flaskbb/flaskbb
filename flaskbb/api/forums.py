# -*- coding: utf-8 -*-
"""
    flaskbb.api.forums
    ~~~~~~~~~~~~~~~~~~

    The Forum API.
    TODO: - POST/PUT/DELETE stuff
          - Permission checks.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_restful import Resource, fields, marshal, abort, reqparse

from flaskbb.forum.models import Category, Forum, Topic, Post


category_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'slug': fields.String,
    'forums': fields.String(attribute="forums.title")
}

forum_fields = {
    'id': fields.Integer,
    'category_id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'position': fields.Integer,
    'locked': fields.Boolean,
    'show_moderators': fields.Boolean,
    'external': fields.String,
    'post_count': fields.Integer,
    'topic_count': fields.Integer,
    'last_post_id': fields.Integer,
    'last_post_title': fields.String,
    'last_post_created': fields.DateTime,
    'last_post_username': fields.String
}

topic_fields = {
    'id': fields.Integer,
    'forum_id': fields.Integer,
    'title': fields.String,
    'user_id': fields.Integer,
    'username': fields.String,
    'date_created': fields.DateTime,
    'last_updated': fields.DateTime,
    'locked': fields.Boolean,
    'important': fields.Boolean,
    'views': fields.Integer,
    'post_count': fields.Integer,
    'content': fields.String(attribute='first_post.content'),
    'first_post_id': fields.Integer,
    'last_post_id': fields.Integer,
}

post_fields = {
    'id': fields.Integer,
    'topic_id': fields.Integer,
    'user_id': fields.Integer,
    'username': fields.String,
    'content': fields.String,
    'date_created': fields.DateTime,
    'date_modified': fields.DateTime,
    'modified_by': fields.String
}


class CategoryListAPI(Resource):

    def __init__(self):
        super(CategoryListAPI, self).__init__()

    def get(self):
        categories_list = Category.query.order_by(Category.position).all()

        categories = {'categories': [marshal(category, category_fields)
                                     for category in categories_list]}
        return categories


class CategoryAPI(Resource):

    def __init__(self):
        super(CategoryAPI, self).__init__()

    def get(self, id):
        category = Category.query.filter_by(id=id).first()

        if not category:
            abort(404)

        return {'category': marshal(category, category_fields)}


class ForumListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('category_id', type=int, location='args')
        super(ForumListAPI, self).__init__()

    def get(self):
        # get the forums for a category or get all
        args = self.reqparse.parse_args()
        if args['category_id'] is not None:
            forums_list = Forum.query.\
                filter(Forum.category_id == args['category_id']).\
                order_by(Forum.position).all()
        else:
            forums_list = Forum.query.order_by(Forum.position).all()

        forums = {'forums': [marshal(forum, forum_fields)
                             for forum in forums_list]}
        return forums


class ForumAPI(Resource):

    def __init__(self):
        super(ForumAPI, self).__init__()

    def get(self, id):
        forum = Forum.query.filter_by(id=id).first()

        if not forum:
            abort(404)

        return {'forum': marshal(forum, forum_fields)}


class TopicListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('page', type=int, location='args')
        self.reqparse.add_argument('per_page', type=int, location='args')
        self.reqparse.add_argument('forum_id', type=int, location='args')
        super(TopicListAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        page = args['page'] or 1
        per_page = args['per_page'] or 20
        forum_id = args['forum_id']

        if forum_id is not None:
            topics_list = Topic.query.filter_by(forum_id=forum_id).\
                order_by(Topic.important.desc(), Topic.last_updated.desc()).\
                paginate(page, per_page, True)
        else:
            topics_list = Topic.query.\
                order_by(Topic.important.desc(), Topic.last_updated.desc()).\
                paginate(page, per_page, True)

        topics = {'topics': [marshal(topic, topic_fields)
                             for topic in topics_list.items]}
        return topics


class TopicAPI(Resource):

    def __init__(self):
        super(TopicAPI, self).__init__()

    def get(self, id):
        topic = Topic.query.filter_by(id=id).first()

        if not topic:
            abort(404)

        return {'topic': marshal(topic, topic_fields)}


class PostListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('page', type=int, location='args')
        self.reqparse.add_argument('per_page', type=int, location='args')
        self.reqparse.add_argument('topic_id', type=int, location='args')
        super(PostListAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        page = args['page'] or 1
        per_page = args['per_page'] or 20
        topic_id = args['topic_id']

        if topic_id is not None:
            posts_list = Post.query.\
                filter_by(topic_id=id).\
                order_by(Post.id.asc()).\
                paginate(page, per_page)
        else:
            posts_list = Post.query.\
                order_by(Post.id.asc()).\
                paginate(page, per_page)

        posts = {'posts': [marshal(post, post_fields)
                           for post in posts_list.items]}
        return posts


class PostAPI(Resource):

    def __init__(self):
        super(PostAPI, self).__init__()

    def get(self, id):
        post = Post.query.filter_by(id=id).first()

        if not post:
            abort(404)

        return {'post': marshal(post, post_fields)}
