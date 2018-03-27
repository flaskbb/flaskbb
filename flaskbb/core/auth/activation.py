# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.activation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Interfaces for handling account activation
    in FlaskBB

    :copyright: (c) 2014-2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from abc import abstractmethod

from ..._compat import ABC


class AccountActivator(ABC):
    @abstractmethod
    def initiate_account_activation(self, user):
        pass

    @abstractmethod
    def activate_account(self, token):
        pass
