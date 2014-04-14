from flaskbb.utils.populate import create_default_groups, GROUPS
from flaskbb.user.models import Group


def test_create_default_groups(database):
    """Test that the default groups are created correctly."""

    assert Group.query.count() == 0

    create_default_groups()

    assert Group.query.count() == len(GROUPS)

    for key, attributes in GROUPS.items():
        group = Group.query.filter_by(name=key).first()

        for attribute, value in attributes.items():
            assert getattr(group, attribute) == value
