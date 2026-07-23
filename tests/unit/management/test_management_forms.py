from werkzeug.datastructures import MultiDict

from flaskbb.management.forms import AddForumForm


def _form(category, groups=None):
    data = {
        "title": "Restricted Forum",
        "position": "1",
        "category": str(category.id),
    }
    if groups is not None:
        data["groups"] = [str(g.id) for g in groups]
    return AddForumForm(
        formdata=MultiDict(data),
        meta={"csrf": False},
    )


def test_add_forum_form_restricts_to_selected_groups(
    database, category, default_groups, default_settings
):
    """Regression test: Forum.save() used to silently discard an
    explicit `groups` selection and fall back to granting every group
    access, because it only checked `groups is None` to decide whether
    to apply the "all groups" default, without ever assigning the
    passed-in value otherwise.
    """
    form = _form(category, groups=[default_groups[0]])
    assert form.validate(), form.errors

    forum = form.save()

    assert [g.id for g in forum.groups] == [default_groups[0].id]


def test_add_forum_form_with_no_groups_selected_grants_no_access(
    database, category, default_groups, default_settings
):
    """An explicit, empty group selection must result in a forum with no
    groups - distinct from omitting `groups` entirely, which defaults to
    every group (see Forum.save()).
    """
    form = _form(category, groups=[])
    assert form.validate(), form.errors

    forum = form.save()

    assert forum.groups == []
