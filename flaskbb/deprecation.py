# -*- coding: utf-8 -*-
"""
    flaskbb.deprecation
    ~~~~~~~~~~~~~~~~~~~

    Module used for deprecation handling in FlaskBB
"""

import inspect
import warnings
from abc import abstractproperty
from functools import wraps

from flask_babelplus import gettext as _

from ._compat import ABC


class FlaskBBWarning(Warning):
    pass


class FlaskBBDeprecation(DeprecationWarning, FlaskBBWarning, ABC):
    version = abstractproperty(lambda self: None)


class RemovedInFlaskBB3(FlaskBBDeprecation):
    version = (3, 0, 0)


RemovedInNextVersion = RemovedInFlaskBB3

# deprecation warnings are ignored by default but since we're the application
# let's turn ours on anyways
warnings.simplefilter("default", FlaskBBWarning)


def deprecated(message="", category=RemovedInNextVersion):
    """
    Flags a function or method as deprecated, should not be used on
    classes as it will break inheritance and introspection.

    :param message: Optional message to display along with deprecation warning.
    :param category: Warning category to use, defaults to RemovedInNextVersion,
        if provided must be a subclass of FlaskBBDeprecation.
    """

    def deprecation_decorator(f):
        if not issubclass(category, FlaskBBDeprecation):
            raise ValueError(
                "Expected subclass of FlaskBBDeprecation for category, got {}".format(  # noqa
                    str(category)
                )
            )

        version = ".".join([str(x) for x in category.version])

        warning = _(
            "%(name)s is deprecated and will be removed in version %(version)s.",  # noqa
            name=f.__name__,
            version=version,
        )
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
