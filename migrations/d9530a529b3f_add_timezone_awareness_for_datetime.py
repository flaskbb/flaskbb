"""add timezone awareness for datetime objects

Revision ID: d9530a529b3f
Revises: 221d918aa9f0
Create Date: 2016-06-21 09:39:38.348519

"""
from alembic import op
import sqlalchemy as sa
import flaskbb

# revision identifiers, used by Alembic.
revision = 'd9530a529b3f'
down_revision = '221d918aa9f0'


def upgrade():
    # batch_alter_table will only use the 'recreate' style on SQLite!

    # user/models.py
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('date_joined', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('lastseen', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('birthday', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('last_failed_login', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

    # message/models.py
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.alter_column('date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

    # forum/models.py
    with op.batch_alter_table('topicsread') as batch_op:
        batch_op.alter_column('last_read', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('forumsread') as batch_op:
        batch_op.alter_column('last_read', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('cleared', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('reports') as batch_op:
        batch_op.alter_column('reported', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('zapped', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('posts') as batch_op:
        batch_op.alter_column('date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('date_modified', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('topics') as batch_op:
        batch_op.alter_column('date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('last_updated', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('forums') as batch_op:
        batch_op.alter_column('last_post_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)


def downgrade():

        # user/models.py
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('date_joined', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('lastseen', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('birthday', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('last_failed_login', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

        # message/models.py
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.alter_column('date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

        # forum/models.py
    with op.batch_alter_table('topicsread') as batch_op:
        batch_op.alter_column('last_read', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('forumsread') as batch_op:
        batch_op.alter_column('last_read', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('cleared', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('reports') as batch_op:
        batch_op.alter_column('reported', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('zapped', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('posts') as batch_op:
        batch_op.alter_column('date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('date_modified', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('topics') as batch_op:
        batch_op.alter_column('date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        batch_op.alter_column('last_updated', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
    with op.batch_alter_table('forums') as batch_op:
        batch_op.alter_column('last_post_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
