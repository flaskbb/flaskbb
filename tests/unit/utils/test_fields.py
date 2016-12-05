"""Tests for the utils/fields.py file."""
import pytest
from wtforms.form import Form
from flaskbb.utils.fields import SelectBirthdayWidget, BirthdayField


def test_birthday_field():
    class F(Form):
        birthday = BirthdayField(format='%d %m %Y')

    a = ["04 02 2015"]
    b = ["None", "None", "2015"]  # this one should fail
    c = ["None", "None", "None"]

    form = F()

    assert form.birthday.process_formdata(a) is None
    assert form.birthday.process_formdata(c) is None

    with pytest.raises(ValueError):
        form.birthday.process_formdata(b)


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
