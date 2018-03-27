# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.password
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Interfaces and services for auth services
    related to password.

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from abc import abstractmethod

from ..._compat import ABC


class ResetPasswordService(ABC):

    @abstractmethod
    def initiate_password_reset(self, email):
        pass

    @abstractmethod
    def reset_password(self, token, email, new_password):
        pass
