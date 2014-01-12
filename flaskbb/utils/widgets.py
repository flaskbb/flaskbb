# -*- coding: utf-8 -*-
"""
    flaskbb.utils.wtforms
    ~~~~~~~~~~~~~~~~~~~~

    Additional widgets for wtforms

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from wtforms.widgets.core import Select, HTMLString, html_params


class SelectDateWidget(object):
    """
    Renders a DateTime field with 3 selects.
    For more information see: http://stackoverflow.com/a/14664504
    """
    FORMAT_CHOICES = {
        '%d': [(x, str(x)) for x in range(1, 32)],
        '%m': [(x, str(x)) for x in range(1, 13)]
    }

    FORMAT_CLASSES = {
        '%d': 'select_date_day',
        '%m': 'select_date_month',
        '%Y': 'select_date_year'
    }

    def __init__(self, years=range(1930, datetime.utcnow().year+1)):
        super(SelectDateWidget, self).__init__()
        self.FORMAT_CHOICES['%Y'] = [(x, str(x)) for x in years]

    def __call__(self, field, **kwargs):
        field_id = kwargs.pop('id', field.id)
        html = []
        allowed_format = ['%d', '%m', '%Y']

        for format in field.format.split():
            if (format in allowed_format):
                choices = self.FORMAT_CHOICES[format]
                id_suffix = format.replace('%', '-')
                id_current = field_id + id_suffix

                kwargs['class'] = self.FORMAT_CLASSES[format]
                try:
                    del kwargs['placeholder']
                except:
                    pass

                html.append('<select %s>' % html_params(name=field.name,
                                                        id=id_current,
                                                        **kwargs))

                if field.data:
                    current_value = int(field.data.strftime(format))
                else:
                    current_value = None

                for value, label in choices:
                    selected = (value == current_value)
                    html.append(Select.render_option(value, label, selected))
                html.append('</select>')
            else:
                html.append(format)
                html.append(
                    """<input type="hidden" value="{}" {}></input>""".format(
                        html_params(name=field.name, id=id_current, **kwargs)))

            html.append(' ')

        return HTMLString(''.join(html))
