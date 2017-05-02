"""remove timezone info from birthday field

Revision ID: d87cea4e995d
Revises: d9530a529b3f
Create Date: 2016-11-19 09:19:28.000276

"""

# revision identifiers, used by Alembic.
from alembic import op
import sqlalchemy as sa
import flaskbb

revision = 'd87cea4e995d'
down_revision = 'd9530a529b3f'


def upgrade():
    # user/models.py
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('birthday', type_=sa.DateTime(), existing_type=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)


def downgrade():
    # user/models.py
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('birthday', existing_type=sa.DateTime(), type_=flaskbb.utils.database.UTCDateTime(timezone=True), existing_nullable=True)
