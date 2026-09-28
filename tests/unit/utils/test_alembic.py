import logging

import pytest
from flaskbb.extensions import alembic, db


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
