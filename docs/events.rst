.. _events:

Events
======

In order to extend FlaskBB you will need to connect your callbacks with
events.

.. admonition:: Additional events

    If you miss an event, feel free to open a new issue or create a pull
    request. The pull request should always contain a entry in this document
    with a small example.

    A event can be created by placing a :func:`~flask.ext.plugins.emit_event`
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


Available Events
----------------


Python Events
~~~~~~~~~~~~~

None at the moment. :(


Template Events
~~~~~~~~~~~~~~~

.. data:: before-first-navigation-element

    This event inserts a navigation link **before** the **first** navigation
    element is rendered.

    Example:

    .. sourcecode:: python

        def inject_navigation_element():
            return render_template("navigation_element_snippet.html")

        connect_event("before-first-navigation-element", inject_navigation_element)


.. data:: after-last-navigation-element

    This event inserts a navigation link **after** the **last** navigation
    element is rendered.

    Example:

    .. sourcecode:: python

        def inject_navigation_element():
            return render_template("navigation_element_snippet.html")

        connect_event("after-last-navigation-element", inject_navigation_element)


