# -*- coding: utf-8 -*-
"""
    flaskbb.utils.fields
    ~~~~~~~~~~~~~~~~~~~~

    Additional fields for wtforms

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from wtforms.fields import DateField


class BirthdayField(DateField):
    """Same as DateField, except it allows ``None`` values in case a user
    wants to delete his birthday.
    """
    def __init__(self, label=None, validators=None, format='%Y-%m-%d', **kwargs):
        super(DateField, self).__init__(label, validators, format, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                self.data = datetime.strptime(date_str, self.format).date()
            except ValueError:
                self.data = None

                # Only except the None value if all values are None.
                # A bit dirty though
                if valuelist != ["None", "None", "None"]:
                    raise ValueError("Not a valid date value")
