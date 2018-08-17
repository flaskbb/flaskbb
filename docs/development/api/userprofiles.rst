.. _userprofiles:

User Profiles
=============

FlaskBB exposes several interfaces, hooks and validators to customize
user profile updates, as well as several implementations for these. For
details on the hooks see :ref:`hooks`



Change Sets
-----------


.. autoclass:: flaskbb.core.user.update.UserDetailsChange

.. autoclass:: flaskbb.core.user.update.PasswordUpdate

.. autoclass:: flaskbb.core.user.update.EmailUpdate

.. autoclass:: flaskbb.core.user.update.SettingsUpdate

Implementations
---------------

Services
~~~~~~~~

.. autoclass:: flaskbb.user.services.update.DefaultDetailsUpdateHandler

.. autoclass:: flaskbb.user.services.update.DefaultPasswordUpdateHandler

.. autoclass:: flaskbb.user.services.update.DefaultEmailUpdateHandler

.. autoclass:: flaskbb.user.services.update.DefaultSettingsUpdateHandler


Validators
~~~~~~~~~~

.. autoclass:: flaskbb.user.services.validators.CantShareEmailValidator
.. autoclass:: flaskbb.user.services.validators.OldEmailMustMatch
.. autoclass:: flaskbb.user.services.validators.EmailsMustBeDifferent
.. autoclass:: flaskbb.user.services.validators.PasswordsMustBeDifferent
.. autoclass:: flaskbb.user.services.validators.OldPasswordMustMatch
.. autoclass:: flaskbb.user.services.validators.ValidateAvatarURL
