.. _events:

Events
======

In order to extend FlaskBB you will need to connect your callbacks with
events.

.. admonition:: Additional events

    If you miss an event, feel free to open a new issue or create a pull
    request. The pull request should always contain a entry in this document
    with a small example.

    An event can be created by placing a :func:`~flask_plugins.emit_event`
    function at specific places in the code which then can modify the behavior
    of FlaskBB. The same thing applies for template events.

    Python Event:

    .. sourcecode:: python

        def foobar(data)
            somedata = "foobar"
            emit_event("your-newly-contributed-event", somedata)


    Template Event:

    .. sourcecode:: html+jinja

        {{ emit_event("your-newly-contributed-template-event") }}


Python Events
-------------

None at the moment.


Template Events
---------------

Template events, which are used in forms, are usually rendered after the
hidden CSRF token field and before an submit field.


.. data:: before-first-navigation-element

    in ``templates/layout.html``

    This event inserts a navigation link **before** the **first** navigation
    element is rendered.

    .. sourcecode:: python

        def inject_navigation_element():
            return render_template("navigation_element_snippet.html")

        connect_event("before-first-navigation-element", inject_navigation_element)


.. data:: after-last-navigation-element

    in ``templates/layout.html``

    This event inserts a navigation link **after** the **last** navigation
    element is rendered.

    .. sourcecode:: python

        def inject_navigation_element():
            return render_template("navigation_element_snippet.html")

        connect_event("after-last-navigation-element", inject_navigation_element)


.. data:: before-registration-form

    in ``templates/auth/register.html``

    This event is emitted in the Registration form **before** the first
    input field but after the hidden CSRF token field.

    .. sourcecode:: python

        connect_event("before-registration-form", do_before_register_form)


.. data:: after-registration-form

    in ``templates/auth/register.html``

    This event is emitted in the Registration form **after** the last
    input field but before the submit field.

    .. sourcecode:: python

            connect_event("after-registration-form", do_after_register_form)


.. data:: before-update-user-details

    in ``templates/user/change_user_details.html``

    This event is emitted in the Change User Details form **before** an
    input field is rendered.

    .. sourcecode:: python

        connect_event("before-update-user-details", do_before_update_user_form)


.. data:: after-update-user-details

    in ``templates/user/change_user_details.html``

    This event is emitted in the Change User Details form **after** the last
    input field has been rendered but before the submit field.

    .. sourcecode:: python

        connect_event("after-update-user-details", do_after_update_user_form)
