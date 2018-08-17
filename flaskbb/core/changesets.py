# -*- coding: utf-8 -*-
"""
    flaskbb.core.changesets
    ~~~~~~~~~~~~~~~~~~~~~

    Core interfaces for handlers, services, etc.

    :copyright: (c) 2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from abc import abstractmethod
from inspect import isclass

from .._compat import ABC

empty = None


class EmptyValue(object):
    """
    Represents an empty change set value when None is a valid value
    to apply to the model.

    This class is a singleton.
    """

    __slots__ = ()

    def __new__(cls):
        # hack to cut down on instances
        global empty
        if empty is None:
            empty = super(EmptyValue, EmptyValue).__new__(cls)
        return empty

    def __eq__(self, other):
        return isinstance(other, EmptyValue) or (
            isclass(other) and issubclass(other, EmptyValue)
        )

    def __bool__(self):
        return False

    __nonzero__ = __bool__


empty = EmptyValue()


def is_empty(value, consider_none=False):
    """
    Helper to check if an arbitrary value is an EmptyValue
    """
    return empty == value or (consider_none and value is None)


class ChangeSetValidator(ABC):
    """
    Used to validate a change set is valid to apply against a model
    """

    @abstractmethod
    def validate(self, model, changeset):
        """
        May raise a :class:`~flaskbb.core.exceptions.ValidationError`
        to signify that the changeset cannot be applied to the model.
        Or a :class:`~flaskbb.core.exceptions.StopValidation` to immediately
        halt all validation.
        """
        pass


class ChangeSetHandler(ABC):
    """
    Used to apply a changeset to a model.
    """

    @abstractmethod
    def apply_changeset(self, model, changeset):
        """
        Receives the current model and the changeset object, apply the
        changeset to the model and persist the model. May raise a
        :class:`~flaskbb.core.exceptions.StopValidation` if the changeset
        could not be applied.
        """


class ChangeSetPostProcessor(ABC):
    """
    Used to handle actions after a change set has been persisted.
    """

    @abstractmethod
    def post_process_changeset(self, model, changeset):
        """
        Used to react to a changeset's application to a model.
        """
