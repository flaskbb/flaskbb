import sqlalchemy as sa
from flaskbb.extensions import db
from flaskbb.utils.database import drop_all


def test_sqlite_enforces_foreign_keys(database):
    assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar() == 1


def test_drop_all_leaves_foreign_keys_enforced(application):
    """The drop has to suspend enforcement to get around the cyclic foreign
    keys, and the connection it borrows goes back to the pool afterwards.
    """
    db.create_all()

    drop_all()

    assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar() == 1


def test_drop_all_drops_the_tables_outside_the_metadata(database):
    db.session.execute(db.text("CREATE TABLE leftover (id INTEGER PRIMARY KEY)"))
    db.session.execute(
        db.text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
    )
    db.session.commit()

    drop_all()

    assert sa.inspect(db.engine).get_table_names() == []


def test_drop_all_drops_virtual_tables_with_their_shadow_tables(database):
    db.session.execute(
        db.text("CREATE VIRTUAL TABLE posts_fts USING fts5(content, content='posts')")
    )
    db.session.commit()

    drop_all()

    assert sa.inspect(db.engine).get_table_names() == []
