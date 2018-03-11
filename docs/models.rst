.. _models:

Models
======

FlaskBB uses SQLAlchemy as it's ORM. The models are split in three modules
which are covered below.


Forum Models
------------

.. module:: flaskbb.forum.models

This module contains all related models for the forums.

The hierarchy looks like this: Category > Forum > Topic > Post. In the Report
model are stored the reports and the TopicsRead and ForumsRead models are
used to store the status if the user has read a specific forum or not.


.. autoclass:: Category
   :members:


.. autoclass:: Forum
   :members:


.. autoclass:: Topic
   :members:


.. autoclass:: Post
   :members:


.. autoclass:: TopicsRead
   :members:


.. autoclass:: ForumsRead
   :members:


.. autoclass:: Report
   :members:



User Models
-----------

.. module:: flaskbb.user.models

The user modules contains all related models for the users.

.. autoclass:: User
   :members:

.. autoclass:: Group
   :members:


Management Models
-----------------

.. module:: flaskbb.management.models

The management module contains all related models for the management of FlaskBB.

.. autoclass:: SettingsGroup
   :members:

.. autoclass:: Setting
   :members:
