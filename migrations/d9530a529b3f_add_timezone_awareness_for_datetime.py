"""add timezone awareness for datetime objects

Revision ID: d9530a529b3f
Revises: 221d918aa9f0
Create Date: 2016-06-21 09:39:38.348519

"""

# revision identifiers, used by Alembic.
revision = 'd9530a529b3f'
down_revision = '221d918aa9f0'

from alembic import op
import sqlalchemy as sa
import flaskbb


def upgrade():
    connection = op.get_bind()

    # Having a hard time with ALTER TABLE/COLUMN stuff in SQLite.. and because DateTime objects are stored as strings anyway,
    # we can simply skip those migrations for SQLite
    if connection.engine.dialect.name != "sqlite":
        # user/models.py
        op.alter_column('users', 'date_joined', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'lastseen', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'birthday', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'last_failed_login', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

        # message/models.py
        op.alter_column('conversations', 'date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('messages', 'date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

        # forum/models.py
        op.alter_column('topicsread', 'last_read', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('forumsread', 'last_read', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('forumsread', 'cleared', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('reports', 'reported', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('reports', 'zapped', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('posts', 'date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('posts', 'date_modified', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('topics', 'date_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('topics', 'last_updated', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('forums', 'last_post_created', existing_type=sa.DateTime(timezone=False), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)


def downgrade():
    connection = op.get_bind()

    if connection.engine.dialect.name != "sqlite":
        # user/models.py
        op.alter_column('users', 'date_joined', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'lastseen', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'birthday', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'last_failed_login', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

        # message/models.py
        op.alter_column('conversations', 'date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('messages', 'date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)

        # forum/models.py
        op.alter_column('topicsread', 'last_read', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('forumsread', 'last_read', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('forumsread', 'cleared', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('reports', 'reported', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('reports', 'zapped', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('posts', 'date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('posts', 'date_modified', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('topics', 'date_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('topics', 'last_updated', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
        op.alter_column('forums', 'last_post_created', type_=sa.DateTime(timezone=False), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
