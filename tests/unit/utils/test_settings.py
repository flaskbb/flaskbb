import sqlalchemy as sa
from flaskbb.extensions import db
from flaskbb.settings.models import Setting
from flaskbb.settings.proxy import FlaskBBConfigProxy


def test_setting_keys_are_unique_per_group(database):
    db.session.add_all(
        [
            Setting(key="enabled", value="true", group_key="portal"),
            Setting(key="enabled", value="false", group_key="conversations"),
        ]
    )
    db.session.commit()

    group_keys = db.session.execute(
        sa.select(Setting.group_key).where(Setting.key == "enabled")
    ).scalars()

    assert sorted(group_keys) == ["conversations", "portal"]


def test_flaskbb_config(default_settings):
    flaskbb_config = FlaskBBConfigProxy()

    assert len(flaskbb_config) > 0
    # test __getitem__
    assert flaskbb_config["PROJECT_TITLE"] == "FlaskBB"
    # test __setitem__
    flaskbb_config["PROJECT_TITLE"] = "FlaskBBTest"
    assert flaskbb_config["PROJECT_TITLE"] == "FlaskBBTest"
    # test __iter__
    assert "PROJECT_TITLE" in list(flaskbb_config.__iter__())
