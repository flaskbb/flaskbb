# -*- coding: utf-8 -*-
"""
    flaskbb.management.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the management views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import Form
from wtforms import (StringField, TextAreaField, PasswordField, IntegerField,
                     BooleanField, SelectField, DateField, SubmitField)
from wtforms.validators import (DataRequired, Optional, Email, regexp, Length,
                                URL, ValidationError)

from wtforms.ext.sqlalchemy.fields import (QuerySelectField,
                                           QuerySelectMultipleField)
from flask.ext.babel import lazy_gettext as _

from flaskbb.utils.widgets import SelectDateWidget
from flaskbb.extensions import db
from flaskbb.forum.models import Forum, Category
from flaskbb.user.models import User, Group

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=_("You can only use letters, numbers or dashes"))


def selectable_forums():
    return Forum.query.order_by(Forum.position)


def selectable_categories():
    return Category.query.order_by(Category.position)


def select_primary_group():
    return Group.query.filter(Group.guest != True).order_by(Group.id)


class UserForm(Form):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A Username is required.")),
        is_username])

    email = StringField(_("E-Mail"), validators=[
        DataRequired(message=_("A E-Mail Address is required.")),
        Email(message=_("Invalid E-Mail Address."))])

    password = PasswordField("Password", validators=[
        Optional()])

    birthday = DateField(_("Birthday"), format="%d %m %Y",
                         widget=SelectDateWidget(),
                         validators=[Optional()])

    gender = SelectField(_("Gender"), default="None", choices=[
        ("None", ""),
        ("Male", _("Male")),
        ("Female", _("Female"))])

    location = StringField(_("Location"), validators=[
        Optional()])

    website = StringField(_("Website"), validators=[
        Optional(), URL()])

    avatar = StringField(_("Avatar"), validators=[
        Optional(), URL()])

    signature = TextAreaField(_("Forum Signature"), validators=[
        Optional(), Length(min=0, max=250)])

    notes = TextAreaField(_("Notes"), validators=[
        Optional(), Length(min=0, max=5000)])

    primary_group = QuerySelectField(
        _("Primary Group"),
        query_factory=select_primary_group,
        get_label="name")

    secondary_groups = QuerySelectMultipleField(
        _("Secondary Groups"),
        # TODO: Template rendering errors "NoneType is not callable"
        #       without this, figure out why.
        query_factory=select_primary_group,
        get_label="name")

    submit = SubmitField(_("Save"))

    def validate_username(self, field):
        if hasattr(self, "user"):
            user = User.query.filter(
                db.and_(
                    User.username.like(field.data),
                    db.not_(User.id == self.user.id)
                )
            ).first()
        else:
            user = User.query.filter(User.username.like(field.data)).first()

        if user:
            raise ValidationError(_("This Username is taken."))

    def validate_email(self, field):
        if hasattr(self, "user"):
            user = User.query.filter(
                db.and_(
                    User.email.like(field.data),
                    db.not_(User.id == self.user.id)
                )
            ).first()
        else:
            user = User.query.filter(User.email.like(field.data)).first()

        if user:
            raise ValidationError(_("This E-Mail is taken."))

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
    name = StringField(_("Group Name"), validators=[
        DataRequired(message=_("A Group name is required."))])

    description = TextAreaField(_("Description"), validators=[
        Optional()])

    admin = BooleanField(
        _("Is Admin Group?"),
        description=_("With this option the group has access to "
                      "the admin panel.")
    )
    super_mod = BooleanField(
        _("Is Super Moderator Group?"),
        description=_("Check this if the users in this group are allowed to "
                      "moderate every forum")
    )
    mod = BooleanField(
        _("Is Moderator Group?"),
        description=_("Check this if the users in this group are allowed to "
                      "moderate specified forums")
    )
    banned = BooleanField(
        _("Is Banned Group?"),
        description=_("Only one Banned group is allowed")
    )
    guest = BooleanField(
        _("Is Guest Group?"),
        description=_("Only one Guest group is allowed")
    )
    editpost = BooleanField(
        _("Can edit posts"),
        description=_("Check this if the users in this group can edit posts")
    )
    deletepost = BooleanField(
        _("Can delete posts"),
        description=_("Check this is the users in this group can delete posts")
    )
    deletetopic = BooleanField(
        _("Can delete topics"),
        description=_("Check this is the users in this group can delete topics")
    )
    posttopic = BooleanField(
        _("Can create topics"),
        description=_("Check this is the users in this group can create topics")
    )
    postreply = BooleanField(
        _("Can post replies"),
        description=_("Check this is the users in this group can post replies")
    )

    mod_edituser = BooleanField(
        _("Moderators can edit user profiles"),
        description=_("Allow moderators to edit a another users profile "
                      "including password and email changes.")
    )

    mod_banuser = BooleanField(
        _("Moderators can ban users"),
        description=_("Allow moderators to ban other users")
    )

    submit = SubmitField(_("Save"))

    def validate_name(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(
                    Group.name.like(field.data),
                    db.not_(Group.id == self.group.id)
                )
            ).first()
        else:
            group = Group.query.filter(Group.name.like(field.data)).first()

        if group:
            raise ValidationError(_("This Group name is taken."))

    def validate_banned(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(
                    Group.banned,
                    db.not_(Group.id == self.group.id)
                )
            ).count()
        else:
            group = Group.query.filter_by(banned=True).count()

        if field.data and group > 0:
            raise ValidationError(_("There is already a Banned group."))

    def validate_guest(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(
                    Group.guest,
                    db.not_(Group.id == self.group.id)
                )
            ).count()
        else:
            group = Group.query.filter_by(guest=True).count()

        if field.data and group > 0:
            raise ValidationError(_("There is already a Guest group."))

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
    title = StringField(
        _("Forum Title"),
        validators=[DataRequired(message=_("A Forum Title is required."))]
    )

    description = TextAreaField(
        _("Description"),
        validators=[Optional()],
        description=_("You can format your description with BBCode.")
    )

    position = IntegerField(
        _("Position"),
        default=1,
        validators=[DataRequired(message=_("The Forum Position is required."))]
    )

    category = QuerySelectField(
        _("Category"),
        query_factory=selectable_categories,
        allow_blank=False,
        get_label="title",
        description=_("The category that contains this forum.")
    )

    external = StringField(
        _("External Link"),
        validators=[Optional(), URL()],
        description=_("A link to a website i.e. 'http://flaskbb.org'")
    )

    moderators = StringField(
        _("Moderators"),
        description=_("Comma seperated usernames. Leave it blank if you do not "
                      "want to set any moderators.")
    )

    show_moderators = BooleanField(
        _("Show Moderators"),
        description=_("Do you want show the moderators on the index page?")
    )

    locked = BooleanField(
        _("Locked?"),
        description=_("Disable new posts and topics in this forum.")
    )

    submit = SubmitField(_("Save"))

    def validate_external(self, field):
        if hasattr(self, "forum"):
            if self.forum.topics:
                raise ValidationError(_("You cannot convert a forum that "
                                        "contain topics in a external link"))

    def validate_show_moderators(self, field):
        if field.data and not self.moderators.data:
            raise ValidationError(_("You also need to specify some "
                                    "moderators."))

    def validate_moderators(self, field):
        approved_moderators = list()

        if field.data:
            # convert the CSV string in a list
            moderators = field.data.split(",")
            # remove leading and ending spaces
            moderators = [mod.strip() for mod in moderators]
            for moderator in moderators:
                # Check if the usernames exist
                user = User.query.filter_by(username=moderator).first()

                # Check if the user has the permissions to moderate a forum
                if user:
                    if not (user.get_permissions()["mod"] or
                            user.get_permissions()["admin"] or
                            user.get_permissions()["super_mod"]):
                        raise ValidationError(
                            _("%(user)s is not in a moderators group",
                              user=user.username)
                        )
                    else:
                        approved_moderators.append(user)
                else:
                    raise ValidationError(_("User %(moderator)s not found",
                                            moderator=moderator))
            field.data = approved_moderators

        else:
            field.data = approved_moderators

    def save(self):
        forum = Forum(title=self.title.data,
                      description=self.description.data,
                      position=self.position.data,
                      external=self.external.data,
                      show_moderators=self.show_moderators.data,
                      locked=self.locked.data)

        if self.moderators.data:
            # is already validated
            forum.moderators = self.moderators.data

        forum.category_id = self.category.data.id

        return forum.save()


class EditForumForm(ForumForm):
    def __init__(self, forum, *args, **kwargs):
        self.forum = forum
        kwargs['obj'] = self.forum
        super(ForumForm, self).__init__(*args, **kwargs)


class AddForumForm(ForumForm):
    pass


class CategoryForm(Form):
    title = StringField(_("Category Title"), validators=[
        DataRequired(message=_("A Category Title is required."))])

    description = TextAreaField(
        _("Description"),
        validators=[Optional()],
        description=_("You can format your description with BBCode.")
    )

    position = IntegerField(
        _("Position"),
        default=1,
        validators=[DataRequired(message=_("The Category Position is "
                                           "required."))]
    )

    submit = SubmitField(_("Save"))

    def save(self):
        category = Category(**self.data)
        return category.save()
