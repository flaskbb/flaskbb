"""
flaskbb.management.forms
~~~~~~~~~~~~~~~~~~~~~~~~

It provides the forms that are needed for the management views.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
from collections.abc import Mapping, Sequence
from typing import Any, override

import sqlalchemy as sa
from flask_allows2 import Permission
from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import make_transient, make_transient_to_detached
from wtforms import (
    BooleanField,
    DateField,
    Field,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    regexp,
    URL,
    ValidationError,
)
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

from flaskbb.extensions import db
from flaskbb.forum.models import Attachment, Category, Forum, Post
from flaskbb.permissions import permission_registry, PermissionLevel
from flaskbb.user.models import Group, GroupRole, User
from flaskbb.utils.forms import (
    FlaskBBForm,
)
from flaskbb.utils.proxies import current_user
from flaskbb.utils.requirements import IsAdmin, IsAtleastModerator
from flaskbb.utils.uploads import (
    validate_image,
)
from flaskbb.utils.validators import AvatarExtensionValidator, AvatarSizeValidator

logger = logging.getLogger(__name__)


USERNAME_RE = r"^[\w.+-]+$"
is_username = regexp(USERNAME_RE, message=_("You can only use letters, numbers or dashes."))


def selectable_forums():
    return db.session.execute(sa.select(Forum).order_by(Forum.position)).scalars().all()


def selectable_categories():
    return db.session.execute(sa.select(Category).order_by(Category.position)).scalars().all()


def selectable_groups():
    return db.session.execute(sa.select(Group).order_by(Group.id.asc())).scalars().all()


def select_primary_group():
    return (
        db.session.execute(sa.select(Group).where(Group.role != GroupRole.GUEST).order_by(Group.id))
        .scalars()
        .all()
    )


def assignable_groups():
    """The groups the acting user is allowed to hand out.

    Only administrators may grant administrator or super moderator status; a
    super moderator can promote up to moderator. This is enforced server side
    because wtforms-sqlalchemy validates a submitted choice against this list,
    so a hand-crafted POST cannot smuggle in a group that is not offered.
    """
    if Permission(IsAdmin, identity=current_user):
        return select_primary_group()

    return (
        db.session.execute(
            sa.select(Group)
            .where(Group.role.in_([GroupRole.MEMBER, GroupRole.MODERATOR, GroupRole.BANNED]))
            .order_by(Group.id)
        )
        .scalars()
        .all()
    )


class AttachmentSearchForm(FlaskForm):
    search_query = StringField(_("Search"), validators=[DataRequired(), Length(min=3, max=50)])

    submit = SubmitField(_("Search"))

    def get_results(self):
        pattern = "%{}%".format(self.search_query.data or "")
        # outer join: user_id is nullable, an inner join would hide the
        # attachments of deleted users
        return (
            sa.select(Attachment)
            .outerjoin(User, User.id == Attachment.user_id)
            .options(
                joinedload(Attachment.user),
                joinedload(Attachment.post).joinedload(Post.topic),
            )
            .where(
                sa.or_(
                    Attachment.original_filename.ilike(pattern),
                    User.username.ilike(pattern),
                )
            )
            .order_by(Attachment.id.desc())
        )


class UserForm(FlaskBBForm):
    user: User | None = None

    username = StringField(
        _("Username"),
        validators=[
            DataRequired(message=_("A valid username is required.")),
            is_username,
        ],
    )

    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(message=_("A valid email address is required.")),
            Email(message=_("Invalid email address.")),
        ],
    )

    password = PasswordField("Password", validators=[DataRequired()])

    birthday = DateField(_("Birthday"), format="%Y-%m-%d", validators=[Optional()])

    gender = StringField(_("Gender"), validators=[Optional()])

    location = StringField(_("Location"), validators=[Optional()])

    website = StringField(_("Website"), validators=[Optional(), URL()])

    delete_avatar = HiddenField(default="false")

    avatar = FileField(
        _("Avatar"),
        validators=[Optional(), AvatarExtensionValidator(), AvatarSizeValidator()],
    )

    signature = TextAreaField(_("Forum signature"), validators=[Optional()])

    notes = TextAreaField(_("Notes"), validators=[Optional(), Length(min=0, max=5000)])

    activated = BooleanField(_("Is active?"), validators=[Optional()])

    # ModeratorEditUserForm removes both fields by assigning None
    primary_group: QuerySelectField | None = QuerySelectField(
        _("Primary group"), query_factory=select_primary_group, get_label="name"
    )

    secondary_groups: QuerySelectMultipleField | None = QuerySelectMultipleField(
        _("Secondary groups"),
        # TODO: Template rendering errors "NoneType is not callable"
        #       without this, figure out why.
        query_factory=select_primary_group,
        get_label="name",
    )

    submit = SubmitField(_("Save"))

    def validate_username(self, field: Field):
        if self.user is not None:
            user = User.get(
                sa.and_(
                    User.username.like(field.data.lower()),
                    sa.not_(User.id == self.user.id),
                )
            )
        else:
            user = User.get(User.username.like(field.data.lower()))

        if user:
            raise ValidationError(_("This username is already taken."))

    def validate_email(self, field: Field):
        if self.user is not None:
            user = User.get(
                sa.and_(
                    User.email.like(field.data.lower()),
                    sa.not_(User.id == self.user.id),
                )
            )
        else:
            user = User.get(User.email.like(field.data.lower()))

        if user:
            raise ValidationError(_("This email address is already taken."))

    def validate_avatar(self, field: Field):
        if field.data is not None:
            error, status = validate_image(field.data)
            if error is not None:
                raise ValidationError(error)
            return status

    def save(self):
        data = self.data
        data.pop("submit", None)
        data.pop("csrf_token", None)
        user = User(**data)
        return user.save()


class AddUserForm(UserForm):
    pass


class EditUserForm(UserForm):
    password = PasswordField("Password", validators=[Optional()])

    def __init__(self, user: User, *args: Any, **kwargs: Any):
        self.user = user
        kwargs["obj"] = self.user
        UserForm.__init__(self, *args, **kwargs)  # pyright: ignore[reportUnknownMemberType]


class SuperModeratorEditUserForm(EditUserForm):
    """The edit form as seen by super moderators.

    Credentials are administrator territory - being able to set another user's
    password or email address is an account takeover, which is what group
    membership on its own is not. Group assignment stays, but the choices are
    narrowed per actor in ``EditUser`` so that only administrators can hand out
    administrator or super moderator status.

    Assigning ``None`` drops a field from the form, and therefore from
    validation and ``populate_obj`` alike.
    """

    email = None  # type: ignore[assignment]
    password = None  # type: ignore[assignment]
    activated = None  # type: ignore[assignment]


class ModeratorEditUserForm(SuperModeratorEditUserForm):
    """The edit form as seen by moderators, who may only clean up profiles."""

    primary_group = None
    secondary_groups = None


def role_choices() -> list[tuple[GroupRole, str]]:
    return [
        (GroupRole.MEMBER, _("Member")),
        (GroupRole.MODERATOR, _("Moderator")),
        (GroupRole.SUPER_MODERATOR, _("Super Moderator")),
        (GroupRole.ADMINISTRATOR, _("Administrator")),
        (GroupRole.BANNED, _("Banned")),
        (GroupRole.GUEST, _("Guest")),
    ]


def level_choices() -> list[tuple[PermissionLevel, str]]:
    return [
        (PermissionLevel.ALLOW, _("Allow")),
        (PermissionLevel.DENY, _("Deny")),
        (PermissionLevel.NEVER, _("Never")),
    ]


class GroupForm(FlaskBBForm):
    """The name, description and role of a group. ``group_form`` adds one
    level field per registered permission.
    """

    group: Group | None = None

    name = StringField(
        _("Group name"),
        validators=[DataRequired(message=_("Please enter a name for the group."))],
    )

    description = TextAreaField(_("Description"), validators=[Optional()])

    role = SelectField(
        _("Role"),
        coerce=GroupRole,
        choices=role_choices,
        description=_(
            "Moderators can moderate the forums they are assigned to, super moderators "
            "every forum, and administrators have access to the admin panel. There can "
            "only be one banned and one guest group."
        ),
    )

    submit = SubmitField(_("Save"))

    def permission_fields(self) -> list[Field]:
        return [self[key] for key in permission_registry.keys()]

    def permission_sections(self) -> list[tuple[str, list[Field]]]:
        """The permission fields, grouped the way they were registered."""
        return [
            (group.name, [self[key] for key, _definition in permissions])
            for group, permissions in permission_registry.sections()
        ]

    def validate_name(self, field: Field):
        if self.group is not None:
            group = Group.get(
                sa.and_(
                    Group.name.like(field.data.lower()),
                    sa.not_(Group.id == self.group.id),
                )
            )
        else:
            group = Group.get(Group.name.like(field.data.lower()))

        if group:
            raise ValidationError(_("This group name is already taken."))

    def validate_role(self, field: Field):
        if field.data not in (GroupRole.BANNED, GroupRole.GUEST):
            return

        others = Group.role == field.data
        if self.group is not None:
            others = sa.and_(others, sa.not_(Group.id == self.group.id))

        if Group.count(others) > 0:
            raise ValidationError(
                _("There is already a group of role '%(role)s'.", role=field.data.value)
            )

    @override
    def validate(self, extra_validators: Mapping[str, Sequence[Any]] | None = None):
        if not super().validate(extra_validators):
            return False

        if self.role.data is not GroupRole.GUEST:
            return True

        # guests never get any permissions
        result = True
        for field in self.permission_fields():
            if field.data is PermissionLevel.ALLOW:
                field.errors = [*field.errors, _("Can't assign any permissions to this group.")]
                result = False
        return result

    def save(self) -> Group:
        group = self.group if self.group is not None else Group()
        permission_keys = permission_registry.keys()
        self.populate_obj(group, exclude=["submit", "csrf_token", *permission_keys])
        group.set_permissions({key: self[key].data for key in permission_keys})
        return group.save()


def group_form(group: Group | None = None, **kwargs: Any) -> GroupForm:
    """Builds a group form with a level field per registered permission,
    preset to the permission's default and filled from ``group`` when one is
    being edited.
    """
    fields = {
        key: SelectField(
            _(definition.name),
            description=_(definition.description),
            choices=level_choices,
            coerce=PermissionLevel,
            default=PermissionLevel.of(definition.default),
        )
        for _group, permissions in permission_registry.sections()
        for key, definition in permissions
    }
    form_class = type("GroupPermissionsForm", (GroupForm,), fields)

    if group is not None:
        kwargs.update(obj=group, data=group.permission_levels)
    form = form_class(**kwargs)
    form.group = group
    return form


class ForumForm(FlaskForm):
    forum: Forum | None = None

    title = StringField(
        _("Forum title"),
        validators=[DataRequired(message=_("Please enter a forum title."))],
    )

    description = TextAreaField(
        _("Description"),
        validators=[Optional()],
        description=_("You can format your description with Markdown."),
    )

    position = IntegerField(
        _("Position"),
        default=1,
        validators=[DataRequired(message=_("Please enter a position for theforum."))],
    )

    category = QuerySelectField(
        _("Category"),
        query_factory=selectable_categories,
        allow_blank=False,
        get_label="title",
        description=_("The category that contains this forum."),
    )

    external = StringField(
        _("External link"),
        validators=[Optional(), URL()],
        description=_("A link to a website i.e. 'http://flaskbb.com'."),
    )

    moderators = StringField(
        _("Moderators"),
        description=_(
            "Comma separated usernames. Leave it blank if you do not want to set any moderators."
        ),
    )

    show_moderators = BooleanField(
        _("Show moderators"),
        description=_("Do you want to show the moderators on the index page?"),
    )

    locked = BooleanField(
        _("Locked?"), description=_("Disable new posts and topics in this forum.")
    )

    groups = QuerySelectMultipleField(
        _("Group access"),
        query_factory=selectable_groups,
        get_label="name",
        description=_("Select the groups that can access this forum."),
    )

    submit = SubmitField(_("Save"))

    def validate_external(self, field: Field):
        if self.forum is not None:
            if len(self.forum.topics) > 0:
                raise ValidationError(
                    _("You cannot convert a forum that contains topics into an external link.")
                )

    def validate_show_moderators(self, field: Field):
        if field.data and not self.moderators.data:
            raise ValidationError(_("You also need to specify some moderators."))

    def validate_moderators(self, field: Field):
        approved_moderators: list[User] = []

        if field.data:
            moderators = [mod.strip() for mod in field.data.split(",")]
            users = User.get_all(User.username.in_(moderators))
            for user in users:
                if not Permission(IsAtleastModerator, identity=user):
                    raise ValidationError(
                        _("%(user)s is not in a moderators group.", user=user.username)
                    )
                else:
                    approved_moderators.append(user)
        field.data = approved_moderators

    def save(self):
        data = self.data
        # delete submit and csrf_token from data
        data.pop("submit", None)
        data.pop("csrf_token", None)
        forum = Forum(**data)
        return forum.save(groups=data["groups"])


class EditForumForm(ForumForm):
    id = HiddenField()

    def __init__(self, forum: Forum, *args: Any, **kwargs: Any):
        self.forum = forum
        kwargs["obj"] = self.forum
        ForumForm.__init__(self, *args, **kwargs)

    @override
    def save(self):
        data = self.data
        # delete submit and csrf_token from data
        data.pop("submit", None)
        data.pop("csrf_token", None)
        forum = Forum(**data)
        # flush SQLA info from created instance so that it can be merged
        make_transient(forum)
        make_transient_to_detached(forum)

        return forum.save()


class AddForumForm(ForumForm):
    pass


class CategoryForm(FlaskForm):
    title = StringField(
        _("Category title"),
        validators=[DataRequired(message=_("Please enter a category title."))],
    )

    description = TextAreaField(
        _("Description"),
        validators=[Optional()],
        description=_("You can format your description with Markdown."),
    )

    position = IntegerField(
        _("Position"),
        default=1,
        validators=[DataRequired(message=_("Please enter a position for the category."))],
    )

    submit = SubmitField(_("Save"))

    def save(self):
        data = self.data
        # delete submit and csrf_token from data
        data.pop("submit", None)
        data.pop("csrf_token", None)
        category = Category(**data)
        return category.save()
