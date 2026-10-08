from flaskbb.management.forms import group_form
from flaskbb.permissions import (
    permission_registry,
    PermissionDefinition,
    PermissionGroup,
    PermissionLevel,
)
from flaskbb.user.models import Group, GroupRole

MODERATOR, MEMBER = 2, 3


def _posted(application, **data):
    with application.test_request_context(method="POST", data=data):
        form = group_form(meta={"csrf": False})
        valid = form.validate()
        return form, valid


def test_form_is_filled_from_the_group(application, default_groups):
    with application.test_request_context():
        form = group_form(default_groups[MODERATOR])

    assert form.name.data == "Moderator"
    assert form.role.data is GroupRole.MODERATOR
    assert form["mod_banuser"].data is PermissionLevel.ALLOW
    assert form["makehidden"].data is PermissionLevel.DENY


def test_form_saves_role_and_permissions(application, default_groups):
    form, valid = _posted(
        application, name="VIP", description="Trusted", role="mod", viewhidden="allow"
    )
    assert valid

    with application.test_request_context():
        group = form.save()

    assert group.role is GroupRole.MODERATOR
    assert group.permissions["viewhidden"] is True
    assert group.permissions["makehidden"] is False
    # a permission that was not posted keeps the default of its definition
    assert group.permission_levels["editpost"] is PermissionLevel.ALLOW
    assert group.permission_levels["makehidden"] is PermissionLevel.DENY


def test_new_form_presets_the_defaults(application, default_groups):
    with application.test_request_context():
        form = group_form()

    assert form["editpost"].data is PermissionLevel.ALLOW
    assert form["makehidden"].data is PermissionLevel.DENY


def test_form_saves_never(application, default_groups):
    form, valid = _posted(application, name="Probation", role="member", deletepost="never")
    assert valid

    with application.test_request_context():
        group = form.save()

    assert group.permission_levels["deletepost"] is PermissionLevel.NEVER
    assert group.permissions["deletepost"] is False


def test_form_rejects_an_unknown_level(application, default_groups):
    form, valid = _posted(application, name="VIP", role="member", deletepost="maybe")

    assert not valid
    assert form["deletepost"].errors


def test_form_updates_an_existing_group(application, default_groups):
    member = default_groups[MEMBER]
    with application.test_request_context(
        method="POST", data={"name": "Members", "role": "member", "deletepost": "allow"}
    ):
        form = group_form(member, meta={"csrf": False})
        assert form.validate()
        form.save()

    assert member.name == "Members"
    assert member.permissions["deletepost"] is True
    # a permission that was not posted keeps what the group had
    assert member.permissions["editpost"] is True


def test_guest_group_gets_no_permissions(application, default_groups):
    with application.test_request_context(
        method="POST", data={"name": "Guest", "role": "guest", "editpost": "allow"}
    ):
        form = group_form(default_groups[5], meta={"csrf": False})
        assert not form.validate()

    assert "Can't assign any permissions to this group." in form["editpost"].errors


def test_second_banned_group_is_rejected(application, default_groups):
    form, valid = _posted(application, name="Jail", role="banned")

    assert not valid
    assert "There is already a group of role 'banned'." in form.role.errors
    assert Group.count() == len(default_groups)


def test_plugin_permissions_get_their_own_section(application, default_groups):
    permission_registry.register_group(
        PermissionGroup(
            key="myplugin",
            name="My Plugin",
            permissions=(
                PermissionDefinition(key="do_things", name="Can do things", description=""),
            ),
        ),
        is_plugin=True,
    )
    try:
        with application.test_request_context():
            form = group_form()
        sections = {
            name: [field.name for field in fields] for name, fields in form.permission_sections()
        }
    finally:
        permission_registry.unregister_group("myplugin")

    assert sections["My Plugin"] == ["myplugin_do_things"]
