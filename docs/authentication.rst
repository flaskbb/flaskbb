.. _authentication:

.. module:: flaskbb.core.auth.authentication

Authentication Interfaces
=========================


FlaskBB exposes several interfaces and hooks to customize authentication. The
below should be considered an exhaustive guide for interfaces and hooks in
FlaskBB but not necessarily their implementations in FlaskBB (though, where
appropriate, these implementations are documented).

Exceptions
----------

.. autoexception:: StopAuthentication
.. autoexception:: ForceLogout

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


Relevant Plugin Hooks
---------------------

.. module:: flaskbb.plugins.spec

.. autofunction:: flaskbb_post_authenticate
.. autofunction:: flaskbb_authentication_failed
.. autofunction:: flaskbb_reauth_attempt
.. autofunction:: flaskbb_post_reauth
.. autofunction:: flaskbb_reauth_failed
