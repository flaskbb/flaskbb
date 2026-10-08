"""
flaskbb.permissions.fixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~

FlaskBB's own permission definitions.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from pluggy import HookimplMarker

from .definitions import PermissionDefinition, PermissionGroup

impl = HookimplMarker("flaskbb")


posting_group = PermissionGroup(
    key="posting",
    name="Posting",
    permissions=(
        PermissionDefinition(
            key="editpost",
            name="Can edit posts",
            description="Check this, if the users in this group can edit posts.",
            default=True,
        ),
        PermissionDefinition(
            key="deletepost",
            name="Can delete posts",
            description="Check this, if the users in this group can delete posts.",
        ),
        PermissionDefinition(
            key="deletetopic",
            name="Can delete topics",
            description="Check this, if the users in this group can delete topics.",
        ),
        PermissionDefinition(
            key="posttopic",
            name="Can create topics",
            description="Check this, if the users in this group can create topics.",
            default=True,
        ),
        PermissionDefinition(
            key="postreply",
            name="Can post replies",
            description="Check this, if the users in this group can post replies.",
            default=True,
        ),
        PermissionDefinition(
            key="postattachment",
            name="Can upload attachments",
            description="Check this, if the users in this group can attach files to posts.",
            default=True,
        ),
    ),
)

moderation_group = PermissionGroup(
    key="moderation",
    name="Moderation",
    permissions=(
        PermissionDefinition(
            key="mod_edituser",
            name="Moderators can edit user profiles",
            description=(
                "Allow moderators to edit another user's profile including password "
                "and email changes."
            ),
        ),
        PermissionDefinition(
            key="mod_banuser",
            name="Moderators can ban users",
            description="Allow moderators to ban other users.",
        ),
        PermissionDefinition(
            key="makehidden",
            name="Can hide posts and topics",
            description="Allows a user to hide posts and topics",
        ),
        PermissionDefinition(
            key="viewhidden",
            name="Can view hidden posts and topics",
            description="Allows a user to view hidden posts and topics",
        ),
    ),
)


@impl
def flaskbb_load_internal_permissions():
    return [posting_group, moderation_group]
