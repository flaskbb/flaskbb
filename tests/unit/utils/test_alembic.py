import logging

import pytest
from alembic.util.exc import CommandError
from flaskbb.extensions import alembic, db
from flaskbb.plugins.models import PluginRegistry


def _no_migrations(revision, context):
    return []


@pytest.fixture()
def version_table(database):
    yield
    db.session.execute(db.text("DROP TABLE IF EXISTS alembic_version"))
    db.session.commit()


@pytest.fixture()
def orphaned_row(version_table):
    db.session.execute(db.text("PRAGMA foreign_keys=OFF"))
    db.session.execute(db.text("INSERT INTO topictracker (user_id, topic_id) VALUES (999, 999)"))
    db.session.commit()
    db.session.execute(db.text("PRAGMA foreign_keys=ON"))
    yield
    db.session.rollback()
    db.session.execute(db.text("DELETE FROM topictracker"))
    db.session.commit()
    db.session.execute(db.text("PRAGMA foreign_keys=ON"))


def _flaskbb_head():
    return next(
        script.revision
        for script in alembic.script_directory.get_revisions("heads")
        if "default" in script.branch_labels
    )


@pytest.fixture()
def unknown_revision(version_table):
    alembic.run_migrations(_no_migrations)
    db.session.execute(db.text("INSERT INTO alembic_version (version_num) VALUES ('deadbeef0001')"))
    db.session.commit()


@pytest.fixture()
def unknown_plugin_revision(unknown_revision):
    db.session.execute(
        db.text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": _flaskbb_head()},
    )
    db.session.commit()


def test_migrations_run_with_sqlite_foreign_keys_suspended(version_table):
    enforced = []

    def record_foreign_keys(revision, context):
        enforced.append(context.connection.exec_driver_sql("PRAGMA foreign_keys").scalar())
        return []

    alembic.run_migrations(record_foreign_keys)

    assert enforced == [0]
    assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar() == 1


def test_migrations_warn_about_foreign_key_violations(orphaned_row, caplog):
    with caplog.at_level(logging.WARNING, logger="flaskbb.utils.alembic"):
        alembic.run_migrations(_no_migrations)

    assert "topictracker row 1 references a missing row in users" in caplog.text
    assert "topictracker row 1 references a missing row in topics" in caplog.text


def test_migrations_name_the_registered_plugins_that_are_not_installed(unknown_revision):
    PluginRegistry("removed_plugin").save()

    with pytest.raises(CommandError, match="registered but not installed: removed_plugin") as exc:
        alembic.run_migrations(_no_migrations)

    assert "deadbeef0001" in str(exc.value)


def test_migrations_reject_unknown_revisions_without_a_missing_plugin(unknown_revision):
    with pytest.raises(CommandError, match="no installed package provides: deadbeef0001") as exc:
        alembic.run_migrations(_no_migrations)

    assert "newer version of FlaskBB" in str(exc.value)
    assert "--skip-missing" not in str(exc.value)


def test_migrations_suggest_skipping_the_revisions_of_plugins(unknown_plugin_revision):
    with pytest.raises(CommandError, match="no installed package provides: deadbeef0001") as exc:
        alembic.run_migrations(_no_migrations)

    assert "newer version of FlaskBB" not in str(exc.value)
    assert "run 'flaskbb db upgrade --skip-missing'" in str(exc.value)


def test_migrations_skip_unknown_revisions_and_keep_their_rows(unknown_plugin_revision, caplog):
    seen = []

    def record_revisions(revision, context):
        seen.append(revision)
        return []

    with caplog.at_level(logging.WARNING, logger="flaskbb.utils.alembic"):
        alembic.run_migrations(record_revisions, skip_missing=True)

    assert seen == [(_flaskbb_head(),)]
    rows = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalars()
    assert set(rows) == {_flaskbb_head(), "deadbeef0001"}
    assert "Skipping the unknown revisions deadbeef0001" in caplog.text


def test_migrations_refuse_to_skip_without_a_revision_of_flaskbb(unknown_revision):
    with pytest.raises(CommandError, match="Can't skip deadbeef0001"):
        alembic.run_migrations(_no_migrations, skip_missing=True)


@pytest.mark.parametrize("target", ["heads", "portal@head", "+1"])
def test_upgrade_skips_missing_revisions_for_every_target(monkeypatch, target):
    calls = []
    monkeypatch.setattr(
        alembic, "run_migrations", lambda fn, skip_missing: calls.append(skip_missing)
    )

    alembic.upgrade(target, skip_missing=True)

    assert calls == [True]
