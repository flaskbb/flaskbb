# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.spec
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the core FlaskBB plugin hook definitions

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from pluggy import HookspecMarker

spec = HookspecMarker("flaskbb")


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


# TODO(anr): When pluggy 1.0 is released, mark this spec deprecated
@spec
def flaskbb_event_user_registered(username):
    """Hook for handling events after a user is registered

    .. warning::

        This hook is deprecated in favor of
        :func:`~flaskbb.plugins.spec.flaskbb_registration_post_processor`

    :param username: The username of the newly registered user.
    """


@spec
def flaskbb_gather_registration_validators():
    """
    Hook for gathering user registration validators, implementers must return
    a callable that accepts a
    :class:`~flaskbb.core.auth.registration.UserRegistrationInfo` and raises
    a :class:`~flaskbb.core.exceptions.ValidationError` if the registration
    is invalid or :class:`~flaskbb.core.exceptions.StopValidation` if
    validation of the registration should end immediatey.

    Example::

        def cannot_be_named_fred(user_info):
            if user_info.username.lower() == 'fred':
                raise ValidationError(('username', 'Cannot name user fred'))

        @impl
        def flaskbb_gather_registration_validators():
            return [cannot_be_named_fred]

    .. note::

        This is implemented as a hook that returns callables since the
        callables are designed to raise exceptions that are aggregated to
        form the failure message for the registration response.

    See Also: :class:`~flaskbb.core.auth.registration.UserValidator`
    """


@spec
def flaskbb_registration_failure_handler(user_info, failures):
    """
    Hook for dealing with user registration failures, receives the info
    that user attempted to register with as well as the errors that failed
    the registration.

    Example::

        from .utils import fuzz_username

        def has_already_registered(failures):
            return any(
                attr = "username" and "already registered" in msg
                for (attr, msg) in failures
            )


        def suggest_alternate_usernames(user_info, failures):
            if has_already_registered(failures):
                suggestions = fuzz_username(user_info.username)
                failures.append(("username", "Try: {}".format(suggestions)))


        @impl
        def flaskbb_registration_failure_handler(user_info, failures):
            suggest_alternate_usernames(user_info, failures)

    See Also: :class:`~flaskbb.core.auth.registration.RegistrationFailureHandler`
    """  # noqa


@spec
def flaskbb_registration_post_processor(user):
    """
    Hook for handling actions after a user has successfully registered. This
    spec receives the user object after it has been successfully persisted
    to the database.

    Example::

        def greet_user(user):
            flash(_("Thanks for registering {}".format(user.username)))

        @impl
        def flaskbb_registration_post_processor(user):
            greet_user(user)

    See Also: :class:`~flaskbb.core.auth.registration.RegistrationPostProcessor`
    """  # noqa


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
                        "Your account is temporarily locked due to too many"
                        " login attempts"
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
                raise StopAuthentication(
                    _("Too many failed authentication attempts")
                )
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
def flaskbb_form_post(form):
    """Hook for modifying the :class:`~flaskbb.forum.forms.ReplyForm`.

    For example::

        @impl
        def flaskbb_form_post(form):
            form.example = TextField("Example Field", validators=[
                DataRequired(message="This field is required"),
                Length(min=3, max=50)])

    :param form: The :class:`~flaskbb.forum.forms.ReplyForm` class.
    """


@spec
def flaskbb_form_post_save(form, post):
    """Hook for modifying the :class:`~flaskbb.forum.forms.ReplyForm`.

    This hook is called while populating the post object with
    the data from the form. The post object will be saved after the hook
    call.

    :param form: The form object.
    :param post: The post object.
    """


@spec
def flaskbb_form_topic(form):
    """Hook for modifying the :class:`~flaskbb.forum.forms.NewTopicForm`

    For example::

        @impl
        def flaskbb_form_topic(form):
            form.example = TextField("Example Field", validators=[
                DataRequired(message="This field is required"),
                Length(min=3, max=50)])

    :param form: The :class:`~flaskbb.forum.forms.NewTopicForm` class.
    """


@spec
def flaskbb_form_topic_save(form, topic):
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


@spec
def flaskbb_gather_password_validators(app):
    """
    Hook for gathering :class:`~flaskbb.core.changesets.ChangeSetValidator`
    instances specialized for handling :class:`~flaskbb.core.user.update.PasswordUpdate`
    This hook should return an iterable::

        class NotLongEnough(ChangeSetValidator):
            def __init__(self, min_length):
                self._min_length = min_length

            def validate(self, model, changeset):
                if len(changeset.new_password) < self._min_length:
                    raise ValidationError(
                        "new_password",
                        "Password must be at least {} characters ".format(
                            self._min_length
                        )
                    )

        @impl
        def flaskbb_gather_password_validators(app):
            return [NotLongEnough(app.config['MIN_PASSWORD_LENGTH'])]

    :param app: The current application
    """


@spec
def flaskbb_gather_email_validators(app):
    """
    Hook for gathering :class:`~flaskbb.core.changesets.ChangeSetValidator`
    instances specialized for :class:`~flaskbb.core.user.update.EmailUpdate`.
    This hook should return an iterable::

        class BlackListedEmailProviders(ChangeSetValidator):
            def __init__(self, black_list):
                self._black_list = black_list

            def validate(self, model, changeset):
                provider = changeset.new_email.split('@')[1]
                if provider in self._black_list:
                    raise ValidationError(
                        "new_email",
                        "{} is a black listed email provider".format(provider)
                    )

        @impl
        def flaskbb_gather_email_validators(app):
            return [BlackListedEmailProviders(app.config["EMAIL_PROVIDER_BLACK_LIST"])]

    :param app: The current application
    """


@spec
def flaskbb_gather_details_update_validators(app):
    """
    Hook for gathering :class:`~flaskbb.core.changesets.ChangeSetValidator`
    instances specialized for :class:`~flaskbb.core.user.update.UserDetailsChange`.
    This hook should return an iterable::

        class DontAllowImageSignatures(ChangeSetValidator):
            def __init__(self, renderer):
                self._renderer = renderer

            def validate(self, model, changeset):
                rendered = self._renderer.render(changeset.signature)
                if '<img' in rendered:
                    raise ValidationError("signature", "No images allowed in signature")

        @impl
        def flaskbb_gather_details_update_validators(app):
            renderer = app.pluggy.hook.flaskbb_load_nonpost_markdown_class()
            return [DontAllowImageSignatures(renderer())]

    :param app: The current application
    """


@spec
def flaskbb_details_updated(user, details_update):
    """
    Hook for responding to a user updating their details. This hook is called
    after the details update has been persisted.

    See also :class:`~flaskbb.core.changesets.ChangeSetPostProcessor`

    :param user: The user whose details have been updated.
    :param details_update: The details change set applied to the user.
    """


@spec
def flaskbb_password_updated(user):
    """
    Hook for responding to a user updating their password. This hook is called
    after the password change has been persisted::


        @impl
        def flaskbb_password_updated(app, user):
            send_email(
                "Password changed",
                [user.email],
                text_body=...,
                html_body=...
            )


    See also :class:`~flaskbb.core.changesets.ChangeSetPostProcessor`

    :param user: The user that updated their password.
    """


@spec
def flaskbb_email_updated(user, email_update):
    """
    Hook for responding to a user updating their email. This hook is called after
    the email change has been persisted::


        @impl
        def flaskbb_email_updated(app):
            send_email(
                "Email changed",
                [email_change.old_email],
                text_body=...,
                html_body=...
            )

    See also :class:`~flaskbb.core.changesets.ChangeSetPostProcessor`.

    :param user: The user whose email was updated.
    :param email_update: The change set applied to the user.
    """


@spec
def flaskbb_settings_updated(user, settings_update):
    """
    Hook for responding to a user updating their settings. This hook is called after
    the settings change has been persisted.

    See also :class:`~flaskbb.core.changesets.ChangeSetPostProcessor`

    :param user: The user whose settings have been updated.
    :param settings: The settings change set applied to the user.
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
def flaskbb_tpl_profile_settings_menu(user):
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

    .. versionchanged:: 2.1.0
        The user param. Typically this will be the current user but might not
        always be the current user.

    :param user: The user the settings menu is being rendered for.
    """


@spec
def flaskbb_tpl_profile_sidebar_links(user):
    """
    This hook is emitted on the user profile page in order to populate the
    sidebar menu. Implementations of this hook should return an iterable of
    :class:`~flaskbb.display.navigation.NavigationItem` instances::

        @impl
        def flaskbb_tpl_profile_sidebar_links(user):
            return [
                NavigationLink(
                    endpoint="user.profile",
                    name=_("Overview"),
                    icon="fa fa-home",
                    urlforkwargs={"username": user.username},
                ),
                NavigationLink(
                    endpoint="user.view_all_topics",
                    name=_("Topics"),
                    icon="fa fa-comments",
                    urlforkwargs={"username": user.username},
                ),
                NavigationLink(
                    endpoint="user.view_all_posts",
                    name=_("Posts"),
                    icon="fa fa-comment",
                    urlforkwargs={"username": user.username},
                ),
            ]


    .. warning::
        Hookwrappers for this spec should not be registered as FlaskBB registers
        its own hook wrapper to flatten all the results into a single list.

    .. versionadded:: 2.1

    :param user: The user the profile page belongs to.
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
def flaskbb_tpl_admin_settings_sidebar(user):
    """This hook is emitted in the admin panels setting tab and used
    to add additional navigation links to the sidebar settings menu.

    Implementations of this hook should return a list of tuples
    that are view name and display text.
    The display text will be provided to the translation service so it
    is unnecessary to supply translated text.

    For example::

        @impl(trylast=True)
        def flaskbb_tpl_admin_settings_menu():
            return [
                ("myplugin.foobar", "Foobar")
            ]

    Only admins can view the Settings tab.

    Hookwrappers for this spec should not be registered as FlaskBB
    supplies its own hookwrapper to flatten all the lists into a single list.

    in :file:`templates/management/settings.html`

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
