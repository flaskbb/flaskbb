"""
    flaskbb.models.permissions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Permission models for flaskbb

    :copyright: 2017, the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""


from flaskbb.extensions import db
from flaskbb.utils.database import primary_key


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = primary_key()
    name = db.Column(db.Unicode(25), nullable=False, unique=True)
    description = db.Column(db.UnicodeText, nullable=True)
    default = db.Column(db.Boolean, default=False, nullable=False)
