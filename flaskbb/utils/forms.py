"""
flaskbb.utils.forms
~~~~~~~~~~~~~~~~~~~

This module contains stuff for forms.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Iterable
from typing import override

from flask_wtf import FlaskForm


class FlaskBBForm(FlaskForm):
    @override
    def populate_obj(self, obj, exclude: Iterable[str] | None = None):
        """Populates the attributes of the passed `obj` with data from the
        form's fields, skipping any field names listed in `exclude`.

        :param obj: The object to populate.
        :param exclude: An iterable of field names to skip.
        """
        exclude = exclude or ()
        for name, field in self._fields.items():
            if name not in exclude:
                field.populate_obj(obj, name)

    def populate_errors(self, errors: list[tuple[str, str]]):
        for attribute, reason in errors:
            self.errors.setdefault(attribute, []).append(reason)  # pyright: ignore
            field = getattr(self, attribute, None)
            if field:
                field.errors.append(reason)

    def disable_all(self):
        for field in self:
            # Preserve existing render_kw attributes if any exist
            if field.render_kw is None:
                field.render_kw = {}
            field.render_kw["disabled"] = "disabled"
