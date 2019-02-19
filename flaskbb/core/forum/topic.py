# -*- coding: utf-8 -*-
"""
    flaskbb.core.forum.topic
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014-2018 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from abc import abstractmethod
from ..._compat import ABC


class TopicService(ABC):
    """
    Used to manage the registration process. A default implementation is
    provided however, this interface is provided in case alternative
    flows are needed.
    """

    @abstractmethod
    def update(self, topic_info):
        """
        This method is abstract.

        :param topic_info: The provided user registration information.
        :type topic_info: :class:`~flaskbb.core.auth.registration.UserRegistrationInfo`
        """  # noqa
        pass


class PostService(ABC):
    """
    Used to manage the registration process. A default implementation is
    provided however, this interface is provided in case alternative
    flows are needed.
    """

    @abstractmethod
    def update(self, post_info):
        """
        This method is abstract.

        :param topic_info: The provided user registration information.
        :type topic_info: :class:`~flaskbb.core.auth.registration.UserRegistrationInfo`
        """  # noqa
        pass


class ForumService(ABC):
    """
    Used to manage the registration process. A default implementation is
    provided however, this interface is provided in case alternative
    flows are needed.
    """

    @abstractmethod
    def update(self, forum_info):
        """
        This method is abstract.

        :param topic_info: The provided user registration information.
        :type topic_info: :class:`~flaskbb.core.auth.registration.UserRegistrationInfo`
        """  # noqa
        pass
