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
