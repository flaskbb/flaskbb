.. _hooks_events:

.. currentmodule:: flaskbb.plugins.spec

FlaskBB Event Hooks
===================

Post and Topic Events
---------------------

.. autofunction:: flaskbb_event_post_save_before
.. autofunction:: flaskbb_event_post_save_after
.. autofunction:: flaskbb_event_topic_save_before
.. autofunction:: flaskbb_event_topic_save_after

Registration Events
-------------------

.. autofunction:: flaskbb_event_user_registered
.. autofunction:: flaskbb_gather_registration_validators
.. autofunction:: flaskbb_registration_post_processor
.. autofunction:: flaskbb_registration_failure_handler

Authentication Events
---------------------

.. autofunction:: flaskbb_authenticate
.. autofunction:: flaskbb_post_authenticate
.. autofunction:: flaskbb_authentication_failed
.. autofunction:: flaskbb_reauth_attempt
.. autofunction:: flaskbb_post_reauth
.. autofunction:: flaskbb_reauth_failed

Profile Edit Events
-------------------

.. autofunction:: flaskbb_gather_password_validators
.. autofunction:: flaskbb_password_updated
.. autofunction:: flaskbb_gather_email_validators
.. autofunction:: flaskbb_email_updated
.. autofunction:: flaskbb_gather_details_update_validators
.. autofunction:: flaskbb_details_updated
.. autofunction:: flaskbb_settings_updated
