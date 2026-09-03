from flaskbb.cli.groups import delete_group, list_groups, new_group, show_group, update_group
from flaskbb.extensions import db
from flaskbb.user.models import Group


def _get_group(name):
    return db.session.execute(db.select(Group).filter_by(name=name)).scalar_one()


def test_list_groups(cli_runner, default_groups):
    result = cli_runner.invoke(list_groups, [])

    assert result.exit_code == 0
    for group in default_groups:
        assert group.name in result.output


def test_list_groups_counts_the_members(cli_runner, user, default_groups):
    user.add_to_group(default_groups[2])
    user.save()

    result = cli_runner.invoke(list_groups, [])

    assert result.exit_code == 0
    # the member group (primary) and the moderator group (secondary)
    assert "Moderator        mod        1" in result.output
    assert "Member           member     1" in result.output


def test_show_group(cli_runner, default_groups):
    result = cli_runner.invoke(show_group, ["moderator"])

    assert result.exit_code == 0
    assert "The Moderator Group" in result.output
    assert "[+] mod_banuser" in result.output
    assert "[-] makehidden" in result.output


def test_new_group(cli_runner, default_groups):
    result = cli_runner.invoke(
        new_group,
        ["VIP", "--description", "Trusted", "--grant", "viewhidden", "--revoke", "editpost"],
    )

    assert result.exit_code == 0

    group = _get_group("VIP")
    assert group.description == "Trusted"
    assert group.viewhidden
    assert not group.editpost
    # untouched permissions keep the default of the model
    assert group.postreply
    assert not group.makehidden


def test_new_group_with_type(cli_runner, default_groups):
    result = cli_runner.invoke(new_group, ["Junior Mods", "--type", "mod"])

    assert result.exit_code == 0

    group = _get_group("Junior Mods")
    assert group.mod
    assert not group.admin


def test_new_group_with_taken_name(cli_runner, default_groups):
    result = cli_runner.invoke(new_group, ["Member"])

    assert result.exit_code != 0
    assert "already taken" in result.stderr


def test_new_group_with_unknown_permission(cli_runner, default_groups):
    result = cli_runner.invoke(new_group, ["VIP", "--grant", "flyaround"])

    assert result.exit_code != 0
    assert "Unknown permission(s): flyaround" in result.stderr
    assert Group.count() == len(default_groups)


def test_new_group_granting_and_revoking_the_same_permission(cli_runner, default_groups):
    result = cli_runner.invoke(new_group, ["VIP", "--grant", "editpost", "--revoke", "editpost"])

    assert result.exit_code != 0
    assert "Can't grant and revoke" in result.stderr


def test_new_group_with_a_second_guest_type(cli_runner, default_groups):
    result = cli_runner.invoke(new_group, ["Visitors", "--type", "guest"])

    assert result.exit_code != 0
    assert "Only one group of type 'guest'" in result.stderr


def test_update_group(cli_runner, default_groups):
    result = cli_runner.invoke(
        update_group,
        ["Member", "--name", "Members", "--grant", "deletepost", "--revoke", "editpost"],
    )

    assert result.exit_code == 0

    group = _get_group("Members")
    assert group.deletepost
    assert not group.editpost


def test_update_group_type(cli_runner, default_groups):
    result = cli_runner.invoke(update_group, ["Moderator", "--type", "member"])

    assert result.exit_code == 0

    group = _get_group("Moderator")
    assert not group.mod
    assert not group.admin


def test_update_group_leaves_omitted_options_alone(cli_runner, default_groups):
    result = cli_runner.invoke(update_group, ["Member", "--grant", "makehidden"])

    assert result.exit_code == 0

    group = _get_group("Member")
    assert group.description == "The Member Group"
    assert group.makehidden
    assert group.editpost


def test_update_unknown_group(cli_runner, default_groups):
    result = cli_runner.invoke(update_group, ["Nobodies", "--grant", "editpost"])

    assert result.exit_code != 0
    assert "does not exist" in result.stderr


def test_delete_group(cli_runner, default_groups):
    cli_runner.invoke(new_group, ["VIP"])

    result = cli_runner.invoke(delete_group, ["VIP", "--force"])

    assert result.exit_code == 0
    assert Group.count() == len(default_groups)


def test_delete_group_asks_for_confirmation(cli_runner, default_groups):
    cli_runner.invoke(new_group, ["VIP"])

    result = cli_runner.invoke(delete_group, ["VIP"], input="n\n")

    assert result.exit_code == 0
    assert Group.count() == len(default_groups) + 1


def test_delete_standard_group(cli_runner, default_groups):
    result = cli_runner.invoke(delete_group, ["Member", "--force"])

    assert result.exit_code != 0
    assert "can't be deleted" in result.stderr


def test_delete_group_with_members(cli_runner, user, default_groups):
    cli_runner.invoke(new_group, ["VIP"])
    user.add_to_group(_get_group("VIP"))
    user.save()

    result = cli_runner.invoke(delete_group, ["VIP", "--force"])

    assert result.exit_code != 0
    assert "still has 1 member(s)" in result.stderr
