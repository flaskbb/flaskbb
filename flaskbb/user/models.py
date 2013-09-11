# -*- coding: utf-8 -*-
"""
    flaskbb.user.models
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the models for the user.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from werkzeug import generate_password_hash, check_password_hash
from flask import current_app
from flask.ext.login import UserMixin

from flaskbb.extensions import db
from flaskbb.forum.models import Post, Topic


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    _password = db.Column('password', db.String(80), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow())
    post_count = db.Column(db.Integer, default=0)
    lastseen = db.Column(db.DateTime, default=datetime.utcnow())
    birthday = db.Column(db.DateTime)
    gender = db.Column(db.String)
    website = db.Column(db.String)
    location = db.Column(db.String)
    signature = db.Column(db.String)
    avatar = db.Column(db.String, default="/static/uploads/avatar/default.png")
    notes = db.Column(db.Text(5000), default="User has not added any notes about him.")

    posts = db.relationship("Post", backref="user", lazy="dynamic")
    topics = db.relationship("Topic", backref="user", lazy="dynamic")

    post_count = db.Column(db.Integer, default=0) # Bye bye normalization

    def __repr__(self):
        return "Username: %s" % self.username

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    password = db.synonym('_password',
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        """
        Check passwords. If passwords match it returns true, else false
        """
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def authenticate(cls, login, password):
        """
        A classmethod for authenticating users
        It returns true if the user exists and has entered a correct password
        """
        user = cls.query.filter(db.or_(User.username == login,
                                       User.email == login)).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False
        return user, authenticated

    @property
    def last_post(self):
        """
        Returns the latest post from the user
        """
        return Post.query.filter(Post.user_id == self.id).\
            order_by(Post.date_created.desc()).first()

    def all_topics(self, page):
        """
        Returns a paginated query result with all topics the user has created.
        """
        return Topic.query.filter(Topic.user_id == self.id).\
            order_by(Topic.last_post_id.desc()).\
            paginate(page, current_app.config['TOPICS_PER_PAGE'], False)

    def all_posts(self, page):
        """
        Returns a paginated query result with all posts the user has created.
        """
        return Post.query.filter(Post.user_id == self.id).\
            paginate(page, current_app.config['TOPICS_PER_PAGE'], False)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
