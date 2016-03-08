"""
Look here for more information:
https://github.com/mitsuhiko/flask/blob/master/flask/_compat.py
"""

import sys

PY2 = sys.version_info[0] == 2

if not PY2:     # pragma: no cover
    text_type = str
    string_types = (str,)
    integer_types = (int, )
    intern_method = sys.intern
    range_method = range
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())
    max_integer = sys.maxsize
else:           # pragma: no cover
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
    intern_method = intern
    range_method = xrange
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
    max_integer = sys.maxint


def to_bytes(text):
    """Transform string to bytes."""
    if isinstance(text, text_type):
        text = text.encode('utf-8')
    return text


def to_unicode(input_bytes, encoding='utf-8'):
    """Decodes input_bytes to text if needed."""
    if not isinstance(input_bytes, string_types):
        input_bytes = input_bytes.decode(encoding)
    return input_bytes
