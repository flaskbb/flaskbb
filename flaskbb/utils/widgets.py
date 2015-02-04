# -*- coding: utf-8 -*-
"""
    flaskbb.utils.widgets
    ~~~~~~~~~~~~~~~~~~~~~

    Additional widgets for wtforms

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from wtforms.widgets.core import Select, HTMLString, html_params


class SelectBirthdayWidget(object):
    """Renders a DateTime field with 3 selects.
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

    def __init__(self, years=range(1930, datetime.utcnow().year + 1)):
        """Initialzes the widget.

        :param years: The min year which should be chooseable.
                      Defatuls to ``1930``.
        """
        super(SelectBirthdayWidget, self).__init__()
        self.FORMAT_CHOICES['%Y'] = [(x, str(x)) for x in years]

    def __call__(self, field, **kwargs):
        field_id = kwargs.pop('id', field.id)
        html = []
        allowed_format = ['%d', '%m', '%Y']
        surrounded_div = kwargs.pop('surrounded_div', None)
        css_class = kwargs.get('class', None)

        for date_format in field.format.split():
            if date_format in allowed_format:
                choices = self.FORMAT_CHOICES[date_format]
                id_suffix = date_format.replace('%', '-')
                id_current = field_id + id_suffix

                if css_class is not None:
                    select_class = "{} {}".format(
                        css_class, self.FORMAT_CLASSES[date_format]
                    )
                else:
                    select_class = self.FORMAT_CLASSES[date_format]

                kwargs['class'] = select_class

                try:
                    del kwargs['placeholder']
                except KeyError:
                    pass

                if surrounded_div is not None:
                    html.append('<div class="%s">' % surrounded_div)

                html.append('<select %s>' % html_params(name=field.name,
                                                        id=id_current,
                                                        **kwargs))

                if field.data:
                    current_value = int(field.data.strftime(date_format))
                else:
                    current_value = None

                for value, label in choices:
                    selected = (value == current_value)

                    # Defaults to blank
                    if value == 1 or value == 1930:
                        html.append(Select.render_option("None", " ", selected))

                    html.append(Select.render_option(value, label, selected))

                html.append('</select>')

                if surrounded_div is not None:
                    html.append("</div>")

            html.append(' ')

        return HTMLString(''.join(html))
