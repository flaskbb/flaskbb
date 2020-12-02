# -*- coding: utf-8 -*-
"""
    flaskbb.deprecation
    ~~~~~~~~~~~~~~~~~~~

    Module used for deprecation handling in FlaskBB

    :copyright: (c) 2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from abc import ABC
import inspect
import warnings
from abc import abstractproperty
from functools import wraps

from flask_babelplus import gettext as _


class FlaskBBWarning(Warning):
    """
    Base class for any warnings that FlaskBB itself needs to issue, provided
    for convenient filtering.
    """

    pass


class FlaskBBDeprecation(DeprecationWarning, FlaskBBWarning, ABC):
    """
    Base class for deprecations originating from FlaskBB, subclasses must
    provide a version attribute that represents when deprecation becomes a
    removal::


        class RemovedInPluginv3(FlaskBBDeprecation):
            version = (3, 0, 0)
    """

    version = abstractproperty(lambda self: None)


class RemovedInFlaskBB3(FlaskBBDeprecation):
    """
    warning for features removed in FlaskBB3
    """

    version = (3, 0, 0)


def deprecated(message="", category=RemovedInFlaskBB3):
    """
    Flags a function or method as deprecated, should not be used on
    classes as it will break inheritance and introspection.

    :param message: Optional message to display along with deprecation warning.
    :param category: Warning category to use, defaults to RemovedInFlaskBB3,
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

        docstring = f.__doc__

        if docstring:
            docstring = "\n".join([docstring, warning])
        else:
            docstring = warning

        f.__doc__ = docstring

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
