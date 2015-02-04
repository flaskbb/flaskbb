"""Tests for the utils/widgets.py file."""
from flaskbb.utils.widgets import SelectBirthdayWidget


def test_select_birthday_widget():
    """Test the SelectDateWidget."""

    assert SelectBirthdayWidget.FORMAT_CHOICES['%d'] == [
        (x, str(x)) for x in range(1, 32)
    ]
    assert SelectBirthdayWidget.FORMAT_CHOICES['%m'] == [
        (x, str(x)) for x in range(1, 13)
    ]

    assert SelectBirthdayWidget.FORMAT_CLASSES == {
        '%d': 'select_date_day',
        '%m': 'select_date_month',
        '%Y': 'select_date_year'
    }

    select_birthday_widget = SelectBirthdayWidget(years=[0, 1])

    assert select_birthday_widget.FORMAT_CHOICES['%Y'] == [(0, '0'), (1, '1')]

    class Field(object):
        id = 'world'
        name = 'helloWorld'
        format = '%d %m %Y'
        data = None

    html = select_birthday_widget(field=Field(), surrounded_div="test-div")
    assert 'world' in html
    assert 'helloWorld' in html
    assert 'class="select_date_day"' in html
    assert 'class="select_date_month"' in html
    assert 'class="select_date_year"' in html
    assert '<div class="test-div">' in html
