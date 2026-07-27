"""Authorization tests for the user management views.

These cover the target-level authorization that ``EditUser``, ``BanUser`` and
``UnbanUser`` apply on top of the actor-level checks in their decorators. The
views are invoked directly rather than over HTTP, which skips the blueprint's
``login_fresh()`` gate - that gate is orthogonal to what is tested here.
"""

import re

import pytest
from flask import g, get_flashed_messages
from flask_login import login_user, logout_user

from flaskbb.forum import views as forum_views
from flaskbb.management import views
from flaskbb.user import views as user_views
from flaskbb.user.models import Group, User


@pytest.fixture
def no_csrf(application):
    previous = application.config.get("WTF_CSRF_ENABLED", True)
    application.config["WTF_CSRF_ENABLED"] = False
    yield
    application.config["WTF_CSRF_ENABLED"] = previous


@pytest.fixture
def plain_group(database):
    """A group that grants no privileges, usable as a secondary group."""
    group = Group(name="Contributors")
    group.save()
    return group


def _edit(user_id, actor, **data):
    view = views.EditUser.as_view("edit_user")
    method = "POST" if data else "GET"

    with views.current_app.test_request_context(method=method, data=data or None):
        login_user(actor)
        response = view(user_id=user_id)
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    return response, messages


def test_moderator_cannot_edit_other_moderator(
    default_settings, no_csrf, moderator_user, other_moderator_user
):
    """The advisory's repro: a moderator of one forum resetting the password of
    a moderator of another forum, to log in as them and inherit their scope.
    """
    response, messages = _edit(
        moderator_user.id,
        other_moderator_user,
        username=moderator_user.username,
        email="attacker-controlled@example.test",
        password="Known-Test-Password-Only",
    )

    assert response.status_code == 302
    assert ("danger", "You are not allowed to edit this user.") in messages
    assert not moderator_user.check_password("Known-Test-Password-Only")
    assert moderator_user.check_password("test")
    assert moderator_user.email == "test_mod@example.org"


def test_moderator_cannot_open_other_moderators_edit_page(
    default_settings, moderator_user, other_moderator_user
):
    response, messages = _edit(moderator_user.id, other_moderator_user)

    assert response.status_code == 302
    assert ("danger", "You are not allowed to edit this user.") in messages


def test_moderator_cannot_edit_admin(default_settings, moderator_user, admin_user):
    response, _messages = _edit(admin_user.id, moderator_user)

    assert response.status_code == 302


def test_moderator_cannot_edit_super_moderator(
    default_settings, moderator_user, super_moderator_user
):
    response, _messages = _edit(super_moderator_user.id, moderator_user)

    assert response.status_code == 302


def test_moderator_cannot_reset_admin_password(
    default_settings, no_csrf, moderator_user, admin_user
):
    response, _messages = _edit(
        admin_user.id,
        moderator_user,
        username=admin_user.username,
        password="Known-Test-Password-Only",
    )

    assert response.status_code == 302
    assert not admin_user.check_password("Known-Test-Password-Only")


def test_moderator_can_still_edit_a_member(default_settings, moderator_user, user):
    """``mod_edituser`` must keep working for ordinary members."""
    response, _messages = _edit(user.id, moderator_user)

    assert "Edit User" in response


def test_member_edit_page_hides_credential_fields_from_moderator(
    default_settings, moderator_user, user
):
    response, _messages = _edit(user.id, moderator_user)

    assert 'name="username"' in response
    assert 'name="signature"' in response
    for field in (
        "email",
        "password",
        "activated",
        "primary_group",
        "secondary_groups",
    ):
        assert 'name="{}"'.format(field) not in response


def test_admin_edit_page_shows_credential_fields(default_settings, admin_user, user):
    response, _messages = _edit(user.id, admin_user)

    for field in (
        "email",
        "password",
        "activated",
        "primary_group",
        "secondary_groups",
    ):
        assert 'name="{}"'.format(field) in response


def test_moderator_editing_member_cannot_change_credentials_or_groups(
    default_settings, no_csrf, moderator_user, user, plain_group, default_groups
):
    user.save(groups=[plain_group])
    original_email = user.email

    response, _messages = _edit(
        user.id,
        moderator_user,
        username=user.username,
        email="attacker-controlled@example.test",
        password="Known-Test-Password-Only",
        primary_group=str(default_groups[2].id),
        secondary_groups=str(default_groups[2].id),
        signature="moderated by a mod",
    )

    assert response.status_code == 302
    # the fields a moderator legitimately owns still apply
    assert user.signature == "moderated by a mod"
    # everything else is ignored, including the secondary groups, which used to
    # be wiped by the unconditional user.save(groups=...)
    assert user.email == original_email
    assert not user.check_password("Known-Test-Password-Only")
    assert user.activated
    assert user.primary_group_id == default_groups[3].id
    assert [group.id for group in user.secondary_groups] == [plain_group.id]


def test_admin_can_still_change_a_moderators_password(
    default_settings, no_csrf, admin_user, moderator_user, default_groups
):
    response, _messages = _edit(
        moderator_user.id,
        admin_user,
        username=moderator_user.username,
        email=moderator_user.email,
        password="New-Admin-Set-Password",
        primary_group=str(default_groups[2].id),
        activated="y",
    )

    assert response.status_code == 302
    assert moderator_user.check_password("New-Admin-Set-Password")


def test_moderator_cannot_ban_super_moderator(
    default_settings, no_csrf, moderator_user, super_moderator_user
):
    view = views.BanUser.as_view("ban_user")

    with views.current_app.test_request_context(method="POST"):
        login_user(moderator_user)
        response = view(user_id=super_moderator_user.id)
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    assert response.status_code == 302
    assert ("danger", "You are not allowed to ban this user.") in messages
    assert not super_moderator_user.permissions["banned"]


def test_moderator_cannot_unban_user_holding_admin_via_secondary_group(
    default_settings, no_csrf, moderator_user, user, default_groups
):
    """``unban()`` drops the target into the member group, so unbanning is a
    demotion and needs the same target check as banning.
    """
    user.save(groups=[default_groups[0]])
    user.ban()
    assert user.permissions["banned"]

    view = views.UnbanUser.as_view("unban_user")

    with views.current_app.test_request_context(method="POST"):
        login_user(moderator_user)
        response = view(user_id=user.id)
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    assert response.status_code == 302
    assert ("danger", "You are not allowed to unban this user.") in messages
    assert user.permissions["banned"]


def _render(view, actor, **kwargs):
    with views.current_app.test_request_context():
        login_user(actor)
        response = view(**kwargs)
        logout_user()

    return response


def _edit_link(target):
    """The href the templates emit - relative, unlike url_for() called outside
    of a request context.
    """
    return '"/admin/users/{}/edit"'.format(target.id)


def test_users_list_renders_for_moderator(
    default_settings, moderator_user, admin_user, user
):
    """Covers the target-aware can_edit_user/can_ban_user filters in
    management/users.html - a signature mismatch there is a template error.
    """
    response = _render(views.ManageUsers.as_view("users"), moderator_user)

    assert user.username in response
    assert admin_user.username in response
    assert _edit_link(user) in response
    assert _edit_link(admin_user) not in response


def test_users_list_renders_for_admin(default_settings, admin_user, moderator_user):
    response = _render(views.ManageUsers.as_view("users"), admin_user)

    assert _edit_link(moderator_user) in response


def test_banned_users_list_renders_for_moderator(
    default_settings, moderator_user, user
):
    """Covers the same filters in management/banned_users.html."""
    user.ban()
    response = _render(views.BannedUsers.as_view("banned_users"), moderator_user)

    assert user.username in response
    assert _edit_link(user) in response


def test_profile_page_renders_for_moderator(
    default_settings, moderator_user, admin_user
):
    """Covers the filters in user/profile_layout.html, which previously linked
    to the edit page for any target.
    """
    response = _render(
        user_views.UserProfile.as_view("profile"),
        moderator_user,
        username=admin_user.username,
    )

    assert admin_user.username in response
    assert _edit_link(admin_user) not in response


def test_topic_page_renders_admin_actions(default_settings, admin_user, topic, user):
    """Covers the target-aware filters in forum/topic.html, whose author
    actions block is only rendered for administrators.
    """
    view = forum_views.ViewTopic.as_view("view_topic")

    with views.current_app.test_request_context():
        # the forum/topic requirements on this view and its templates resolve
        # their subject off of g when it is not in the URL
        g.forum = topic.forum
        g.topic = topic
        login_user(admin_user)
        response = view(topic_id=topic.id)
        logout_user()

    assert user.username in response
    assert _edit_link(user) in response


def test_secondary_groups_exclude_the_targets_primary_group(
    default_settings, admin_user, moderator_user
):
    """User.save() refuses to add the primary group to the secondary groups, so
    the secondary field must not offer it.
    """
    response, _messages = _edit(moderator_user.id, admin_user)

    secondary = re.search(
        r'<select[^>]*name="secondary_groups".*?</select>', response, re.S
    )
    assert secondary is not None
    offered = re.findall(r'value="([^"]*)"', secondary.group(0))

    assert str(moderator_user.primary_group_id) not in offered
    # the other groups are still on offer, and primary_group still lists it
    assert offered
    assert 'value="{}"'.format(moderator_user.primary_group_id) in response


def test_super_moderator_form_hides_credentials_but_keeps_groups(
    default_settings, super_moderator_user, user
):
    response, _messages = _edit(user.id, super_moderator_user)

    for field in ("email", "password", "activated"):
        assert 'name="{}"'.format(field) not in response
    for field in ("primary_group", "secondary_groups"):
        assert 'name="{}"'.format(field) in response


def test_super_moderator_can_promote_a_member_to_moderator(
    default_settings, no_csrf, super_moderator_user, user, default_groups
):
    moderator_group = default_groups[2]

    response, _messages = _edit(
        user.id,
        super_moderator_user,
        username=user.username,
        primary_group=str(moderator_group.id),
    )

    assert response.status_code == 302
    assert user.primary_group_id == moderator_group.id


def test_super_moderator_cannot_assign_the_administrator_group(
    default_settings, no_csrf, super_moderator_user, user, default_groups
):
    """The choice list is the server-side gate - a submitted group that is not
    offered must fail validation rather than be silently applied.
    """
    admin_group = default_groups[0]
    original = user.primary_group_id

    response, _messages = _edit(
        user.id,
        super_moderator_user,
        username=user.username,
        primary_group=str(admin_group.id),
    )

    # re-rendered form, not a redirect
    assert not hasattr(response, "status_code")
    assert user.primary_group_id == original


def test_super_moderator_cannot_assign_the_super_moderator_group(
    default_settings, no_csrf, super_moderator_user, user, default_groups
):
    smod_group = default_groups[1]
    original = user.primary_group_id

    response, _messages = _edit(
        user.id,
        super_moderator_user,
        username=user.username,
        primary_group=str(smod_group.id),
    )

    assert not hasattr(response, "status_code")
    assert user.primary_group_id == original


def test_super_moderator_cannot_smuggle_admin_in_as_a_secondary_group(
    default_settings, no_csrf, super_moderator_user, user, default_groups
):
    """Unlike the single-select, wtforms-sqlalchemy drops an unofferable pk from
    a multi-select instead of rejecting it - its pre_validate reads
    _invalid_formdata before accessing .data is what sets it. The outcome is
    what matters here: no administrator rights are granted either way.
    """
    admin_group = default_groups[0]
    moderator_group = default_groups[2]

    _edit(
        user.id,
        super_moderator_user,
        username=user.username,
        primary_group=str(moderator_group.id),
        secondary_groups=str(admin_group.id),
    )

    assert [group.id for group in user.secondary_groups] == []
    assert not user.permissions["admin"]


def test_super_moderator_cannot_change_a_password(
    default_settings, no_csrf, super_moderator_user, user, default_groups
):
    response, _messages = _edit(
        user.id,
        super_moderator_user,
        username=user.username,
        primary_group=str(default_groups[3].id),
        password="Known-Test-Password-Only",
        email="attacker-controlled@example.test",
    )

    assert response.status_code == 302
    assert not user.check_password("Known-Test-Password-Only")
    assert user.email == "test_normal@example.org"


@pytest.fixture
def second_admin_user(default_groups):
    """A second administrator, so admin-on-admin edits stay testable."""
    admin = User(
        username="test_admin_two",
        email="test_admin_two@example.org",
        password="test",
        primary_group=default_groups[0],
        activated=True,
    )
    admin.save()
    return admin


def test_self_edit_form_drops_group_and_activation_fields(default_settings, admin_user):
    response, _messages = _edit(admin_user.id, admin_user)

    # self service is fine
    for field in ("username", "email", "password"):
        assert 'name="{}"'.format(field) in response
    # lockout vectors are not
    for field in ("primary_group", "secondary_groups", "activated"):
        assert 'name="{}"'.format(field) not in response


def test_admin_cannot_ban_themselves_via_the_edit_form(
    default_settings, no_csrf, admin_user, default_groups
):
    response, _messages = _edit(
        admin_user.id,
        admin_user,
        username=admin_user.username,
        email=admin_user.email,
        primary_group=str(default_groups[4].id),
    )

    assert response.status_code == 302
    assert not admin_user.permissions["banned"]
    assert admin_user.permissions["admin"]


def test_admin_cannot_demote_themselves_via_the_edit_form(
    default_settings, no_csrf, admin_user, default_groups
):
    response, _messages = _edit(
        admin_user.id,
        admin_user,
        username=admin_user.username,
        email=admin_user.email,
        primary_group=str(default_groups[3].id),
    )

    assert response.status_code == 302
    assert admin_user.primary_group_id == default_groups[0].id
    assert admin_user.permissions["admin"]


def test_admin_cannot_deactivate_themselves_via_the_edit_form(
    default_settings, no_csrf, admin_user
):
    """A BooleanField absent from the POST reads as False, so submitting the
    form without ticking "Is active?" used to deactivate the account.
    """
    response, _messages = _edit(
        admin_user.id,
        admin_user,
        username=admin_user.username,
        email=admin_user.email,
    )

    assert response.status_code == 302
    assert admin_user.activated


def test_admin_can_still_change_their_own_password(
    default_settings, no_csrf, admin_user
):
    response, _messages = _edit(
        admin_user.id,
        admin_user,
        username=admin_user.username,
        email=admin_user.email,
        password="New-Self-Set-Password",
    )

    assert response.status_code == 302
    assert admin_user.check_password("New-Self-Set-Password")


def test_the_self_restriction_does_not_apply_to_other_admins(
    default_settings, no_csrf, admin_user, second_admin_user, default_groups
):
    """Only the acting user's own account is protected - an administrator can
    still demote a different administrator.
    """
    response, _messages = _edit(
        second_admin_user.id,
        admin_user,
        username=second_admin_user.username,
        email=second_admin_user.email,
        primary_group=str(default_groups[3].id),
        activated="y",
    )

    assert response.status_code == 302
    assert second_admin_user.primary_group_id == default_groups[3].id
