"""Permissions are declared in a registry that FlaskBB and plugins fill,
and stored per group as rows that fall back to the definition's default.
"""

import pytest
from flaskbb.permissions import permission_registry, PermissionDefinition, PermissionGroup
from flaskbb.utils import requirements as r

MEMBER = 3


@pytest.fixture
def plugin_permissions():
    group = PermissionGroup(
        key="myplugin",
        name="My Plugin",
        permissions=(
            PermissionDefinition(
                key="do_things",
                name="Can do things",
                description="Allows doing things.",
                default=True,
            ),
        ),
    )
    permission_registry.register_group(group, is_plugin=True)
    yield group
    permission_registry.unregister_group(group.key)


def test_core_permissions_are_registered_unprefixed():
    assert permission_registry.is_registered("editpost")
    assert permission_registry.definition("editpost").default is True
    assert permission_registry.definition("makehidden").default is False


def test_plugin_permissions_are_prefixed_with_the_plugin_name(plugin_permissions):
    assert permission_registry.is_registered("myplugin_do_things")
    assert not permission_registry.is_registered("do_things")
    assert permission_registry.keys()[-1] == "myplugin_do_things"


def test_plugin_section_lists_the_prefixed_keys(plugin_permissions):
    sections = dict(
        (group.name, [key for key, _definition in permissions])
        for group, permissions in permission_registry.sections()
    )
    assert sections["My Plugin"] == ["myplugin_do_things"]
    assert "editpost" in sections["Posting"]


def test_duplicate_group_is_rejected(plugin_permissions):
    with pytest.raises(ValueError, match="Duplicate permission group"):
        permission_registry.register_group(plugin_permissions, is_plugin=True)


def test_duplicate_permission_key_is_rejected():
    clash = PermissionGroup(
        key="clash",
        name="Clash",
        permissions=(PermissionDefinition(key="editpost", name="Clash", description=""),),
    )
    with pytest.raises(ValueError, match="Duplicate permission: editpost"):
        permission_registry.register_group(clash)
    assert "clash" not in [group.key for group, _permissions in permission_registry.sections()]


def test_unregistering_a_group_forgets_its_permissions(plugin_permissions):
    permission_registry.unregister_group("myplugin")
    assert not permission_registry.is_registered("myplugin_do_things")
    permission_registry.register_group(plugin_permissions, is_plugin=True)


def test_group_without_a_decision_gets_the_default(plugin_permissions, default_groups):
    assert default_groups[MEMBER].permissions["myplugin_do_things"] is True


def test_plugin_permission_reaches_the_requirements(plugin_permissions, user, default_groups):
    assert r.Has("myplugin_do_things")(user)

    default_groups[MEMBER].set_permission("myplugin_do_things", False)
    default_groups[MEMBER].save()

    assert not r.Has("myplugin_do_things")(user)
    assert user.permissions["myplugin_do_things"] is False


def test_a_decision_is_stored_once_per_permission(default_groups):
    group = default_groups[MEMBER]
    group.set_permission("deletepost", True)
    group.set_permission("deletepost", False)
    group.save()

    rows = [row for row in group.permission_rows if row.permission == "deletepost"]
    assert len(rows) == 1
    assert group.permissions["deletepost"] is False
