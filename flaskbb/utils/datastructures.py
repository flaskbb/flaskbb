"""
flaskbb.utils.datastructures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A few helpers that are used by flaskbb

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Iterable
from typing import override


class TemplateEventResult(list[object]):
    """A list subclass for results returned by the hook that
    concatenates the results if converted to string, otherwise it works
    exactly like any other list.
    """

    @override
    def __init__(self, items: Iterable[str]):
        list.__init__(self, items)

    def __unicode__(self):
        return "".join(map(str, self))

    @override
    def __str__(self):
        return self.__unicode__()
