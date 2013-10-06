# -*- coding: utf-8 -*-
"""
    flaskbb.user.models
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the models for the user.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from werkzeug import generate_password_hash, check_password_hash
from flask import current_app
from flask.ext.login import UserMixin, AnonymousUserMixin
from flaskbb.extensions import db, cache
from flaskbb.forum.models import Post, Topic


groups_users = db.Table('groups_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('group_id', db.Integer(), db.ForeignKey('groups.id')))


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    description = db.Column(db.String(80))

    admin = db.Column(db.Boolean, default=False)
    super_mod = db.Column(db.Boolean, default=False)
    mod = db.Column(db.Boolean, default=False)
    guest = db.Column(db.Boolean, default=False)
    banned = db.Column(db.Boolean, default=False)

    editpost = db.Column(db.Boolean, default=True)
    deletepost = db.Column(db.Boolean, default=False)
    deletetopic = db.Column(db.Boolean, default=False)
    posttopic = db.Column(db.Boolean, default=True)
    postreply = db.Column(db.Boolean, default=True)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    _password = db.Column('password', db.String(80), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow())
    lastseen = db.Column(db.DateTime, default=datetime.utcnow())
    birthday = db.Column(db.DateTime)
    gender = db.Column(db.String)
    website = db.Column(db.String)
    location = db.Column(db.String)
    signature = db.Column(db.String)
    avatar = db.Column(db.String)
    notes = db.Column(db.Text(5000))

    posts = db.relationship("Post", backref="user", lazy="dynamic")
    topics = db.relationship("Topic", backref="user", lazy="dynamic")

    post_count = db.Column(db.Integer, default=0)

    primary_group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

    primary_group = db.relationship('Group', lazy="joined",
                                    backref="user_group", uselist=False,
                                    foreign_keys=[primary_group_id])

    groups = db.relationship('Group',
                             secondary=groups_users,
                             primaryjoin=(groups_users.c.user_id == id),
                             backref=db.backref('users', lazy='dynamic'),
                             lazy='dynamic')

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

    def _make_token(self, data, timeout):
        s = Serializer(current_app.config['SECRET_KEY'], timeout)
        return s.dumps(data)

    def _verify_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        data = None
        expired, invalid = False, False
        try:
            data = s.loads(token)
        except SignatureExpired:
            expired = True
        except Exception:
            invalid = True
        return expired, invalid, data

    def make_reset_token(self, expiration=3600):
        return self._make_token({'id': self.id, 'op': 'reset'}, expiration)

    def verify_reset_token(self, token):
        expired, invalid, data = self._verify_token(token)
        if data and data.get('id') == self.id and data.get('op') == 'reset':
            data = True
        else:
            data = False
        return expired, invalid, data

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

    def add_to_group(self, group):
        """
        Adds the user to the `group` if he isn't in it.
        """
        if not self.in_group(group):
            self.groups.append(group)
            return self

    def remove_from_group(self, group):
        """
        Removes the user from the `group` if he is in it.
        """
        if self.in_group(group):
            self.groups.pop(group)
            return self

    def in_group(self, group):
        """
        Returns True if the user is in the specified group
        """
        return self.groups.filter(
            groups_users.c.group_id == group.id).count() > 0

    @cache.memoize(60*5)
    def get_permissions(self, exclude=None):
        """
        Returns a dictionary with all the permissions the user has.
        """
        exclude = exclude or []
        exclude.extend(['id', 'name', 'description'])

        perms = {}
        # Iterate over all groups
        for group in self.groups.all():
            for c in group.__table__.columns:
                # try if the permission already exists in the dictionary
                # and if the permission is true, set it to True
                try:
                    if not perms[c.name] and getattr(group, c.name):
                        perms[c.name] = True

                # if the permission doesn't exist in the dictionary
                # add it to the dictionary
                except KeyError:
                    # if the permission is in the exclude list,
                    # skip to the next permission
                    if c.name in exclude:
                        continue
                    perms[c.name] = getattr(group, c.name)
        return perms

    def has_perm(self, perm):
        """
        Returns True if the user has the specified permission.
        """
        permissions = self.get_permissions()
        if permissions['admin'] or permissions['super_mod']:
            return True

        if permissions[perm]:
            return True
        return False

    def has_one_perm(self, perms_list):
        """
        Returns True if the user has one of the provided permissions.
        """
        for perm in perms_list:
            if self.has_perm(perm):
                return True
        return False

    def has_perms(self, perms_list):
        """
        Returns True if the user has each of the specified permissions.
        It is basically the same as has_perm but every permission in the
        provided list needs to be True to return True.
        """
        # Iterate over the list with the permissions
        for perm in perms_list:
            if self.has_perm(perm):
                # After checking the permission,
                # we can remove the perm from the list
                perms_list.remove(perm)
            else:
                return False
        return True

    def save(self, groups=None):
        if groups:
            # TODO: Only remove/add groups that are selected
            all_groups = self.groups.all()
            if all_groups:
                for group in all_groups:
                    self.groups.remove(group)
                db.session.commit()

            for group in groups:
                self.groups.append(group)
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class Guest(AnonymousUserMixin):
    @cache.memoize(60*5)
    def get_permissions(self, exclude=None):
        """
        Returns a dictionary with all permissions the user has
        """
        exclude = exclude or []
        exclude.extend(['id', 'name', 'description'])

        perms = {}
        # Get the Guest group
        group = Group.query.filter_by(guest=True).first()
        for c in group.__table__.columns:
            # try if the permission already exists in the dictionary
            # and if the permission is true, go to the next permission
            try:
                if perms[c.name]:
                    continue
            # if the permission doesn't exist in the dictionary
            # add it to the dictionary
            except KeyError:
                # if the permission is in the exclude list,
                # skip to the next permission
                if c.name in exclude:
                    continue
                perms[c.name] = getattr(group, c.name)
        return perms

    def has_perm(self, perm):
        """
        Returns True if the user has the specified permission.
        """
        group = Group.query.filter_by(guest=True).first()
        if getattr(group, perm, True):
            return True
        return False

    def has_one_perm(self, perms_list):
        """
        Returns True if the user has one of the provided permissions.
        """
        group = Group.query.filter_by(guest=True).first()
        for perm in perms_list:
            if getattr(group, perm, True):
                return True
        return False

    def has_perms(self, perms_list):
        """
        Returns True if the user has each of the specified permissions.
        It is basically the same as has_perm but every permission in the
        provided list needs to be True to return True.
        """
        # Iterate overall groups
        group = Group.query.filter_by(guest=True).first()
        # Iterate over the list with the permissions
        for perm in perms_list:
            if getattr(group, perm, True):
                # After checking the permission,
                # we can remove the perm from the list
                perms_list.remove(perm)
            else:
                return False
        return True
