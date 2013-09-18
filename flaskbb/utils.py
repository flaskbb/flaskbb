# -*- coding: utf-8 -*-
"""
    flaskbb.utils
    ~~~~~~~~~~~~~~~~~~~~

    A few utils that are used by flaskbb

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import random
from datetime import datetime

from wtforms.widgets.core import Select, HTMLString, html_params


def generate_random_pass(length=8):
    return "".join(chr(random.randint(33, 126)) for i in range(length))


def time_delta_format(dt, default=None):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    Ref: https://bitbucket.org/danjac/newsmeme/src/a281babb9ca3/newsmeme/
    """

    if default is None:
        default = 'just now'

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, 'year', 'years'),
        (diff.days / 30, 'month', 'months'),
        (diff.days / 7, 'week', 'weeks'),
        (diff.days, 'day', 'days'),
        (diff.seconds / 3600, 'hour', 'hours'),
        (diff.seconds / 60, 'minute', 'minutes'),
        (diff.seconds, 'second', 'seconds'),
    )

    for period, singular, plural in periods:

        if not period:
            continue

        if period == 1:
            return u'%d %s ago' % (period, singular)
        else:
            return u'%d %s ago' % (period, plural)

    return default


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
