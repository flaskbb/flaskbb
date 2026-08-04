"""
flaskbb.management.views
~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the management views.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import importlib.metadata
import logging
import os
import sys
from datetime import timedelta
from typing import Any

from celery import __version__ as celery_version
from flask import (
    Blueprint,
    current_app,
    flash,
    Flask,
    jsonify,
    redirect,
    request,
    url_for,
)
from flask.views import MethodView
from flask_allows2 import Permission
from flask_babelplus import gettext as _
from flask_login import current_user, login_fresh
from flask_wtf.file import FileStorage
from pluggy import HookimplMarker
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from flaskbb import __version__ as flaskbb_version
from flaskbb.core.settings import flaskbb_config
from flaskbb.core.settings.forms import build_form
from flaskbb.core.settings.models import Setting
from flaskbb.core.settings.registry import setting_registry
from flaskbb.extensions import allows, celery, db
from flaskbb.forum.forms import UserSearchForm
from flaskbb.forum.models import Attachment, Category, Forum, Post, Report, Topic
from flaskbb.management.forms import (
    AddForumForm,
    AddGroupForm,
    AddUserForm,
    assignable_groups,
    AttachmentSearchForm,
    CategoryForm,
    EditForumForm,
    EditGroupForm,
    EditUserForm,
    ModeratorEditUserForm,
    SuperModeratorEditUserForm,
)
from flaskbb.plugins.models import PluginRegistry
from flaskbb.plugins.utils import validate_plugin
from flaskbb.user.models import Group, Guest, User
from flaskbb.utils.helpers import (
    FlashAndRedirect,
    get_online_users,
    redirect_or_next,
    register_view,
    render_template,
    time_diff,
    time_utcnow,
)
from flaskbb.utils.requirements import (
    CanBanTargetUser,
    CanBanUser,
    CanEditTargetUser,
    CanEditUser,
    IsAdmin,
    IsAtleastModerator,
    IsAtleastSuperModerator,
)
from flaskbb.utils.uploads import (
    delete_avatar_file,
    get_attachment_disk_path,
    get_avatar_filename,
    get_avatar_upload_path,
    remove_orphan_attachment_files,
    scan_attachment_storage,
)

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)

PROTECTED_GROUP_ID = 6

# an upload writes the file before it commits the row, so anything younger
# than this is left alone by the cleanup - in either direction
ATTACHMENT_CLEANUP_GRACE = timedelta(minutes=5)

# keeps the identity map and the pending unlink queue bounded when a large
# table is deleted row by row
ATTACHMENT_DELETE_BATCH = 500


class ManagementOverview(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the management panel"),
                level="danger",
                endpoint="forum.index",
            ),
        )
    ]

    def get(self):
        # user and group stats
        banned_users = User.count(
            clause=[Group.banned == True, Group.id == User.primary_group_id]
        )
        if not current_app.config["REDIS_ENABLED"]:
            online_users = User.count(User.lastseen >= time_diff())
        else:
            online_users = len(get_online_users())

        unread_reports = Report.count(Report.zapped == None)

        python_version = (
            f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
        )

        stats = {
            "current_app": current_app,
            "unread_reports": unread_reports,
            # stats stats
            "all_users": User.count(),
            "banned_users": banned_users,
            "online_users": online_users,
            "all_groups": Group.count(),
            "report_count": Report.count(),
            "topic_count": Topic.count(),
            "post_count": Post.count(),
            "attachment_count": Attachment.count(),
            # components
            "python_version": python_version,
            "celery_version": celery_version,
            "flask_version": importlib.metadata.version("flask"),
            "flaskbb_version": flaskbb_version,
            # plugins
            "plugins": PluginRegistry.get_all(),
        }

        return render_template("management/overview.html", **stats)


class ManagementSettings(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the management settings"),  # noqa
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self, slug: str | None = None, plugin: str | None = None):
        form, old_settings, _, active_nav = self._determine_active_settings(
            slug, plugin
        )

        form.process(data=old_settings)

        return render_template(
            "management/settings.html",
            form=form,
            active_nav=active_nav,
        )

    def post(self, slug: str | None = None, plugin: str | None = None):
        form, _, plugin_obj, active_nav = self._determine_active_settings(slug, plugin)

        if form.validate_on_submit():
            if plugin_obj is not None:
                plugin_obj.update_settings(form.data)
            else:
                Setting.update(slug if slug else "general", form.data)
            flash("Settings saved.", "success")

        return render_template(
            "management/settings.html",
            form=form,
            active_nav=active_nav,
        )

    def _determine_active_settings(self, slug: str | None, plugin: str | None):
        """Determines which settings are active.

        Returns a tuple in following order:
        ``form``, ``old_settings``, ``plugin_obj``, ``active_nav``
        """
        slug = slug if slug else "general"
        active_nav: dict[str, str] = {}
        plugin_obj = None

        if plugin is not None:
            # plugin settings (PluginRegistry) are a separate mechanism
            # from SettingGroup and are untouched by this refactor
            plugin_obj = PluginRegistry.get_by_or_404(name=plugin)
            active_nav.update(
                {"key": plugin_obj.name, "title": plugin_obj.name.title()}
            )
            form = plugin_obj.get_settings_form()
            if plugin_obj.needs_setting_upgrade():
                flash(_("Upgrade the plugin first to update its setting!"), "warning")
                form.disable_all()
            old_settings = plugin_obj.settings
        else:
            group_obj = setting_registry.group(slug)
            active_nav.update({"key": group_obj.key, "title": group_obj.name})

            form_cls = build_form(group_obj)
            form = form_cls()

            all_values = Setting.as_dict()
            old_settings = {
                setting.key: all_values[setting.key] for setting in group_obj.settings
            }

        return form, old_settings, plugin_obj, active_nav


class ManageUsers(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = UserSearchForm

    def get(self):
        page = request.args.get("page", 1, type=int)
        form = self.form()

        users = db.paginate(
            select(User).order_by(User.id.asc()),
            page=page,
            per_page=flaskbb_config["USERS_PER_PAGE"],
            error_out=False,
        )

        return render_template("management/users.html", users=users, search_form=form)

    def post(self):
        page = request.args.get("page", 1, type=int)
        form = self.form()

        if form.validate():
            users = db.paginate(
                form.get_results(),
                page=page,
                per_page=flaskbb_config["USERS_PER_PAGE"],
                error_out=False,
            )
            return render_template(
                "management/users.html", users=users, search_form=form
            )

        users = db.paginate(
            select(User).order_by(User.id.asc()),
            page=page,
            per_page=flaskbb_config["USERS_PER_PAGE"],
            error_out=False,
        )
        return render_template("management/users.html", users=users, search_form=form)


class EditUser(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            CanEditUser,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = EditUserForm

    def _load_target_user(self, user_id: int):
        """Loads the user being edited, or ``None`` if the acting user may not
        touch that account.
        """
        user = User.get_by_or_404(id=user_id)

        if not Permission(CanEditTargetUser(user), identity=current_user):
            return None

        return user

    def _form_for(self, user: User):
        # Administrators keep every field, including on their own account. The
        # template asks them to confirm a change to their own group or
        # activation rather than taking the choice away.
        if Permission(IsAdmin, identity=current_user):
            return self.form(user)

        # A super moderator may hand out groups, but not to themselves - that
        # would be a self-demotion or self-ban, so they fall through to the
        # moderator form for their own account.
        if (
            Permission(IsAtleastSuperModerator, identity=current_user)
            and user.id != current_user.id
        ):
            return SuperModeratorEditUserForm(user)

        return ModeratorEditUserForm(user)

    def _restrict_group_choices(self, form: EditUserForm, user: User):
        """Narrows the group fields to what the acting user may hand out.

        Does nothing for moderators, whose form has no group fields at all.
        """
        if form.primary_group is None or form.secondary_groups is None:
            return

        groups = assignable_groups()
        form.primary_group.query = groups  # pyright: ignore[reportAttributeAccessIssue]
        form.secondary_groups.query = [  # pyright: ignore[reportAttributeAccessIssue]
            group for group in groups if group.id != user.primary_group_id
        ]

    def get(self, user_id: int):
        user = self._load_target_user(user_id)
        if user is None:
            flash(_("You are not allowed to edit this user."), "danger")
            return redirect(url_for("management.users"))

        form = self._form_for(user)
        self._restrict_group_choices(form, user)

        return render_template(
            "management/user_form.html", form=form, user=user, title=_("Edit User")
        )

    def post(self, user_id: int):
        user = self._load_target_user(user_id)
        if user is None:
            flash(_("You are not allowed to edit this user."), "danger")
            return redirect(url_for("management.users"))

        form = self._form_for(user)
        self._restrict_group_choices(form, user)

        if form.validate_on_submit():
            form.populate_obj(user, exclude=("avatar", "secondary_groups"))

            if form.primary_group is not None:
                user.primary_group_id = form.primary_group.data.id

            if form.delete_avatar.data:
                delete_avatar_file(user.avatar)
                user.avatar = None

            if form.avatar.data and isinstance(form.avatar.data, FileStorage):
                filename = get_avatar_filename(user.username, form.avatar.data.filename)
                form.avatar.data.save(os.path.join(get_avatar_upload_path(), filename))
                user.avatar = filename

            # Don't override the password
            if form.password is not None and form.password.data:
                user.password = form.password.data

            # Passing groups=None leaves the existing secondary groups alone,
            # which is what has to happen when the form has no groups field.
            groups = (
                None if form.secondary_groups is None else form.secondary_groups.data
            )
            user.save(groups=groups)

            flash(_("User updated."), "success")
            return redirect(url_for("management.edit_user", user_id=user.id))

        return render_template(
            "management/user_form.html", form=form, user=user, title=_("Edit User")
        )


class DeleteUser(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, user_id: int | None = None):
        # ajax request
        json = request.get_json(silent=True)
        if json is not None:
            ids = json.get("ids")
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)
            data: list[dict[str, Any]] = []
            for user in User.get_all(User.id.in_(ids)):
                # do not delete current user
                if current_user.id == user.id:
                    continue

                if user.delete():
                    data.append(
                        {
                            "id": user.id,
                            "type": "delete",
                            "reverse": False,
                            "reverse_name": None,
                            "reverse_url": None,
                        }
                    )

            return jsonify(
                message=f"{len(data)} users deleted.",
                category="success",
                data=data,
                status=200,
            )

        user = User.get_by_or_404(id=user_id)

        if current_user.id == user.id:
            flash(_("You cannot delete yourself."), "danger")
            return redirect(url_for("management.users"))

        user.delete()
        flash(_("User deleted."), "success")
        return redirect(url_for("management.users"))


class DeleteUserPosts(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, user_id: int):
        user = User.get_by_or_404(id=user_id)

        # Post.delete() can cascade-delete the whole topic (and every post in
        # it) when it's a topic's first post, so a pre-fetched batch could
        # hold stale objects for rows a previous iteration already removed.
        # Re-querying the lowest remaining id each time sidesteps that.
        while True:
            post = db.session.execute(
                db.select(Post)
                .where(Post.user_id == user.id)
                .order_by(Post.id)
                .limit(1)
            ).scalar_one_or_none()
            if post is None:
                break
            post.delete()

        flash(
            _("All posts by %(user)s have been deleted.", user=user.username),
            "success",
        )
        return redirect(url_for("management.users"))


class AddUser(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = AddUserForm

    def get(self):
        return render_template(
            "management/user_form.html", form=self.form(), title=_("Add User")
        )

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            form.save()
            flash(_("User added."), "success")
            return redirect(url_for("management.users"))

        return render_template(
            "management/user_form.html", form=form, title=_("Add User")
        )


class BannedUsers(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = UserSearchForm

    def get(self):
        page = request.args.get("page", 1, type=int)
        search_form = self.form()

        users = db.paginate(
            select(User)
            .join(Group, Group.id == User.primary_group_id)
            .where(Group.banned == True),
            page=page,
            per_page=flaskbb_config["USERS_PER_PAGE"],
            error_out=False,
        )

        return render_template(
            "management/banned_users.html", users=users, search_form=search_form
        )

    def post(self):
        page = request.args.get("page", 1, type=int)
        search_form = self.form()

        users = db.paginate(
            select(User)
            .join(Group, Group.id == User.primary_group_id)
            .where(Group.banned == True),
            page=page,
            per_page=flaskbb_config["USERS_PER_PAGE"],
            error_out=False,
        )

        if search_form.validate():
            users = db.paginate(
                search_form.get_results(),
                page=page,
                per_page=flaskbb_config["USERS_PER_PAGE"],
                error_out=False,
            )

            return render_template(
                "management/banned_users.html", users=users, search_form=search_form
            )

        return render_template(
            "management/banned_users.html", users=users, search_form=search_form
        )


class BanUser(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, user_id: int | None = None):
        if not Permission(CanBanUser, identity=current_user):
            flash(_("You do not have the permissions to ban this user."), "danger")
            return redirect(url_for("management.overview"))

        # ajax request
        json = request.get_json(silent=True)
        if json is not None:
            ids = json.get("ids")
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)

            data: list[dict[str, Any]] = []
            users = User.get_all(User.id.in_(ids))
            for user in users:
                # don't let a user ban himself and do not allow banning a user
                # who is not outranked by the acting user
                if current_user.id == user.id or not Permission(
                    CanBanTargetUser(user), identity=current_user
                ):
                    continue

                elif user.ban():
                    data.append(
                        {
                            "id": user.id,
                            "type": "ban",
                            "reverse": "unban",
                            "reverse_name": _("Unban"),
                            "reverse_url": url_for(
                                "management.unban_user", user_id=user.id
                            ),
                        }
                    )

            return jsonify(
                message=f"{len(data)} users banned.",
                category="success",
                data=data,
                status=200,
            )

        user = User.get_by_or_404(id=user_id)
        # Do not allow banning a user who is not outranked by the acting user
        if not Permission(CanBanTargetUser(user), identity=current_user):
            flash(_("You are not allowed to ban this user."), "danger")
            return redirect(url_for("management.overview"))

        if not current_user.id == user.id and user.ban():
            flash(_("User is now banned."), "success")
        else:
            flash(_("Could not ban user."), "danger")

        return redirect_or_next(url_for("management.banned_users"))


class UnbanUser(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, user_id: int | None = None):
        if not Permission(CanBanUser, identity=current_user):
            flash(_("You do not have the permissions to unban this user."), "danger")
            return redirect(url_for("management.overview"))

        # ajax request
        json = request.get_json(silent=True)
        if json is not None:
            ids = json.get("ids")
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)

            data: list[dict[str, Any]] = []
            for user in User.get_all(User.id.in_(ids)):
                # unban() drops the user into the member group, so it needs the
                # same target check as banning
                if not Permission(CanBanTargetUser(user), identity=current_user):
                    continue

                if user.unban():
                    data.append(
                        {
                            "id": user.id,
                            "type": "ban",
                            "reverse": "ban",
                            "reverse_name": _("Ban"),
                            "reverse_url": url_for(
                                "management.ban_user", user_id=user.id
                            ),
                        }
                    )

            return jsonify(
                message=f"{len(data)} users unbanned.",
                category="success",
                data=data,
                status=200,
            )

        user = User.get_by_or_404(id=user_id)

        if not Permission(CanBanTargetUser(user), identity=current_user):
            flash(_("You are not allowed to unban this user."), "danger")
            return redirect(url_for("management.overview"))

        if user.unban():
            flash(_("User is now unbanned."), "success")
        else:
            flash(_("Could not unban user."), "danger")

        return redirect_or_next(url_for("management.users"))


class Groups(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self):
        page = request.args.get("page", 1, type=int)

        groups = db.paginate(
            select(Group).order_by(Group.id.asc()),
            page=page,
            per_page=flaskbb_config["USERS_PER_PAGE"],
            error_out=False,
        )
        return render_template("management/groups.html", groups=groups)


class AddGroup(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = AddGroupForm

    def get(self):
        return render_template(
            "management/group_form.html", form=self.form(), title=_("Add Group")
        )

    def post(self):
        form = AddGroupForm()
        if form.validate_on_submit():
            form.save()
            flash(_("Group added."), "success")
            return redirect(url_for("management.groups"))

        return render_template(
            "management/group_form.html", form=form, title=_("Add Group")
        )


class EditGroup(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = EditGroupForm

    def get(self, group_id: int):
        group = Group.get_by_or_404(id=group_id)
        form = self.form(group)
        return render_template(
            "management/group_form.html", form=form, title=_("Edit Group")
        )

    def post(self, group_id: int):
        group = Group.get_by_or_404(id=group_id)
        form = EditGroupForm(group)

        if form.validate_on_submit():
            form.populate_obj(group)
            group.save()

            if group.guest:
                Guest.invalidate_cache()

            flash(_("Group updated."), "success")
            return redirect(url_for("management.groups", group_id=group.id))

        return render_template(
            "management/group_form.html", form=form, title=_("Edit Group")
        )


class DeleteGroup(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, group_id: int | None = None):
        json = request.get_json(silent=True)
        if json is not None:
            ids: list[Any] = json.get("ids", [])
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)

            try:
                id_list = [int(id) for id in ids]
            except (ValueError, TypeError):
                return jsonify(
                    message="No valid ids provided.", category="error", status=404
                )

            if any(id <= PROTECTED_GROUP_ID for id in id_list):
                return jsonify(
                    message=_("You cannot delete one of the standard groups."),
                    category="danger",
                    data=None,
                    status=404,
                )

            data: list[dict[str, Any]] = []
            for group in Group.get_all(Group.id.in_(id_list)):
                group.delete()
                data.append(
                    {
                        "id": group.id,
                        "type": "delete",
                        "reverse": False,
                        "reverse_name": None,
                        "reverse_url": None,
                    }
                )

            return jsonify(
                message=f"{len(data)} groups deleted.",
                category="success",
                data=data,
                status=200,
            )

        if group_id is not None:
            if group_id <= PROTECTED_GROUP_ID:  # there are 6 standard groups
                flash(
                    _(
                        "You cannot delete the standard groups. Try renaming it instead."
                    ),
                    "danger",
                )
                return redirect(url_for("management.groups"))

            group = Group.get_by_or_404(id=group_id)
            group.delete()
            flash(_("Group deleted."), "success")
            return redirect(url_for("management.groups"))

        flash(_("No group chosen."), "danger")
        return redirect(url_for("management.groups"))


class Forums(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self):
        categories = db.session.execute(
            select(Category).order_by(Category.position.asc())
        ).scalars()
        return render_template("management/forums.html", categories=categories)


class EditForum(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = EditForumForm

    def get(self, forum_id: int):
        forum = Forum.get_by_or_404(id=forum_id)

        form = self.form(forum)

        if forum.moderators:
            form.moderators.data = ",".join(
                [user.username for user in forum.moderators]
            )
        else:
            form.moderators.data = None

        return render_template(
            "management/forum_form.html", form=form, title=_("Edit Forum")
        )

    def post(self, forum_id: int):
        forum = Forum.get_by_or_404(id=forum_id)

        form = self.form(forum)
        if form.validate_on_submit():
            form.save()
            flash(_("Forum updated."), "success")
            return redirect(url_for("management.edit_forum", forum_id=forum.id))
        else:
            if forum.moderators:
                form.moderators.data = ",".join(
                    [user.username for user in forum.moderators]
                )
            else:
                form.moderators.data = None

        return render_template(
            "management/forum_form.html", form=form, title=_("Edit Forum")
        )


class AddForum(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = AddForumForm

    def get(self, category_id: int | None = None):
        form = self.form()

        form.groups.data = db.session.execute(
            select(Group).order_by(Group.id.asc())
        ).scalars()

        if category_id:
            category = Category.get_by(id=category_id)
            form.category.data = category

        return render_template(
            "management/forum_form.html", form=form, title=_("Add Forum")
        )

    def post(self, category_id: int | None = None):
        form = self.form()

        if form.validate_on_submit():
            form.save()
            flash(_("Forum added."), "success")
            return redirect(url_for("management.forums"))
        else:
            form.groups.data = db.session.execute(
                select(Group).order_by(Group.id.asc())
            ).scalars()
            if category_id:
                category = Category.get_by(id=category_id)
                form.category.data = category

        return render_template(
            "management/forum_form.html", form=form, title=_("Add Forum")
        )


class DeleteForum(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, forum_id: int):
        forum = Forum.get_by_or_404(id=forum_id)

        involved_users = User.get_all(
            Topic.forum_id == forum.id, Post.user_id == User.id
        )

        forum.delete(involved_users)

        flash(_("Forum deleted."), "success")
        return redirect(url_for("management.forums"))


class AddCategory(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify categories"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = CategoryForm

    def get(self):
        return render_template(
            "management/category_form.html", form=self.form(), title=_("Add Category")
        )

    def post(self):
        form = self.form()

        if form.validate_on_submit():
            form.save()
            flash(_("Category added."), "success")
            return redirect(url_for("management.forums"))

        return render_template(
            "management/category_form.html", form=form, title=_("Add Category")
        )


class EditCategory(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify categories"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = CategoryForm

    def get(self, category_id: int):
        category = Category.get_by_or_404(id=category_id)

        form = self.form(obj=category)

        return render_template(
            "management/category_form.html", form=form, title=_("Edit Category")
        )

    def post(self, category_id: int):
        category = Category.get_by_or_404(id=category_id)

        form = self.form(obj=category)

        if form.validate_on_submit():
            form.populate_obj(category)
            flash(_("Category updated."), "success")
            category.save()

        return render_template(
            "management/category_form.html", form=form, title=_("Edit Category")
        )


class DeleteCategory(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify categories"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, category_id: int):
        category = Category.get_by_or_404(id=category_id)

        involved_users = User.query.filter(
            Forum.category_id == category.id,
            Topic.forum_id == Forum.id,
            Post.user_id == User.id,
        ).all()

        category.delete(involved_users)
        flash(_("Category with all associated forums deleted."), "success")
        return redirect(url_for("management.forums"))


class Reports(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self):
        page = request.args.get("page", 1, type=int)
        reports = Report.query.order_by(Report.id.asc()).paginate(
            page=page, per_page=flaskbb_config["USERS_PER_PAGE"], error_out=False
        )

        return render_template("management/reports.html", reports=reports)


class UnreadReports(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self):
        page = request.args.get("page", 1, type=int)
        reports = (
            Report.query.filter(Report.zapped == None)
            .order_by(Report.id.desc())
            .paginate(
                page=page, per_page=flaskbb_config["USERS_PER_PAGE"], error_out=False
            )
        )

        return render_template("management/reports.html", reports=reports)


class MarkReportRead(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, report_id=None):
        # AJAX request
        json = request.get_json(silent=True)
        if json is not None:
            ids = json.get("ids")
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)

            data: list[dict[str, Any]] = []
            for report in Report.get_all(Report.id.in_(ids)):
                report.zapped_by = current_user.id
                report.zapped = time_utcnow()
                report.save()
                data.append(
                    {
                        "id": report.id,
                        "type": "read",
                        "reverse": False,
                        "reverse_name": None,
                        "reverse_url": None,
                    }
                )

            return jsonify(
                message=f"{len(data)} reports marked as read.",
                category="success",
                data=data,
                status=200,
            )

        # mark single report as read
        if report_id:
            report = Report.get_by_or_404(id=report_id)
            if report.zapped:
                flash(
                    _("Report %(id)s is already marked as read.", id=report.id),
                    "success",
                )
                return redirect_or_next(url_for("management.reports"))

            report.zapped_by = current_user.id
            report.zapped = time_utcnow()
            report.save()
            flash(_("Report %(id)s marked as read.", id=report.id), "success")
            return redirect_or_next(url_for("management.reports"))

        # mark all as read
        reports = Report.get_all(Report.zapped == None)
        report_list: list[Report] = []
        for report in reports:
            report.zapped_by = current_user.id
            report.zapped = time_utcnow()
            report_list.append(report)

        db.session.add_all(report_list)
        db.session.commit()

        flash(_("All reports were marked as read."), "success")
        return redirect_or_next(url_for("management.reports"))


class DeleteReport(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, report_id: int | None = None):
        json = request.get_json(silent=True)
        if json is not None:
            ids = json.get("ids")
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)

            data: list[dict[str, Any]] = []
            for report in Report.get_all(Report.id.in_(ids)):
                if report.delete():
                    data.append(
                        {
                            "id": report.id,
                            "type": "delete",
                            "reverse": False,
                            "reverse_name": None,
                            "reverse_url": None,
                        }
                    )

            return jsonify(
                message=f"{len(data)} reports deleted.",
                category="success",
                data=data,
                status=200,
            )

        report = Report.get_by_or_404(id=report_id)
        report.delete()
        flash(_("Report deleted."), "success")
        return redirect_or_next(url_for("management.reports"))


class ManageAttachments(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage attachments"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]
    form = AttachmentSearchForm

    def get(self):
        return self._render(self._all_attachments(), self.form())

    def post(self):
        form = self.form()

        if form.validate():
            return self._render(form.get_results(), form)

        return self._render(self._all_attachments(), form)

    def _all_attachments(self):
        # id order is the insertion order and unlike date_created it is
        # backed by the primary key index
        return (
            select(Attachment)
            .options(
                joinedload(Attachment.user),
                joinedload(Attachment.post).joinedload(Post.topic),
            )
            .order_by(Attachment.id.desc())
        )

    def _render(self, stmt, search_form):
        page = request.args.get("page", 1, type=int)
        attachments = db.paginate(
            stmt,
            page=page,
            per_page=flaskbb_config["USERS_PER_PAGE"],
            error_out=False,
        )

        # only the rows on this page are stat'ed, so the cleanup button has
        # something to point at without walking the whole upload directory
        missing = {
            attachment.id
            for attachment in attachments.items
            if not os.path.exists(
                get_attachment_disk_path(attachment.post_id, attachment.filename)
            )
        }

        return render_template(
            "management/attachments.html",
            attachments=attachments,
            search_form=search_form,
            missing=missing,
        )


class DeleteAttachment(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage attachments"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, attachment_id: int | None = None):
        # ajax request
        json = request.get_json(silent=True)
        if json is not None:
            ids = json.get("ids")
            if not ids:
                return jsonify(message="No ids provided.", category="error", status=404)

            data: list[dict[str, Any]] = []
            for attachment in Attachment.get_all(Attachment.id.in_(ids)):
                if attachment.delete():
                    data.append(
                        {
                            "id": attachment.id,
                            "type": "delete",
                            "reverse": False,
                            "reverse_name": None,
                            "reverse_url": None,
                        }
                    )

            return jsonify(
                message=f"{len(data)} attachments deleted.",
                category="success",
                data=data,
                status=200,
            )

        attachment = Attachment.get_by_or_404(id=attachment_id)
        attachment.delete()
        flash(_("Attachment deleted."), "success")
        return redirect_or_next(url_for("management.attachments"))


class CleanupAttachments(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage attachments"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self):
        # the disk is scanned before the table is read: a file that appears
        # in between is then guaranteed to have its row in the snapshot
        storage = scan_attachment_storage()
        cutoff = time_utcnow() - ATTACHMENT_CLEANUP_GRACE

        known: dict[str, set[str]] = {}
        stale_rows: list[int] = []
        rows = db.session.execute(
            select(
                Attachment.id,
                Attachment.post_id,
                Attachment.filename,
                Attachment.date_created,
            ).execution_options(yield_per=1000)
        )
        # the cursor is drained before anything is deleted - a flush against
        # a partially read result would lose the rest of it
        for id, post_id, filename, date_created in rows:
            directory = str(post_id)
            known.setdefault(directory, set()).add(filename)

            if filename not in storage.get(directory, {}) and date_created < cutoff:
                stale_rows.append(id)

        deleted_rows = 0
        for start in range(0, len(stale_rows), ATTACHMENT_DELETE_BATCH):
            batch = stale_rows[start : start + ATTACHMENT_DELETE_BATCH]
            for attachment in Attachment.get_all(Attachment.id.in_(batch)):
                db.session.delete(attachment)
                deleted_rows += 1
            db.session.commit()

        deleted_files = remove_orphan_attachment_files(
            storage, known, cutoff=cutoff.timestamp()
        )

        flash(
            _(
                "Removed %(rows)s attachment(s) with a missing file and "
                "%(files)s orphaned file(s).",
                rows=deleted_rows,
                files=deleted_files,
            ),
            "success",
        )
        return redirect(url_for("management.attachments"))


class PurgeAttachments(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage attachments"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self):
        # a bulk DELETE would not fire the after_delete event and strand
        # every file on disk, so the rows go through the ORM
        deleted_rows = 0
        while True:
            batch = db.session.scalars(
                select(Attachment)
                .order_by(Attachment.id)
                .limit(ATTACHMENT_DELETE_BATCH)
            ).all()
            if not batch:
                break

            for attachment in batch:
                db.session.delete(attachment)
            deleted_rows += len(batch)
            db.session.commit()

        # picks up whatever the delete events could not know about: orphaned
        # files and the post directories they kept alive
        deleted_files = remove_orphan_attachment_files(scan_attachment_storage(), {})

        flash(
            _(
                "Purged %(rows)s attachment(s) and %(files)s leftover file(s).",
                rows=deleted_rows,
                files=deleted_files,
            ),
            "success",
        )
        return redirect(url_for("management.attachments"))


class CeleryStatus(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the management settings"),  # noqa
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self):
        celery_inspect = celery.control.inspect()
        try:
            celery_running = True if celery_inspect.ping() else False
        except Exception:
            # catching Exception is bad, and just catching ConnectionError
            # from redis is also bad because you can run celery with other
            # brokers as well.
            celery_running = False

        return jsonify(celery_running=celery_running, status=200)


class PluginsView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def get(self):
        plugins = PluginRegistry.get_all()
        return render_template("management/plugins.html", plugins=plugins)


class EnablePlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, name: str):
        validate_plugin(name)
        plugin = PluginRegistry.get_by_or_404(name=name)

        if plugin.enabled:
            flash(
                _("Plugin %(plugin)s is already enabled.", plugin=plugin.name), "info"
            )
            return redirect(url_for("management.plugins"))

        plugin.enabled = True
        plugin.save()

        flash(
            _(
                "Plugin %(plugin)s enabled. Please restart FlaskBB now.",
                plugin=plugin.name,
            ),
            "success",
        )
        return redirect(url_for("management.plugins"))


class DisablePlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, name: str):
        validate_plugin(name)
        plugin = PluginRegistry.get_by_or_404(name=name)

        if not plugin.enabled:
            flash(
                _("Plugin %(plugin)s is already disabled.", plugin=plugin.name), "info"
            )
            return redirect(url_for("management.plugins"))

        plugin.enabled = False
        plugin.save()
        flash(
            _(
                "Plugin %(plugin)s disabled. Please restart FlaskBB now.",
                plugin=plugin.name,
            ),
            "success",
        )
        return redirect(url_for("management.plugins"))


class InstallPlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, name: str):
        validate_plugin(name)
        plugin = PluginRegistry.get_by_or_404(name=name)
        plugin.add_settings()

        flash(_("Plugin has been installed."), "success")
        return redirect(url_for("management.plugins"))


class UninstallPlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, name: str):
        validate_plugin(name)
        plugin = PluginRegistry.get_by_or_404(name=name)
        plugin.remove_settings()

        flash(_("Plugin has been uninstalled."), "success")
        return redirect(url_for("management.plugins"))


class UpgradePlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview",
            ),
        )
    ]

    def post(self, name: str):
        validate_plugin(name)
        plugin = PluginRegistry.get_by_or_404(name=name)

        diff = plugin.get_setting_diff()
        if diff is None:
            flash(_("This plugin has no settings to upgrade."), "info")
            return redirect(url_for("management.plugins"))

        if not diff.has_changes:
            flash(_("This plugin's settings are already up to date."), "info")
            return redirect(url_for("management.plugins"))

        plugin.upgrade_settings()
        flash(_("Plugin settings have been upgraded."), "success")
        return redirect(url_for("management.plugins"))


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    management = Blueprint("management", __name__)

    @management.before_request
    def check_fresh_login():
        """Checks if the login is fresh for the current user, otherwise the user
        has to reauthenticate."""
        if not login_fresh():
            return current_app.login_manager.needs_refresh()

    # Attachments
    register_view(
        management,
        routes=["/attachments/cleanup"],
        view_func=CleanupAttachments.as_view("cleanup_attachments"),
    )
    register_view(
        management,
        routes=["/attachments/purge"],
        view_func=PurgeAttachments.as_view("purge_attachments"),
    )
    register_view(
        management,
        routes=["/attachments/delete", "/attachments/<int:attachment_id>/delete"],
        view_func=DeleteAttachment.as_view("delete_attachment"),
    )
    register_view(
        management,
        routes=["/attachments"],
        view_func=ManageAttachments.as_view("attachments"),
    )

    # Categories
    register_view(
        management,
        routes=["/category/add"],
        view_func=AddCategory.as_view("add_category"),
    )
    register_view(
        management,
        routes=["/category/<int:category_id>/delete"],
        view_func=DeleteCategory.as_view("delete_category"),
    )
    register_view(
        management,
        routes=["/category/<int:category_id>/edit"],
        view_func=EditCategory.as_view("edit_category"),
    )

    # Forums
    register_view(
        management,
        routes=["/forums/add", "/forums/<int:category_id>/add"],
        view_func=AddForum.as_view("add_forum"),
    )
    register_view(
        management,
        routes=["/forums/<int:forum_id>/delete"],
        view_func=DeleteForum.as_view("delete_forum"),
    )
    register_view(
        management,
        routes=["/forums/<int:forum_id>/edit"],
        view_func=EditForum.as_view("edit_forum"),
    )
    register_view(management, routes=["/forums"], view_func=Forums.as_view("forums"))

    # Groups
    register_view(
        management, routes=["/groups/add"], view_func=AddGroup.as_view("add_group")
    )
    register_view(
        management,
        routes=["/groups/<int:group_id>/delete", "/groups/delete"],
        view_func=DeleteGroup.as_view("delete_group"),
    )
    register_view(
        management,
        routes=["/groups/<int:group_id>/edit"],
        view_func=EditGroup.as_view("edit_group"),
    )
    register_view(management, routes=["/groups"], view_func=Groups.as_view("groups"))

    # Plugins
    register_view(
        management,
        routes=["/plugins/<path:name>/disable"],
        view_func=DisablePlugin.as_view("disable_plugin"),
    )
    register_view(
        management,
        routes=["/plugins/<path:name>/enable"],
        view_func=EnablePlugin.as_view("enable_plugin"),
    )
    register_view(
        management,
        routes=["/plugins/<path:name>/install"],
        view_func=InstallPlugin.as_view("install_plugin"),
    )
    register_view(
        management,
        routes=["/plugins/<path:name>/uninstall"],
        view_func=UninstallPlugin.as_view("uninstall_plugin"),
    )
    register_view(
        management,
        routes=["/plugins/<path:name>/upgrade"],
        view_func=UpgradePlugin.as_view("upgrade_plugin"),
    )
    register_view(
        management, routes=["/plugins"], view_func=PluginsView.as_view("plugins")
    )

    # Reports
    register_view(
        management,
        routes=["/reports/<int:report_id>/delete", "/reports/delete"],
        view_func=DeleteReport.as_view("delete_report"),
    )
    register_view(
        management,
        routes=["/reports/<int:report_id>/markread", "/reports/markread"],
        view_func=MarkReportRead.as_view("report_markread"),
    )
    register_view(
        management,
        routes=["/reports/unread"],
        view_func=UnreadReports.as_view("unread_reports"),
    )
    register_view(management, routes=["/reports"], view_func=Reports.as_view("reports"))

    # Settings
    register_view(
        management,
        routes=["/settings", "/settings/<path:slug>", "/settings/plugin/<path:plugin>"],
        view_func=ManagementSettings.as_view("settings"),
    )

    # Users
    register_view(
        management, routes=["/users/add"], view_func=AddUser.as_view("add_user")
    )
    register_view(
        management,
        routes=["/users/banned"],
        view_func=BannedUsers.as_view("banned_users"),
    )
    register_view(
        management,
        routes=["/users/ban", "/users/<int:user_id>/ban"],
        view_func=BanUser.as_view("ban_user"),
    )
    register_view(
        management,
        routes=["/users/delete", "/users/<int:user_id>/delete"],
        view_func=DeleteUser.as_view("delete_user"),
    )
    register_view(
        management,
        routes=["/users/<int:user_id>/delete_posts"],
        view_func=DeleteUserPosts.as_view("delete_user_posts"),
    )
    register_view(
        management,
        routes=["/users/<int:user_id>/edit"],
        view_func=EditUser.as_view("edit_user"),
    )
    register_view(
        management,
        routes=["/users/unban", "/users/<int:user_id>/unban"],
        view_func=UnbanUser.as_view("unban_user"),
    )
    register_view(management, routes=["/users"], view_func=ManageUsers.as_view("users"))
    register_view(
        management,
        routes=["/celerystatus"],
        view_func=CeleryStatus.as_view("celery_status"),
    )
    register_view(
        management, routes=["/"], view_func=ManagementOverview.as_view("overview")
    )

    app.register_blueprint(management, url_prefix=app.config["ADMIN_URL_PREFIX"])
