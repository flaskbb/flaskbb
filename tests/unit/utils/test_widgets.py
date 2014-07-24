"""Tests for the utils/widgets.py file."""
import datetime
from flaskbb.utils.widgets import SelectDateWidget

def test_select_date_widget():
    """Test the SelectDateWidget."""
    assert SelectDateWidget.FORMAT_CHOICES['%d'] == [(x, str(x)) for x in range(1, 32)]
    assert SelectDateWidget.FORMAT_CHOICES['%m'] == [(x, str(x)) for x in range(1, 13)]

    assert SelectDateWidget.FORMAT_CLASSES == {
        '%d': 'select_date_day',
        '%m': 'select_date_month',
        '%Y': 'select_date_year'
    }

    select_date_widget = SelectDateWidget(years=[0, 1])

    assert select_date_widget.FORMAT_CHOICES['%Y'] == [(0, '0'), (1, '1')]

    class Field(object):
        id = 'world'
        name = 'helloWorld'
        format = '%d %m %Y'
        data = None

    html = select_date_widget(field=Field())
    assert 'world' in html
    assert 'helloWorld' in html
    assert 'class="select_date_day"' in html
    assert 'class="select_date_month"' in html
    assert 'class="select_date_year"' in html




