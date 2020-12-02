# -*- coding: utf-8 -*-
"""
    flaskbb.management.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the management views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

from flask_allows import Permission
from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm
from sqlalchemy.orm.session import make_transient, make_transient_to_detached
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import (
    URL,
    DataRequired,
    Email,
    Length,
    Optional,
    ValidationError,
    regexp,
)

from flaskbb.extensions import db
from flaskbb.forum.models import Category, Forum
from flaskbb.user.models import Group, User
from flaskbb.utils.fields import BirthdayField
from flaskbb.utils.helpers import check_image
from flaskbb.utils.requirements import IsAtleastModerator


logger = logging.getLogger(__name__)


USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=_("You can only use letters, numbers or dashes."))


def selectable_forums():
    return Forum.query.order_by(Forum.position)


def selectable_categories():
    return Category.query.order_by(Category.position)


def selectable_groups():
    return Group.query.order_by(Group.id.asc()).all()


def select_primary_group():
    return Group.query.filter(Group.guest != True).order_by(Group.id)


class UserForm(FlaskForm):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required.")),
        is_username])

    email = StringField(_("Email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    password = PasswordField("Password", validators=[
        DataRequired()])

    birthday = BirthdayField(_("Birthday"), format="%d %m %Y", validators=[
        Optional()])

    gender = StringField(_("Gender"), validators=[Optional()])

    location = StringField(_("Location"), validators=[
        Optional()])

    website = StringField(_("Website"), validators=[
        Optional(), URL()])

    avatar = StringField(_("Avatar"), validators=[
        Optional(), URL()])

    signature = TextAreaField(_("Forum signature"), validators=[
        Optional()])

    notes = TextAreaField(_("Notes"), validators=[
        Optional(), Length(min=0, max=5000)])

    activated = BooleanField(_("Is active?"), validators=[
        Optional()])

    primary_group = QuerySelectField(
        _("Primary group"),
        query_factory=select_primary_group,
        get_label="name")

    secondary_groups = QuerySelectMultipleField(
        _("Secondary groups"),
        # TODO: Template rendering errors "NoneType is not callable"
        #       without this, figure out why.
        query_factory=select_primary_group,
        get_label="name")

    submit = SubmitField(_("Save"))

    def validate_username(self, field):
        if hasattr(self, "user"):
            user = User.query.filter(
                db.and_(
                    User.username.like(field.data.lower()),
                    db.not_(User.id == self.user.id)
                )
            ).first()
        else:
            user = User.query.filter(
                User.username.like(field.data.lower())
            ).first()

        if user:
            raise ValidationError(_("This username is already taken."))

    def validate_email(self, field):
        if hasattr(self, "user"):
            user = User.query.filter(
                db.and_(
                    User.email.like(field.data.lower()),
                    db.not_(User.id == self.user.id)
                )
            ).first()
        else:
            user = User.query.filter(
                User.email.like(field.data.lower())
            ).first()

        if user:
            raise ValidationError(_("This email address is already taken."))

    def validate_avatar(self, field):
        if field.data is not None:
            error, status = check_image(field.data)
            if error is not None:
                raise ValidationError(error)
            return status

    def save(self):
        data = self.data
        data.pop('submit', None)
        data.pop('csrf_token', None)
        user = User(**data)
        return user.save()


class AddUserForm(UserForm):
    pass


class EditUserForm(UserForm):
    password = PasswordField("Password", validators=[Optional()])

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        UserForm.__init__(self, *args, **kwargs)


class GroupForm(FlaskForm):
    name = StringField(_("Group name"), validators=[
        DataRequired(message=_("Please enter a name for the group."))])

    description = TextAreaField(_("Description"), validators=[
        Optional()])

    admin = BooleanField(
        _("Is 'Admin' group?"),
        description=_("With this option the group has access to "
                      "the admin panel.")
    )
    super_mod = BooleanField(
        _("Is 'Super Moderator' group?"),
        description=_("Check this, if the users in this group are allowed to "
                      "moderate every forum.")
    )
    mod = BooleanField(
        _("Is 'Moderator' group?"),
        description=_("Check this, if the users in this group are allowed to "
                      "moderate specified forums.")
    )
    banned = BooleanField(
        _("Is 'Banned' group?"),
        description=_("Only one group of type 'Banned' is allowed.")
    )
    guest = BooleanField(
        _("Is 'Guest' group?"),
        description=_("Only one group of type 'Guest' is allowed.")
    )
    editpost = BooleanField(
        _("Can edit posts"),
        description=_("Check this, if the users in this group can edit posts.")
    )
    deletepost = BooleanField(
        _("Can delete posts"),
        description=_("Check this, if the users in this group can delete "
                      "posts.")
    )
    deletetopic = BooleanField(
        _("Can delete topics"),
        description=_("Check this, if the users in this group can delete "
                      "topics.")
    )
    posttopic = BooleanField(
        _("Can create topics"),
        description=_("Check this, if the users in this group can create "
                      "topics.")
    )
    postreply = BooleanField(
        _("Can post replies"),
        description=_("Check this, if the users in this group can post "
                      "replies.")
    )

    mod_edituser = BooleanField(
        _("Moderators can edit user profiles"),
        description=_("Allow moderators to edit another user's profile "
                      "including password and email changes.")
    )

    mod_banuser = BooleanField(
        _("Moderators can ban users"),
        description=_("Allow moderators to ban other users.")
    )

    viewhidden = BooleanField(
        _("Can view hidden posts and topics"),
        description=_("Allows a user to view hidden posts and topics"),
    )

    makehidden = BooleanField(
        _("Can hide posts and topics"),
        description=_("Allows a user to hide posts and topics"),
    )

    submit = SubmitField(_("Save"))

    def validate_name(self, field):
        if hasattr(self, "group"):
            group = Group.query.filter(
                db.and_(
                    Group.name.like(field.data.lower()),
                    db.not_(Group.id == self.group.id)
                )
            ).first()
        else:
            group = Group.query.filter(
                Group.name.like(field.data.lower())
            ).first()

        if group:
            raise ValidationError(_("This group name is already taken."))

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
            raise ValidationError(_("There is already a group of type "
                                    "'Banned'."))

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
            raise ValidationError(_("There is already a group of type "
                                    "'Guest'."))

    def validate(self):
        if not super(GroupForm, self).validate():
            return False

        result = True
        permission_fields = (
            self.editpost, self.deletepost, self.deletetopic,
            self.posttopic, self.postreply, self.mod_edituser,
            self.mod_banuser, self.viewhidden, self.makehidden
        )
        group_fields = [
            self.admin, self.super_mod, self.mod, self.banned, self.guest
        ]
        # we do not allow to modify any guest permissions
        if self.guest.data:
            for field in permission_fields:
                if field.data:
                    # if done in 'validate_guest' it would display this
                    # warning on the fields
                    field.errors.append(
                        _("Can't assign any permissions to this group.")
                    )
                    result = False

        checked = []
        for field in group_fields:
            if field.data and field.data in checked:
                if len(checked) > 1:
                    field.errors.append(
                        "A group can't have multiple group types."
                    )
                    result = False
            else:
                checked.append(field.data)

        return result

    def save(self):
        data = self.data
        data.pop('submit', None)
        data.pop('csrf_token', None)
        group = Group(**data)
        return group.save()


class EditGroupForm(GroupForm):
    def __init__(self, group, *args, **kwargs):
        self.group = group
        kwargs['obj'] = self.group
        GroupForm.__init__(self, *args, **kwargs)


class AddGroupForm(GroupForm):
    pass


class ForumForm(FlaskForm):
    title = StringField(
        _("Forum title"),
        validators=[DataRequired(message=_("Please enter a forum title."))]
    )

    description = TextAreaField(
        _("Description"),
        validators=[Optional()],
        description=_("You can format your description with Markdown.")
    )

    position = IntegerField(
        _("Position"),
        default=1,
        validators=[DataRequired(message=_("Please enter a position for the"
                                           "forum."))]
    )

    category = QuerySelectField(
        _("Category"),
        query_factory=selectable_categories,
        allow_blank=False,
        get_label="title",
        description=_("The category that contains this forum.")
    )

    external = StringField(
        _("External link"),
        validators=[Optional(), URL()],
        description=_("A link to a website i.e. 'http://flaskbb.org'.")
    )

    moderators = StringField(
        _("Moderators"),
        description=_("Comma separated usernames. Leave it blank if you do "
                      "not want to set any moderators.")
    )

    show_moderators = BooleanField(
        _("Show moderators"),
        description=_("Do you want to show the moderators on the index page?")
    )

    locked = BooleanField(
        _("Locked?"),
        description=_("Disable new posts and topics in this forum.")
    )

    groups = QuerySelectMultipleField(
        _("Group access"),
        query_factory=selectable_groups,
        get_label="name",
        description=_("Select the groups that can access this forum.")
    )

    submit = SubmitField(_("Save"))

    def validate_external(self, field):
        if hasattr(self, "forum"):
            if self.forum.topics.count() > 0:
                raise ValidationError(_("You cannot convert a forum that "
                                        "contains topics into an "
                                        "external link."))

    def validate_show_moderators(self, field):
        if field.data and not self.moderators.data:
            raise ValidationError(_("You also need to specify some "
                                    "moderators."))

    def validate_moderators(self, field):
        approved_moderators = []

        if field.data:
            moderators = [mod.strip() for mod in field.data.split(',')]
            users = User.query.filter(User.username.in_(moderators))
            for user in users:
                if not Permission(IsAtleastModerator, identity=user):
                    raise ValidationError(
                        _("%(user)s is not in a moderators group.",
                            user=user.username)
                    )
                else:
                    approved_moderators.append(user)
        field.data = approved_moderators

    def save(self):
        data = self.data
        # delete submit and csrf_token from data
        data.pop('submit', None)
        data.pop('csrf_token', None)
        forum = Forum(**data)
        return forum.save()


class EditForumForm(ForumForm):

    id = HiddenField()

    def __init__(self, forum, *args, **kwargs):
        self.forum = forum
        kwargs['obj'] = self.forum
        ForumForm.__init__(self, *args, **kwargs)

    def save(self):
        data = self.data
        # delete submit and csrf_token from data
        data.pop('submit', None)
        data.pop('csrf_token', None)
        forum = Forum(**data)
        # flush SQLA info from created instance so that it can be merged
        make_transient(forum)
        make_transient_to_detached(forum)

        return forum.save()


class AddForumForm(ForumForm):
    pass


class CategoryForm(FlaskForm):
    title = StringField(_("Category title"), validators=[
        DataRequired(message=_("Please enter a category title."))])

    description = TextAreaField(
        _("Description"),
        validators=[Optional()],
        description=_("You can format your description with Markdown.")
    )

    position = IntegerField(
        _("Position"),
        default=1,
        validators=[DataRequired(message=_("Please enter a position for the "
                                           "category."))]
    )

    submit = SubmitField(_("Save"))

    def save(self):
        data = self.data
        # delete submit and csrf_token from data
        data.pop('submit', None)
        data.pop('csrf_token', None)
        category = Category(**data)
        return category.save()
