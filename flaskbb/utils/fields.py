# -*- coding: utf-8 -*-
"""
    flaskbb.utils.fields
    ~~~~~~~~~~~~~~~~~~~~

    Additional fields and widgets for wtforms.
    The reCAPTCHA Field was taken from Flask-WTF and modified
    to use our own settings system.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
import logging
try:
    import urllib2 as http
except ImportError:
    # Python 3
    from urllib import request as http

from flask import request, current_app, Markup, json
from werkzeug.urls import url_encode
from wtforms import ValidationError
from wtforms.fields import DateField, Field
from wtforms.widgets.core import Select, html_params

from flaskbb._compat import to_bytes, to_unicode
from flaskbb.utils.settings import flaskbb_config


logger = logging.getLogger(__name__)


JSONEncoder = json.JSONEncoder

RECAPTCHA_SCRIPT = u'https://www.google.com/recaptcha/api.js'
RECAPTCHA_TEMPLATE = u'''
<script src='%s' async defer></script>
<div class="g-recaptcha" %s></div>
'''

RECAPTCHA_VERIFY_SERVER = 'https://www.google.com/recaptcha/api/siteverify'
RECAPTCHA_ERROR_CODES = {
    'missing-input-secret': 'The secret parameter is missing.',
    'invalid-input-secret': 'The secret parameter is invalid or malformed.',
    'missing-input-response': 'The response parameter is missing.',
    'invalid-input-response': 'The response parameter is invalid or malformed.'
}


class RecaptchaValidator(object):
    """Validates a ReCaptcha."""

    def __init__(self, message=None):
        if message is None:
            message = RECAPTCHA_ERROR_CODES['missing-input-response']
        self.message = message

    def __call__(self, form, field):
        if current_app.testing or not flaskbb_config["RECAPTCHA_ENABLED"]:
            return True

        if request.json:
            response = request.json.get('g-recaptcha-response', '')
        else:
            response = request.form.get('g-recaptcha-response', '')
        remote_ip = request.remote_addr

        if not response:
            raise ValidationError(field.gettext(self.message))

        if not self._validate_recaptcha(response, remote_ip):
            field.recaptcha_error = 'incorrect-captcha-sol'
            raise ValidationError(field.gettext(self.message))

    def _validate_recaptcha(self, response, remote_addr):
        """Performs the actual validation."""
        try:
            private_key = flaskbb_config['RECAPTCHA_PRIVATE_KEY']
        except KeyError:
            raise RuntimeError("No RECAPTCHA_PRIVATE_KEY config set")

        data = url_encode({
            'secret': private_key,
            'remoteip': remote_addr,
            'response': response
        })

        http_response = http.urlopen(RECAPTCHA_VERIFY_SERVER, to_bytes(data))

        if http_response.code != 200:
            return False

        json_resp = json.loads(to_unicode(http_response.read()))

        if json_resp["success"]:
            return True

        for error in json_resp.get("error-codes", []):
            if error in RECAPTCHA_ERROR_CODES:
                raise ValidationError(RECAPTCHA_ERROR_CODES[error])

        return False


class RecaptchaWidget(object):

    def recaptcha_html(self, public_key):
        html = current_app.config.get('RECAPTCHA_HTML')
        if html:
            return Markup(html)
        params = current_app.config.get('RECAPTCHA_PARAMETERS')
        script = RECAPTCHA_SCRIPT
        if params:
            script += u'?' + url_encode(params)

        attrs = current_app.config.get('RECAPTCHA_DATA_ATTRS', {})
        attrs['sitekey'] = public_key
        snippet = u' '.join([u'data-%s="%s"' % (k, attrs[k]) for k in attrs])
        return Markup(RECAPTCHA_TEMPLATE % (script, snippet))

    def __call__(self, field, error=None, **kwargs):
        """Returns the recaptcha input HTML."""

        if not flaskbb_config["RECAPTCHA_ENABLED"]:
            return

        try:
            public_key = flaskbb_config['RECAPTCHA_PUBLIC_KEY']
        except KeyError:
            raise RuntimeError("RECAPTCHA_PUBLIC_KEY config not set")

        return self.recaptcha_html(public_key)


class RecaptchaField(Field):
    widget = RecaptchaWidget()

    # error message if recaptcha validation fails
    recaptcha_error = None

    def __init__(self, label='', validators=None, **kwargs):
        validators = validators or [RecaptchaValidator()]
        super(RecaptchaField, self).__init__(label, validators, **kwargs)


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

    def __init__(self, years=None):
        """Initialzes the widget.

        :param years: The min year which should be chooseable.
                      Defatuls to ``1930``.
        """
        if years is None:
            years = range(1930, datetime.utcnow().year + 1)

        super(SelectBirthdayWidget, self).__init__()
        self.FORMAT_CHOICES['%Y'] = [(x, str(x)) for x in years]

    # TODO(anr): clean up
    def __call__(self, field, **kwargs):  # noqa: C901
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

                if css_class is not None:  # pragma: no cover
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
                        html.append(
                            Select.render_option("None", " ", selected)
                        )

                    html.append(Select.render_option(value, label, selected))

                html.append('</select>')

                if surrounded_div is not None:
                    html.append("</div>")

            html.append(' ')

        return Markup(''.join(html))


class BirthdayField(DateField):
    """Same as DateField, except it allows ``None`` values in case a user
    wants to delete his birthday.
    """
    widget = SelectBirthdayWidget()

    def __init__(self, label=None, validators=None, format='%Y-%m-%d',
                 **kwargs):
        DateField.__init__(self, label, validators, format, **kwargs)

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
