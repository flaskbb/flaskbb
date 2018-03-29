.. _authentication:

.. module:: flaskbb.core.auth.authentication

Authentication Interfaces
=========================


FlaskBB exposes several interfaces and hooks to customize authentication and
implementations of these. For details on the hooks see :ref:`hooks`

Authentication
--------------

.. autoclass:: AuthenticationManager
   :members:
   :undoc-members:

.. autoclass:: AuthenticationProvider
   :members:
   :undoc-members:

.. autoclass:: PostAuthenticationHandler
   :members:
   :undoc-members:

.. autoclass:: AuthenticationFailureHandler
   :members:
   :undoc-members:

Reauthentication
----------------

.. autoclass:: ReauthenticateManager
   :members:
   :undoc-members:

.. autoclass:: ReauthenticateProvider
   :members:
   :undoc-members:

.. autoclass:: PostReauthenticateHandler
   :members:
   :undoc-members:

.. autoclass:: ReauthenticateFailureHandler
   :members:
   :undoc-members:

Exceptions
----------

.. autoexception:: StopAuthentication
.. autoexception:: ForceLogout
