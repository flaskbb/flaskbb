# -*- coding: utf-8 -*-
"""
    flaskbb.utils.datastructures
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A few helpers that are used by flaskbb

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
try:
    from types import SimpleNamespace
except ImportError:
    class SimpleNamespace(dict):

        def __getattr__(self, name):
            try:
                return super(SimpleNamespace, self).__getitem__(name)
            except KeyError:
                raise AttributeError('{0} has no attribute {1}'
                                     .format(self.__class__.__name__, name))

        def __setattr__(self, name, value):
            super(SimpleNamespace, self).__setitem__(name, value)


class TemplateEventResult(list):
    """A list subclass for results returned by the hook that
    concatenates the results if converted to string, otherwise it works
    exactly like any other list.
    """

    def __init__(self, items):
        list.__init__(self, items)

    def __unicode__(self):
        return u"".join(map(str, self))

    def __str__(self):
        if sys.version_info[0] >= 3:
            return self.__unicode__()
        return self.__unicode__().encode("utf-8")
