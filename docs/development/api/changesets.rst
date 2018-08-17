.. _changesets:

Change Sets
===========

Change sets represent a transition from one state of a model to another. There
is no change set base class, rather change sets are a collection of attributes
representing the state change.

However, there are several assisting classes around them.

Interfaces
----------

.. autoclass:: flaskbb.core.changesets.ChangeSetHandler
    :members:
.. autoclass:: flaskbb.core.changesets.ChangeSetValidator
    :members:
.. autoclass:: flaskbb.core.changesets.ChangeSetPostProcessor
    :members:

Helpers
-------

.. autoclass:: flaskbb.core.changesets.EmptyValue
    :members:

.. autofunction:: flaskbb.core.changesets.is_empty
