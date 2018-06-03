# -*- coding: utf-8 -*-
"""
    flaskbb.deprecation
    ~~~~~~~~~~~~~~~~~~~

    Module used for deprecation handling in FlaskBB
"""

import inspect
import warnings
from functools import wraps
from flask_babelplus import gettext as _


class RemovedInFlaskBB3(DeprecationWarning):
    pass


RemovedInNextVersion = RemovedInFlaskBB3

# deprecation warnings are ignored by default but since we're the application
# let's turn ours on anyways
warnings.simplefilter("default", RemovedInNextVersion)


def deprecated(message="", category=RemovedInNextVersion):
    """
    Flags a function or method as deprecated, should not be used on
    classes as it will break inheritance and introspection.

    :param message: Optional message to display along with deprecation warning.
    :param category: Warning category to use, defaults to RemovedInNextVersion
    """

    def deprecation_decorator(f):
        warning = _("%(name)s is deprecated.", name=f.__name__)
        if message:
            warning = "{} {}".format(warning, message)

        @wraps(f)
        def wrapper(*a, **k):
            frame = inspect.currentframe().f_back
            warnings.warn_explicit(
                warning,
                category=category,
                filename=inspect.getfile(frame.f_code),
                lineno=frame.f_lineno,
            )
            return f(*a, **k)

        return wrapper

    return deprecation_decorator
