.. _registration:

Registration
============

These interfaces and implementations control the user registration flow in
FlaskBB.

Registration Interfaces
-----------------------

.. module:: flaskbb.core.auth.registration

.. autoclass:: UserRegistrationInfo

.. autoclass:: UserValidator
    :members:

.. autoclass:: UserRegistrationService
    :members:


Registration Provided Implementations
-------------------------------------

.. module:: flaskbb.auth.services.registration

.. autoclass:: UsernameRequirements
.. autoclass:: UsernameValidator
.. autoclass:: UsernameUniquenessValidator
.. autoclass:: EmailUniquenessValidator
.. autoclass:: RegistrationService
