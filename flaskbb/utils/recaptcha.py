# -*- coding: utf-8 -*-
"""
    flaskbb.utils.recaptcha
    ~~~~~~~~~~~~~~~~~~~~~~~

    The reCAPTCHA Field. Taken from Flask-WTF and modified
    to use our own settings system.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from wtforms.fields import Field

try:
    import urllib2 as http
except ImportError:
    # Python 3
    from urllib import request as http

from flask import request, current_app, Markup, json
from werkzeug import url_encode
from wtforms import ValidationError

from flaskbb._compat import to_bytes, to_unicode
from flaskbb.utils.settings import flaskbb_config

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
            'secret':     private_key,
            'remoteip':   remote_addr,
            'response':   response
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
