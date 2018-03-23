# -*- coding: utf-8 -*-
"""
    flaskbb.core.user.repo
    ~~~~~~~~~~~~~~~~~~~~~~

    This module provides an abstracted access to users stored in the database.

    :copyright: (c) 2014-2018 the FlaskbBB Team.
    :license: BSD, see LICENSE for more details
"""

from ..._compat import ABC
from abc import abstractmethod


class UserRepository(ABC):
    @abstractmethod
    def add(self, user_info):
        pass

    @abstractmethod
    def find_by(self, **kwargs):
        pass

    @abstractmethod
    def get(self, user_id):
        pass

    @abstractmethod
    def find_one_by(self, **kwargs):
        pass
