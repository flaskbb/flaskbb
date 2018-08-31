# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.spec
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the core FlaskBB plugin hook definitions

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from pluggy import HookspecMarker

spec = HookspecMarker('flaskbb')


# Setup Hooks
@spec
def flaskbb_extensions(app):
    """Hook for initializing any plugin loaded extensions."""


@spec
def flaskbb_load_translations():
    """Hook for registering translation folders."""


@spec
def flaskbb_load_migrations():
    """Hook for registering additional migrations."""


@spec
def flaskbb_load_blueprints(app):
    """Hook for registering blueprints.

    :param app: The application object.
    """


@spec
def flaskbb_request_processors(app):
    """Hook for registering pre/post request processors.

    :param app: The application object.
    """


@spec
def flaskbb_errorhandlers(app):
    """Hook for registering error handlers.

    :param app: The application object.
    """


@spec
def flaskbb_jinja_directives(app):
    """Hook for registering jinja filters, context processors, etc.

    :param app: The application object.
    """


@spec
def flaskbb_additional_setup(app, pluggy):
    """Hook for any additional setup a plugin wants to do after all other
    application setup has finished.

    For example, you could apply a WSGI middleware::

        @impl
        def flaskbb_additional_setup(app):
            app.wsgi_app = ProxyFix(app.wsgi_app)

    :param app: The application object.
    :param pluggy: The pluggy object.
    """


@spec
def flaskbb_load_post_markdown_class(app):
    """
    Hook for loading a mistune renderer child class in order to render
    markdown on posts and user signatures. All classes returned by this hook
    will be composed into a single class to render markdown for posts.

    Since all classes will be composed together, child classes should call
    super as appropriate and not add any new arguments to `__init__` since the
    class will be insantiated with predetermined arguments.


    Example::

        class YellingRenderer(mistune.Renderer):
            def paragraph(self, text):
                return super(YellingRenderer, self).paragraph(text.upper())

        @impl
        def flaskbb_load_post_markdown_class():
            return YellingRenderer

    :param app: The application object associated with the class if needed
    :type app: Flask
    """


@spec
def flaskbb_load_nonpost_markdown_class(app):
    """
    Hook for loading a mistune renderer child class in order to render
    markdown in locations other than posts, for example in category or
    forum descriptions. All classes returned by this hook will be composed into
    a single class to render markdown for nonpost content (e.g. forum and
    category descriptions).

    Since all classes will be composed together, child classes should call
    super as appropriate and not add any new arguments to `__init__` since the
    class will be insantiated with predetermined arguments.

    Example::

        class YellingRenderer(mistune.Renderer):
            def paragraph(self, text):
                return super(YellingRenderer, self).paragraph(text.upper())

        @impl
        def flaskbb_load_nonpost_markdown_class():
            return YellingRenderer

    :param app: The application object associated with the class if needed
    :type app: Flask
    """

@spec
def flaskbb_load_post_inline_class(app):
    """
    See flaskbb_load_post_markdown_class. Provides the inline lexer class for
    posts.
    """

def flaskbb_load_nonpost_inline_class(app):
    """
    See flaskbb_load_post_markdown_class. Provides the inline lexer class for
    non-post areas.
    """


@spec
def flaskbb_cli(cli, app):
    """Hook for registering CLI commands.

    For example::

        @impl
        def flaskbb_cli(cli):
            @cli.command()
            def testplugin():
                click.echo("Hello Testplugin")

            return testplugin

    :param app: The application object.
    :param cli: The FlaskBBGroup CLI object.
    """


@spec
def flaskbb_shell_context():
    """Hook for registering shell context handlers
    Expected to return a single callable function that returns a dictionary or
    iterable of key value pairs.
    """


# Event hooks
@spec
def flaskbb_event_post_save_before(post):
    """Hook for handling a post before it has been saved.

    :param flaskbb.forum.models.Post post: The post which triggered the event.
    """


@spec
def flaskbb_event_post_save_after(post, is_new):
    """Hook for handling a post after it has been saved.

    :param flaskbb.forum.models.Post post: The post which triggered the event.
    :param bool is_new: True if the post is new, False if it is an edit.
    """


@spec
def flaskbb_event_topic_save_before(topic):
    """Hook for handling a topic before it has been saved.

    :param flaskbb.forum.models.Topic topic: The topic which triggered the
                                             event.
    """


@spec
def flaskbb_event_topic_save_after(topic, is_new):
    """Hook for handling a topic after it has been saved.

    :param flaskbb.forum.models.Topic topic: The topic which triggered the
                                             event.
    :param bool is_new: True if the topic is new, False if it is an edit.
    """


@spec
def flaskbb_event_user_registered(username):
    """Hook for handling events after a user is registered

    :param username: The username of the newly registered user.
    """


@spec(firstresult=True)
def flaskbb_authenticate(identifier, secret):
    """Hook for authenticating users in FlaskBB.
    This hook should return either an instance of
    :class:`flaskbb.user.models.User` or None.

    If a hook decides that all attempts for authentication
    should end, it may raise a
    :class:`flaskbb.core.exceptions.StopAuthentication`
    and include a reason why authentication was stopped.


    Only the first User result will used and the default FlaskBB
    authentication is tried last to give others an attempt to
    authenticate the user instead.

    See also:
    :class:`AuthenticationProvider<flaskbb.core.auth.AuthenticationProvider>`

    Example of alternative auth::

        def ldap_auth(identifier, secret):
            "basic ldap example with imaginary ldap library"
            user_dn = "uid={},ou=flaskbb,dc=flaskbb,dc=org"
            try:
                ldap.bind(user_dn, secret)
                return User.query.join(
                    UserLDAP
                ).filter(
                    UserLDAP.dn==user_dn
                ).with_entities(User).one()
            except:
                return None

        @impl
        def flaskbb_authenticate(identifier, secret):
            return ldap_auth(identifier, secret)

    Example of ending authentication::

        def prevent_login_with_too_many_failed_attempts(identifier):
            user = User.query.filter(
                db.or_(
                    User.username == identifier,
                    User.email == identifier
                )
            ).first()

            if user is not None:
                if has_too_many_failed_logins(user):
                    raise StopAuthentication(_(
                        "Your account is temporarily locked due to too many login attempts"
                    ))

        @impl(tryfirst=True)
        def flaskbb_authenticate(user, identifier):
            prevent_login_with_too_many_failed_attempts(identifier)

    """


@spec
def flaskbb_post_authenticate(user):
    """Hook for handling actions that occur after a user is
    authenticated but before setting them as the current user.

    This could be used to handle MFA. However, these calls will
    be blocking and should be taken into account.

    Responses from this hook are not considered at all. If a hook
    should need to prevent the user from logging in, it should
    register itself as tryfirst and raise a
    :class:`flaskbb.core.exceptions.StopAuthentication`
    and include why the login was prevented.

    See also:
    :class:`PostAuthenticationHandler<flaskbb.core.auth.PostAuthenticationHandler>`

    Example::

        def post_auth(user):
            today = utcnow()
            if is_anniversary(today, user.date_joined):
                flash(_("Happy registerversary!"))

        @impl
        def flaskbb_post_authenticate(user):
            post_auth(user)
    """


@spec
def flaskbb_authentication_failed(identifier):
    """Hook for handling authentication failure events.
    This hook will only be called when no authentication
    providers successfully return a user or a
    :class:`flaskbb.core.exceptions.StopAuthentication`
    is raised during the login process.

    See also:
    :class:`AuthenticationFailureHandler<flaskbb.core.auth.AuthenticationFailureHandler>`

    Example::

        def mark_failed_logins(identifier):
            user = User.query.filter(
                db.or_(
                    User.username == identifier,
                    User.email == identifier
                )
            ).first()

            if user is not None:
                if user.login_attempts is None:
                    user.login_attempts = 1
                else:
                    user.login_attempts += 1
                user.last_failed_login = utcnow()
    """


@spec(firstresult=True)
def flaskbb_reauth_attempt(user, secret):
    """Hook for handling reauth in FlaskBB

    These hooks receive the currently authenticated user
    and the entered secret. Only the first response from
    this hook is considered -- similar to the authenticate
    hooks. A successful attempt should return True, otherwise
    None for an unsuccessful or untried reauth from an
    implementation. Reauth will be considered a failure if
    no implementation return True.

    If a hook decides that a reauthenticate attempt should
    cease, it may raise StopAuthentication.

    See also:
    :class:`ReauthenticateProvider<flaskbb.core.auth.ReauthenticateProvider>`

    Example of checking secret or passing to the next implementer::

        @impl
        def flaskbb_reauth_attempt(user, secret):
            if check_password(user.password, secret):
                return True


    Example of forcefully ending reauth::

        @impl
        def flaskbb_reauth_attempt(user, secret):
            if user.login_attempts > 5:
                raise StopAuthentication(_("Too many failed authentication attempts"))
    """


@spec
def flaskbb_post_reauth(user):
    """Hook called after successfully reauthenticating.

    These hooks are called a user has passed the flaskbb_reauth_attempt
    hooks but before their reauth is confirmed so a post reauth implementer
    may still force a reauth to fail by raising StopAuthentication.

    Results from these hooks are not considered.

    See also:
    :class:`PostReauthenticateHandler<flaskbb.core.auth.PostAuthenticationHandler>`
    """


@spec
def flaskbb_reauth_failed(user):
    """Hook called if a reauth fails.

    These hooks will only be called if no implementation
    for flaskbb_reauth_attempt returns a True result or if
    an implementation raises StopAuthentication.

    If an implementation raises ForceLogout it should register
    itself as trylast to give other reauth failed handlers an
    opprotunity to run first.

    See also:
    :class:`ReauthenticateFailureHandler<flaskbb.core.auth.ReauthenticateFailureHandler>`
    """


# Form hooks
@spec
def flaskbb_form_new_post(form):
    """Hook for modifying the :class:`~flaskbb.forum.forms.ReplyForm`.

    For example::

        @impl
        def flaskbb_form_new_post(form):
            form.example = TextField("Example Field", validators=[
                DataRequired(message="This field is required"),
                Length(min=3, max=50)])

    :param form: The :class:`~flaskbb.forum.forms.ReplyForm` class.
    """


@spec
def flaskbb_form_new_post_save(form):
    """Hook for modifying the :class:`~flaskbb.forum.forms.ReplyForm`.

    This hook is called while populating the post object with
    the data from the form. The post object will be saved after the hook
    call.

    :param form: The form object.
    :param post: The post object.
    """


@spec
def flaskbb_form_new_topic(form):
    """Hook for modifying the :class:`~flaskbb.forum.forms.NewTopicForm`

    :param form: The :class:`~flaskbb.forum.forms.NewTopicForm` class.
    """


@spec
def flaskbb_form_new_topic_save(form, topic):
    """Hook for modifying the :class:`~flaskbb.forum.forms.NewTopicForm`.

    This hook is called while populating the topic object with
    the data from the form. The topic object will be saved after the hook
    call.

    :param form: The form object.
    :param topic: The topic object.
    """


@spec
def flaskbb_form_registration(form):
    """
    Hook for modifying the :class:`~flaskbb.auth.forms.RegisterForm`.

    :param form: The form class
    """


# Template Hooks
@spec
def flaskbb_tpl_navigation_before():
    """Hook for registering additional navigation items.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_navigation_after():
    """Hook for registering additional navigation items.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_user_nav_loggedin_before():
    """Hook for registering additional user navigational items
    which are only shown when a user is logged in.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_user_nav_loggedin_after():
    """Hook for registering additional user navigational items
    which are only shown when a user is logged in.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_form_registration_before(form):
    """This hook is emitted in the Registration form **before** the first
    input field but after the hidden CSRF token field.

    in :file:`templates/auth/register.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_registration_after(form):
    """This hook is emitted in the Registration form **after** the last
    input field but before the submit field.

    in :file:`templates/auth/register.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_user_details_before(form):
    """This hook is emitted in the Change User Details form **before** an
    input field is rendered.

    in :file:`templates/user/change_user_details.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_user_details_after(form):
    """This hook is emitted in the Change User Details form **after** the last
    input field has been rendered but before the submit field.

    in :file:`templates/user/change_user_details.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_profile_settings_menu():
    """This hook is emitted on the user settings page in order to populate the
    side bar menu. Implementations of this hook should return a list of tuples
    that are view name and display text. The display text will be provided to
    the translation service so it is unnecessary to supply translated text.

    A plugin can declare a new block by setting the view to None. If this is
    done, consider marking the hook implementation with `trylast=True` to
    avoid capturing plugins that do not create new blocks.

    For example::

        @impl(trylast=True)
        def flaskbb_tpl_profile_settings_menu():
            return [
                (None, 'Account Settings'),
                ('user.settings', 'General Settings'),
                ('user.change_user_details', 'Change User Details'),
                ('user.change_email', 'Change E-Mail Address'),
                ('user.change_password', 'Change Password')
            ]

    Hookwrappers for this spec should not be registered as FlaskBB
    supplies its own hookwrapper to flatten all the lists into a single list.

    in :file:`templates/user/settings_layout.html`
    """


@spec
def flaskbb_tpl_admin_settings_menu(user):
    """This hook is emitted in the admin panel and used to add additional
    navigation links to the admin menu.

    Implementations of this hook should return a list of tuples
    that are view name, display text and optionally an icon.
    The display text will be provided to the translation service so it
    is unnecessary to supply translated text.

    For example::

        @impl(trylast=True)
        def flaskbb_tpl_admin_settings_menu():
            # only add this item if the user is an admin
            if Permission(IsAdmin, identity=current_user):
                return [
                    ("myplugin.foobar", "Foobar", "fa fa-foobar")
                ]

    Hookwrappers for this spec should not be registered as FlaskBB
    supplies its own hookwrapper to flatten all the lists into a single list.

    in :file:`templates/management/management_layout.html`

    :param user: The current user object.
    """


@spec
def flaskbb_tpl_profile_sidebar_stats(user):
    """This hook is emitted on the users profile page below the standard
    information. For example, it can be used to add additional items
    such as a link to the profile.

    in :file:`templates/user/profile_layout.html`

    :param user: The user object for whom the profile is currently visited.
    """


@spec
def flaskbb_tpl_post_author_info_before(user, post):
    """This hook is emitted before the information about the
    author of a post is displayed (but after the username).

    in :file:`templates/forum/topic.html`

    :param user: The user object of the post's author.
    :param post: The post object.
    """


@spec
def flaskbb_tpl_post_author_info_after(user, post):
    """This hook is emitted after the information about the
    author of a post is displayed (but after the username).

    in :file:`templates/forum/topic.html`

    :param user: The user object of the post's author.
    :param post: The post object.
    """


@spec
def flaskbb_tpl_post_content_before(post):
    """Hook to do some stuff before the post content is rendered.

    in :file:`templates/forum/topic.html`

    :param post: The current post object.
    """


@spec
def flaskbb_tpl_post_content_after(post):
    """Hook to do some stuff after the post content is rendered.

    in :file:`templates/forum/topic.html`

    :param post: The current post object.
    """


@spec
def flaskbb_tpl_post_menu_before(post):
    """Hook for inserting a new item at the beginning of the post menu.

    in :file:`templates/forum/topic.html`

    :param post: The current post object.
    """


@spec
def flaskbb_tpl_post_menu_after(post):
    """Hook for inserting a new item at the end of the post menu.

    in :file:`templates/forum/topic.html`

    :param post: The current post object.
    """


@spec
def flaskbb_tpl_topic_controls(topic):
    """Hook for inserting additional topic moderation controls.

    in :file:`templates/forum/topic_controls.html`

    :param topic: The current topic object.
    """


@spec
def flaskbb_tpl_form_new_post_before(form):
    """Hook for inserting a new form field before the first field is
    rendered.

    For example::

        @impl
        def flaskbb_tpl_form_new_post_after(form):
            return render_template_string(
                \"""
                <div class="form-group">
                    <div class="col-md-12 col-sm-12 col-xs-12">
                        <label>{{ form.example.label.text }}</label>

                        {{ form.example(class="form-control",
                                        placeholder=form.example.label.text) }}

                        {%- for error in form.example.errors -%}
                        <span class="help-block">{{error}}</span>
                        {%- endfor -%}
                    </div>
                </div>
                \"""

    in :file:`templates/forum/new_post.html`

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_new_post_after(form):
    """Hook for inserting a new form field after the last field is
    rendered (but before the submit field).

    in :file:`templates/forum/new_post.html`

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_new_topic_before(form):
    """Hook for inserting a new form field before the first field is
    rendered (but before the CSRF token).

    in :file:`templates/forum/new_topic.html`

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_new_topic_after(form):
    """Hook for inserting a new form field after the last field is
    rendered (but before the submit button).

    in :file:`templates/forum/new_topic.html`
    :param form: The form object.
    """
