# -*- coding: utf-8 -*-
"""
    flaskbb.admin.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the admin views.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import Form
from wtforms import (TextField, TextAreaField, PasswordField, IntegerField,
                     BooleanField, SelectField, DateField)
from wtforms.validators import (Required, Optional, Email, regexp, Length, URL,
                                ValidationError)

from wtforms.ext.sqlalchemy.fields import (QuerySelectField,
                                           QuerySelectMultipleField)

from flaskbb.utils.widgets import SelectDateWidget
from flaskbb.extensions import db
from flaskbb.forum.models import Forum
from flaskbb.user.models import User, Group

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=("You can only use letters, numbers or dashes"))


def selectable_forums():
    return Forum.query.order_by(Forum.id)


def select_primary_group():
    return Group.query.filter(Group.guest == False).order_by(Group.id)


class UserForm(Form):
    username = TextField("Username", validators=[
        Required(),
        is_username])

    email = TextField("E-Mail", validators=[
        Required(),
        Email(message="This email is invalid")])

    password = PasswordField("Password", validators=[
        Optional()])

    birthday = DateField("Birthday", format="%d %m %Y",
                         widget=SelectDateWidget(),
                         validators=[Optional()])

    gender = SelectField("Gender", default="None", choices=[
        ("None", ""),
        ("Male", "Male"),
        ("Female", "Female")])

    location = TextField("Location", validators=[
        Optional()])

    website = TextField("Website", validators=[
        Optional(), URL()])

    avatar = TextField("Avatar", validators=[
        Optional(), URL()])

    signature = TextAreaField("Forum Signature", validators=[
        Optional(), Length(min=0, max=250)])

    notes = TextAreaField("Notes", validators=[
        Optional(), Length(min=0, max=5000)])

    primary_group = QuerySelectField("Primary Group",
                                     query_factory=select_primary_group,
                                     get_label="name")

    secondary_groups = QuerySelectMultipleField("Secondary Groups",
                                                query_factory=select_primary_group,  # TODO: Template rendering errors "NoneType is not callable" without this, figure out why.
                                                allow_blank=True,
                                                get_label="name")

    def validate_username(self, field):
        if hasattr(self, "user"):
            user = User.query.filter(
                db.and_(User.username.like(field.data),
                        db.not_(User.id == self.user.id)
                        )
            ).first()
        else:
            user = User.query.filter(User.username.like(field.data)).first()

        if user:
            raise ValidationError("This username is taken")

    def validate_email(self, field):
        if hasattr(self, "user"):
            user = User.query.filter(
                db.and_(User.email.like(field.data),
                        db.not_(User.id == self.user.id)
                        )
            ).first()
        else:
            user = User.query.filter(User.email.like(field.data)).first()

        if user:
            raise ValidationError("This email is taken")

    def save(self):
        user = User(**self.data)
        return user.save()


class AddUserForm(UserForm):
    pass


class EditUserForm(UserForm):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(UserForm, self).__init__(*args, **kwargs)


class GroupForm(Form):
    name = TextField("Group Name", validators=[
        Required(message="Group name required")])

    description = TextAreaField("Description", validators=[
        Optional()])

    admin = BooleanField("Is Admin Group?",
                         description="With this option the group has access \
                                      to the admin panel.")
    super_mod = BooleanField("Is Super Moderator Group?",
                             description="Check this if the users in this \
                                          group are allowed to moderate every \
                                          forum")
    mod = BooleanField("Is Moderator Group?",
                       description="Check this if the users in this group are \
                                    allowed to moderate specified forums")
    banned = BooleanField("Is Banned Group?",
                          description="Only one Banned group is allowed")
    guest = BooleanField("Is Guest Group?",
                         description="Only one Guest group is allowed")
    editpost = BooleanField("Can edit posts",
                            description="Check this if the users in this \
                                         group can edit posts")
    deletepost = BooleanField("Can delete posts",
                              description="Check this is the users in this \
                                           group can delete posts")
    deletetopic = BooleanField("Can delete topics",
                               description="Check this is the users in this \
                                            group can delete topics")
    posttopic = BooleanField("Can create topics",
                             description="Check this is the users in this \
                                          group can create topics")
    postreply = BooleanField("Can post replies",
                             description="Check this is the users in this \
                                          group can post replies")

    def validate_name(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(Group.name.like(field.data),
                        db.not_(Group.id == self.group.id)
                        )
            ).first()
        else:
            group = Group.query.filter(Group.name.like(field.data)).first()

        if group:
            raise ValidationError("This name is taken")

    def validate_banned(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(Group.banned == True,
                        db.not_(Group.id == self.group.id)
                        )
            ).count()
        else:
            group = Group.query.filter_by(banned=True).count()

        if field.data and group > 0:
            raise ValidationError("There is already a Banned group")

    def validate_guest(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(Group.guest == True,
                        db.not_(Group.id == self.group.id)
                        )
            ).count()
        else:
            group = Group.query.filter_by(guest=True).count()

        if field.data and group > 0:
            raise ValidationError("There is already a Guest group")

    def save(self):
        group = Group(**self.data)
        return group.save()


class EditGroupForm(GroupForm):
    def __init__(self, group, *args, **kwargs):
        self.group = group
        kwargs['obj'] = self.group
        super(GroupForm, self).__init__(*args, **kwargs)


class AddGroupForm(GroupForm):
    pass


class ForumForm(Form):
    _id = None
    _moderators = set()

    title = TextField("Forum Title", validators=[
        Required(message="Forum title required")])

    description = TextAreaField("Description", validators=[
        Optional()])

    position = IntegerField("Position", default=1, validators=[
        Required(message="Forum position required")])

    parent = QuerySelectField("Parent",
                              query_factory=selectable_forums,
                              allow_blank=True,
                              get_label="title",
                              description="This field is not saved if this \
                                           forum is a category (see \"Is a \
                                           category?\" field below).")

    moderators = TextField("Moderators",
                           description="Comma seperated usernames. Leave it \
                                        blank if you do not want to set any \
                                        moderators.")

    is_category = BooleanField("Is a category?",
                               description="Categories are root-level parents \
                                            for forums. They can not contain \
                                            topics.")

    locked = BooleanField("Locked?", description="Disable new posts and topics \
                                                  in this forum.")

    def validate_parent(self, field):
        if hasattr(field.data, "id"):
            if field.data.id == self._id:
                raise ValidationError("A forum cannot be it's own parent!")

    def validate_moderators(self, field):
        if field.data:
            # Check if the usernames exist
            for moderator in field.data.split(","):
                user = User.query.filter_by(username=moderator).first()

                # Check if the user has the permissions to moderate a forum
                if user:
                    if not user.get_permissions()["mod"]:
                        raise ValidationError("The user is not in a moderators \
                            group")
                    else:
                        self._moderators.add(user.id)
                else:
                    raise ValidationError("User not found")
            field.data = self._moderators

    def save(self):
        forum = Forum(title=self.title.data,
                      description=self.description.data,
                      position=self.position.data)

        if self.moderators.data:
            forum.moderators = self.moderators.data

        if self.is_category.data:
            forum.is_category = True
            forum.parent_id = None
        else:
            forum.parent_id = self.parent.data.id

        return forum.save()
