import pytest
from flaskbb.management.forms import AddForumForm, AddUserForm, EditUserForm
from werkzeug.datastructures import MultiDict
from wtforms.validators import ValidationError


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


def _user_form(form_class, *args, **data):
    return form_class(*args, formdata=MultiDict(data), meta={"csrf": False})


@pytest.mark.parametrize("username", ["fred", "FRED", "fReD"])
def test_user_form_rejects_username_differing_only_by_case(Fred, username):
    form = _user_form(AddUserForm, username=username)

    with pytest.raises(ValidationError):
        form.validate_username(form.username)


@pytest.mark.parametrize("email", ["FRED@FRED.FRED", "Fred@fred.fred"])
def test_user_form_rejects_email_differing_only_by_case(Fred, email):
    form = _user_form(AddUserForm, email=email)

    with pytest.raises(ValidationError):
        form.validate_email(form.email)


def test_user_form_does_not_treat_input_as_like_pattern(Fred):
    form = _user_form(AddUserForm, username="Fre_", email="fre_@fred.fred")

    form.validate_username(form.username)
    form.validate_email(form.email)


def test_edit_user_form_allows_recasing_the_own_username(Fred):
    form = _user_form(EditUserForm, Fred, username="FRED", email="FRED@FRED.FRED")

    form.validate_username(form.username)
    form.validate_email(form.email)


def test_edit_user_form_rejects_case_variant_of_another_user(Fred, user):
    form = _user_form(EditUserForm, user, username="FRED", email="FRED@FRED.FRED")

    with pytest.raises(ValidationError):
        form.validate_username(form.username)
    with pytest.raises(ValidationError):
        form.validate_email(form.email)
