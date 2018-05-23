# -*- coding: utf-8 -*-
"""
    flaskbb
    ~~~~~~~

    FlaskBB is a forum software written in python using the
    microframework Flask.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
__version__ = "2.0.0"

import logging
logger = logging.getLogger(__name__)

from flaskbb.app import create_app  # noqa


# monkeypatch for https://github.com/wtforms/wtforms/issues/373 Taken from
# https://github.com/indico/indico/commit/c79c562866e5efdbeb5a3101cccc97df57906f76
def _patch_wtforms_sqlalchemy():
    from ._compat import text_type
    from wtforms.ext.sqlalchemy import fields
    from sqlalchemy.orm.util import identity_key

    def get_pk_from_identity(obj):
        key = identity_key(instance=obj)[1]
        return u':'.join(map(text_type, key))

    fields.get_pk_from_identity = get_pk_from_identity


_patch_wtforms_sqlalchemy()
del _patch_wtforms_sqlalchemy
