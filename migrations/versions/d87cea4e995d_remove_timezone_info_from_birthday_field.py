"""remove timezone info from birthday field

Revision ID: d87cea4e995d
Revises: d9530a529b3f
Create Date: 2016-11-19 09:19:28.000276

"""

# revision identifiers, used by Alembic.
revision = 'd87cea4e995d'
down_revision = 'd9530a529b3f'

from alembic import op
import sqlalchemy as sa
import flaskbb


def upgrade():
    connection = op.get_bind()

    if connection.engine.dialect.name != "sqlite":
        # user/models.py
        op.alter_column('users', 'birthday', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)


def downgrade():
    connection = op.get_bind()

    if connection.engine.dialect.name != "sqlite":
        # user/models.py
        op.alter_column('users', 'birthday', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
