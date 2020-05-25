# -*- coding: utf-8 -*-
"""
    flaskbb.management.views
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module handles the management views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
import sys

from celery import __version__ as celery_version
from flask import __version__ as flask_version
from flask import (Blueprint, current_app, flash, jsonify, redirect, request,
                   url_for)
from flask.views import MethodView
from flask_allows import Not, Permission
from flask_babelplus import gettext as _
from flask_login import current_user, login_fresh
from pluggy import HookimplMarker

from flaskbb import __version__ as flaskbb_version
from flaskbb.extensions import allows, celery, db
from flaskbb.forum.forms import UserSearchForm
from flaskbb.forum.models import Category, Forum, Post, Report, Topic
from flaskbb.management.forms import (AddForumForm, AddGroupForm, AddUserForm,
                                      CategoryForm, EditForumForm,
                                      EditGroupForm, EditUserForm)
from flaskbb.management.models import Setting, SettingsGroup
from flaskbb.plugins.models import PluginRegistry, PluginStore
from flaskbb.plugins.utils import validate_plugin
from flaskbb.user.models import Group, Guest, User
from flaskbb.utils.forms import populate_settings_dict, populate_settings_form
from flaskbb.utils.helpers import (get_online_users, register_view,
                                   render_template, time_diff, time_utcnow,
                                   FlashAndRedirect)
from flaskbb.utils.requirements import (CanBanUser, CanEditUser, IsAdmin,
                                        IsAtleastModerator,
                                        IsAtleastSuperModerator)
from flaskbb.utils.settings import flaskbb_config

impl = HookimplMarker('flaskbb')

logger = logging.getLogger(__name__)


class ManagementSettings(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the management settings"),  # noqa
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def _determine_active_settings(self, slug, plugin):
        """Determines which settings are active.
        Returns a tuple in following order:
            ``form``, ``old_settings``, ``plugin_obj``, ``active_nav``
        """
        # Any ideas how to do this better?
        slug = slug if slug else 'general'
        active_nav = {}  # used to build the navigation
        plugin_obj = None
        if plugin is not None:
            plugin_obj = PluginRegistry.query.filter_by(name=plugin
                                                        ).first_or_404()
            active_nav.update(
                {
                    'key': plugin_obj.name,
                    'title': plugin_obj.name.title()
                }
            )
            form = plugin_obj.get_settings_form()
            old_settings = plugin_obj.settings

        elif slug is not None:
            group_obj = SettingsGroup.query.filter_by(key=slug).first_or_404()
            active_nav.update({'key': group_obj.key, 'title': group_obj.name})
            form = Setting.get_form(group_obj)()
            old_settings = Setting.get_settings(group_obj)

        return form, old_settings, plugin_obj, active_nav

    def get(self, slug=None, plugin=None):
        form, old_settings, plugin_obj, active_nav = \
            self._determine_active_settings(slug, plugin)

        # get all groups and plugins - used to build the navigation
        all_groups = SettingsGroup.query.all()
        all_plugins = PluginRegistry.query.filter(db.and_(
            PluginRegistry.values != None,
            PluginRegistry.enabled == True
        )).all()
        form = populate_settings_form(form, old_settings)

        return render_template(
            "management/settings.html",
            form=form,
            all_groups=all_groups,
            all_plugins=all_plugins,
            active_nav=active_nav
        )

    def post(self, slug=None, plugin=None):
        form, old_settings, plugin_obj, active_nav = \
            self._determine_active_settings(slug, plugin)
        all_groups = SettingsGroup.query.all()
        all_plugins = PluginRegistry.query.filter(db.and_(
            PluginRegistry.values != None,
            PluginRegistry.enabled == True
        )).all()

        if form.validate_on_submit():
            new_settings = populate_settings_dict(form, old_settings)

            if plugin_obj is not None:
                plugin_obj.update_settings(new_settings)
            else:
                Setting.update(settings=new_settings)

            flash(_("Settings saved."), "success")

        return render_template(
            "management/settings.html",
            form=form,
            all_groups=all_groups,
            all_plugins=all_plugins,
            active_nav=active_nav
        )


class ManageUsers(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = UserSearchForm

    def get(self):
        page = request.args.get('page', 1, type=int)
        form = self.form()

        users = User.query.order_by(User.id.asc()).paginate(
            page, flaskbb_config['USERS_PER_PAGE'], False
        )

        return render_template(
            'management/users.html', users=users, search_form=form
        )

    def post(self):
        page = request.args.get('page', 1, type=int)
        form = self.form()

        if form.validate():
            users = form.get_results().\
                paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
            return render_template(
                'management/users.html', users=users, search_form=form
            )

        users = User.query.order_by(User.id.asc()).paginate(
            page, flaskbb_config['USERS_PER_PAGE'], False
        )

        return render_template(
            'management/users.html', users=users, search_form=form
        )


class EditUser(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator, CanEditUser,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )

        )
    ]
    form = EditUserForm

    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first_or_404()
        form = self.form(user)
        member_group = db.and_(
            * [
                db.not_(getattr(Group, p))
                for p in ['admin', 'mod', 'super_mod', 'banned', 'guest']
            ]
        )

        filt = db.or_(
            Group.id.in_(g.id for g in current_user.groups), member_group
        )

        if Permission(IsAtleastSuperModerator, identity=current_user):
            filt = db.or_(filt, Group.mod)

        if Permission(IsAdmin, identity=current_user):
            filt = db.or_(filt, Group.admin, Group.super_mod)

        if Permission(CanBanUser, identity=current_user):
            filt = db.or_(filt, Group.banned)

        group_query = Group.query.filter(filt)

        form.primary_group.query = group_query
        form.secondary_groups.query = group_query

        return render_template(
            'management/user_form.html', form=form, title=_('Edit User')
        )

    def post(self, user_id):
        user = User.query.filter_by(id=user_id).first_or_404()

        member_group = db.and_(
            * [
                db.not_(getattr(Group, p))
                for p in ['admin', 'mod', 'super_mod', 'banned', 'guest']
            ]
        )

        filt = db.or_(
            Group.id.in_(g.id for g in current_user.groups), member_group
        )

        if Permission(IsAtleastSuperModerator, identity=current_user):
            filt = db.or_(filt, Group.mod)

        if Permission(IsAdmin, identity=current_user):
            filt = db.or_(filt, Group.admin, Group.super_mod)

        if Permission(CanBanUser, identity=current_user):
            filt = db.or_(filt, Group.banned)

        group_query = Group.query.filter(filt)

        form = EditUserForm(user)
        form.primary_group.query = group_query
        form.secondary_groups.query = group_query
        if form.validate_on_submit():
            form.populate_obj(user)
            user.primary_group_id = form.primary_group.data.id

            # Don't override the password
            if form.password.data:
                user.password = form.password.data

            user.save(groups=form.secondary_groups.data)

            flash(_('User updated.'), 'success')
            return redirect(url_for('management.edit_user', user_id=user.id))

        return render_template(
            'management/user_form.html', form=form, title=_('Edit User')
        )


class DeleteUser(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, user_id=None):
        # ajax request
        if request.is_xhr:
            ids = request.get_json()["ids"]

            data = []
            for user in User.query.filter(User.id.in_(ids)).all():
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
                            "reverse_url": None
                        }
                    )

            return jsonify(
                message="{} users deleted.".format(len(data)),
                category="success",
                data=data,
                status=200
            )

        user = User.query.filter_by(id=user_id).first_or_404()

        if current_user.id == user.id:
            flash(_("You cannot delete yourself.", "danger"))
            return redirect(url_for("management.users"))

        user.delete()
        flash(_("User deleted."), "success")
        return redirect(url_for("management.users"))


class AddUser(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = AddUserForm

    def get(self):
        return render_template(
            'management/user_form.html', form=self.form(), title=_('Add User')
        )

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            form.save()
            flash(_('User added.'), 'success')
            return redirect(url_for('management.users'))

        return render_template(
            'management/user_form.html', form=form, title=_('Add User')
        )


class BannedUsers(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = UserSearchForm

    def get(self):
        page = request.args.get('page', 1, type=int)
        search_form = self.form()

        users = User.query.filter(
            Group.banned == True, Group.id == User.primary_group_id
        ).paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

        return render_template(
            'management/banned_users.html',
            users=users,
            search_form=search_form
        )

    def post(self):
        page = request.args.get('page', 1, type=int)
        search_form = self.form()

        users = User.query.filter(
            Group.banned == True, Group.id == User.primary_group_id
        ).paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

        if search_form.validate():
            users = search_form.get_results().\
                paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

            return render_template(
                'management/banned_users.html',
                users=users,
                search_form=search_form
            )

        return render_template(
            'management/banned_users.html',
            users=users,
            search_form=search_form
        )


class BanUser(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, user_id=None):
        if not Permission(CanBanUser, identity=current_user):
            flash(
                _("You do not have the permissions to ban this user."),
                "danger"
            )
            return redirect(url_for("management.overview"))

        # ajax request
        if request.is_xhr:
            ids = request.get_json()["ids"]

            data = []
            users = User.query.filter(User.id.in_(ids)).all()
            for user in users:
                # don't let a user ban himself and do not allow a moderator
                # to ban a admin user
                if (current_user.id == user.id or
                        Permission(IsAdmin, identity=user) and
                        Permission(Not(IsAdmin), current_user)):
                    continue

                elif user.ban():
                    data.append(
                        {
                            "id":
                            user.id,
                            "type":
                            "ban",
                            "reverse":
                            "unban",
                            "reverse_name":
                            _("Unban"),
                            "reverse_url":
                            url_for("management.unban_user", user_id=user.id)
                        }
                    )

            return jsonify(
                message="{} users banned.".format(len(data)),
                category="success",
                data=data,
                status=200
            )

        user = User.query.filter_by(id=user_id).first_or_404()
        # Do not allow moderators to ban admins
        if Permission(IsAdmin, identity=user) and Permission(
                Not(IsAdmin), identity=current_user):
            flash(_("A moderator cannot ban an admin user."), "danger")
            return redirect(url_for("management.overview"))

        if not current_user.id == user.id and user.ban():
            flash(_("User is now banned."), "success")
        else:
            flash(_("Could not ban user."), "danger")
        return redirect(url_for("management.banned_users"))


class UnbanUser(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to manage users"),
                level="danger",
                endpoint="management.overview"
            )

        )
    ]

    def post(self, user_id=None):

        if not Permission(CanBanUser, identity=current_user):
            flash(
                _("You do not have the permissions to unban this user."),
                "danger"
            )
            return redirect(url_for("management.overview"))

        # ajax request
        if request.is_xhr:
            ids = request.get_json()["ids"]

            data = []
            for user in User.query.filter(User.id.in_(ids)).all():
                if user.unban():
                    data.append(
                        {
                            "id": user.id,
                            "type": "unban",
                            "reverse": "ban",
                            "reverse_name": _("Ban"),
                            "reverse_url": url_for("management.ban_user",
                                                   user_id=user.id)
                        }
                    )

            return jsonify(
                message="{} users unbanned.".format(len(data)),
                category="success",
                data=data,
                status=200
            )

        user = User.query.filter_by(id=user_id).first_or_404()

        if user.unban():
            flash(_("User is now unbanned."), "success")
        else:
            flash(_("Could not unban user."), "danger")

        return redirect(url_for("management.banned_users"))


class Groups(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def get(self):

        page = request.args.get("page", 1, type=int)

        groups = Group.query.\
            order_by(Group.id.asc()).\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

        return render_template("management/groups.html", groups=groups)


class AddGroup(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = AddGroupForm

    def get(self):
        return render_template(
            'management/group_form.html',
            form=self.form(),
            title=_('Add Group')
        )

    def post(self):
        form = AddGroupForm()
        if form.validate_on_submit():
            form.save()
            flash(_('Group added.'), 'success')
            return redirect(url_for('management.groups'))

        return render_template(
            'management/group_form.html', form=form, title=_('Add Group')
        )


class EditGroup(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = EditGroupForm

    def get(self, group_id):
        group = Group.query.filter_by(id=group_id).first_or_404()
        form = self.form(group)
        return render_template(
            'management/group_form.html', form=form, title=_('Edit Group')
        )

    def post(self, group_id):
        group = Group.query.filter_by(id=group_id).first_or_404()
        form = EditGroupForm(group)

        if form.validate_on_submit():
            form.populate_obj(group)
            group.save()

            if group.guest:
                Guest.invalidate_cache()

            flash(_('Group updated.'), 'success')
            return redirect(url_for('management.groups', group_id=group.id))

        return render_template(
            'management/group_form.html', form=form, title=_('Edit Group')
        )


class DeleteGroup(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify groups."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, group_id=None):
        if request.is_xhr:
            ids = request.get_json()["ids"]
            # TODO: Get rid of magic numbers
            if not (set(ids) & set(["1", "2", "3", "4", "5", "6"])):
                data = []
                for group in Group.query.filter(Group.id.in_(ids)).all():
                    group.delete()
                    data.append(
                        {
                            "id": group.id,
                            "type": "delete",
                            "reverse": False,
                            "reverse_name": None,
                            "reverse_url": None
                        }
                    )

                return jsonify(
                    message="{} groups deleted.".format(len(data)),
                    category="success",
                    data=data,
                    status=200
                )
            return jsonify(
                message=_("You cannot delete one of the standard groups."),
                category="danger",
                data=None,
                status=404
            )

        if group_id is not None:
            if group_id <= 6:  # there are 6 standard groups
                flash(
                    _(
                        "You cannot delete the standard groups. "
                        "Try renaming it instead.", "danger"
                    )
                )
                return redirect(url_for("management.groups"))

            group = Group.query.filter_by(id=group_id).first_or_404()
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
                endpoint="management.overview"
            )
        )
    ]

    def get(self):
        categories = Category.query.order_by(Category.position.asc()).all()
        return render_template("management/forums.html", categories=categories)


class EditForum(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = EditForumForm

    def get(self, forum_id):
        forum = Forum.query.filter_by(id=forum_id).first_or_404()

        form = self.form(forum)

        if forum.moderators:
            form.moderators.data = ','.join(
                [user.username for user in forum.moderators]
            )
        else:
            form.moderators.data = None

        return render_template(
            'management/forum_form.html', form=form, title=_('Edit Forum')
        )

    def post(self, forum_id):
        forum = Forum.query.filter_by(id=forum_id).first_or_404()

        form = self.form(forum)
        if form.validate_on_submit():
            form.save()
            flash(_('Forum updated.'), 'success')
            return redirect(url_for('management.edit_forum',
                                    forum_id=forum.id))
        else:
            if forum.moderators:
                form.moderators.data = ','.join(
                    [user.username for user in forum.moderators]
                )
            else:
                form.moderators.data = None

        return render_template(
            'management/forum_form.html', form=form, title=_('Edit Forum')
        )


class AddForum(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = AddForumForm

    def get(self, category_id=None):
        form = self.form()

        form.groups.data = Group.query.order_by(Group.id.asc()).all()

        if category_id:
            category = Category.query.filter_by(id=category_id).first()
            form.category.data = category

        return render_template(
            'management/forum_form.html', form=form, title=_('Add Forum')
        )

    def post(self, category_id=None):
        form = self.form()

        if form.validate_on_submit():
            form.save()
            flash(_('Forum added.'), 'success')
            return redirect(url_for('management.forums'))
        else:
            form.groups.data = Group.query.order_by(Group.id.asc()).all()
            if category_id:
                category = Category.query.filter_by(id=category_id).first()
                form.category.data = category

        return render_template(
            'management/forum_form.html', form=form, title=_('Add Forum')
        )


class DeleteForum(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify forums"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, forum_id):
        forum = Forum.query.filter_by(id=forum_id).first_or_404()

        involved_users = User.query.filter(
            Topic.forum_id == forum.id, Post.user_id == User.id
        ).all()

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
                endpoint="management.overview"
            )
        )
    ]
    form = CategoryForm

    def get(self):
        return render_template(
            'management/category_form.html',
            form=self.form(),
            title=_('Add Category')
        )

    def post(self):
        form = self.form()

        if form.validate_on_submit():
            form.save()
            flash(_('Category added.'), 'success')
            return redirect(url_for('management.forums'))

        return render_template(
            'management/category_form.html', form=form, title=_('Add Category')
        )


class EditCategory(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify categories"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]
    form = CategoryForm

    def get(self, category_id):
        category = Category.query.filter_by(id=category_id).first_or_404()

        form = self.form(obj=category)

        return render_template(
            'management/category_form.html',
            form=form,
            title=_('Edit Category')
        )

    def post(self, category_id):
        category = Category.query.filter_by(id=category_id).first_or_404()

        form = self.form(obj=category)

        if form.validate_on_submit():
            form.populate_obj(category)
            flash(_('Category updated.'), 'success')
            category.save()

        return render_template(
            'management/category_form.html',
            form=form,
            title=_('Edit Category')
        )


class DeleteCategory(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify categories"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, category_id):
        category = Category.query.filter_by(id=category_id).first_or_404()

        involved_users = User.query.filter(
            Forum.category_id == category.id, Topic.forum_id == Forum.id,
            Post.user_id == User.id
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
                endpoint="management.overview"
            )
        )
    ]

    def get(self):
        page = request.args.get("page", 1, type=int)
        reports = Report.query.\
            order_by(Report.id.asc()).\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

        return render_template("management/reports.html", reports=reports)


class UnreadReports(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def get(self):
        page = request.args.get("page", 1, type=int)
        reports = Report.query.\
            filter(Report.zapped == None).\
            order_by(Report.id.desc()).\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

        return render_template("management/reports.html", reports=reports)


class MarkReportRead(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, report_id=None):

        # AJAX request
        if request.is_xhr:
            ids = request.get_json()["ids"]
            data = []

            for report in Report.query.filter(Report.id.in_(ids)).all():
                report.zapped_by = current_user.id
                report.zapped = time_utcnow()
                report.save()
                data.append(
                    {
                        "id": report.id,
                        "type": "read",
                        "reverse": False,
                        "reverse_name": None,
                        "reverse_url": None
                    }
                )

            return jsonify(
                message="{} reports marked as read.".format(len(data)),
                category="success",
                data=data,
                status=200
            )

        # mark single report as read
        if report_id:
            report = Report.query.filter_by(id=report_id).first_or_404()
            if report.zapped:
                flash(
                    _("Report %(id)s is already marked as read.", id=report.id),
                    "success"
                )
                return redirect(url_for("management.reports"))

            report.zapped_by = current_user.id
            report.zapped = time_utcnow()
            report.save()
            flash(_("Report %(id)s marked as read.", id=report.id), "success")
            return redirect(url_for("management.reports"))

        # mark all as read
        reports = Report.query.filter(Report.zapped == None).all()
        report_list = []
        for report in reports:
            report.zapped_by = current_user.id
            report.zapped = time_utcnow()
            report_list.append(report)

        db.session.add_all(report_list)
        db.session.commit()

        flash(_("All reports were marked as read."), "success")
        return redirect(url_for("management.reports"))


class DeleteReport(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to view reports."),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, report_id=None):

        if request.is_xhr:
            ids = request.get_json()["ids"]
            data = []

            for report in Report.query.filter(Report.id.in_(ids)).all():
                if report.delete():
                    data.append(
                        {
                            "id": report.id,
                            "type": "delete",
                            "reverse": False,
                            "reverse_name": None,
                            "reverse_url": None
                        }
                    )

            return jsonify(
                message="{} reports deleted.".format(len(data)),
                category="success",
                data=data,
                status=200
            )

        report = Report.query.filter_by(id=report_id).first_or_404()
        report.delete()
        flash(_("Report deleted."), "success")
        return redirect(url_for("management.reports"))


class CeleryStatus(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the management settings"),  # noqa
                level="danger",
                endpoint="management.overview"
            )
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


class ManagementOverview(MethodView):
    decorators = [
        allows.requires(
            IsAtleastModerator,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the management panel"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        # user and group stats
        banned_users = User.query.filter(
            Group.banned == True, Group.id == User.primary_group_id
        ).count()
        if not current_app.config["REDIS_ENABLED"]:
            online_users = User.query.filter(User.lastseen >= time_diff()
                                             ).count()
        else:
            online_users = len(get_online_users())

        unread_reports = Report.query.\
            filter(Report.zapped == None).\
            order_by(Report.id.desc()).\
            count()

        python_version = "{}.{}.{}".format(
            sys.version_info[0], sys.version_info[1], sys.version_info[2]
        )

        stats = {
            "current_app": current_app,
            "unread_reports": unread_reports,
            # stats stats
            "all_users": User.query.count(),
            "banned_users": banned_users,
            "online_users": online_users,
            "all_groups": Group.query.count(),
            "report_count": Report.query.count(),
            "topic_count": Topic.query.count(),
            "post_count": Post.query.count(),
            # components
            "python_version": python_version,
            "celery_version": celery_version,
            "flask_version": flask_version,
            "flaskbb_version": flaskbb_version,
            # plugins
            "plugins": PluginRegistry.query.all()
        }

        return render_template("management/overview.html", **stats)


class PluginsView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def get(self):
        plugins = PluginRegistry.query.all()
        return render_template("management/plugins.html", plugins=plugins)


class EnablePlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, name):
        validate_plugin(name)
        plugin = PluginRegistry.query.filter_by(name=name).first_or_404()

        if plugin.enabled:
            flash(
                _("Plugin %(plugin)s is already enabled.", plugin=plugin.name),
                "info"
            )
            return redirect(url_for("management.plugins"))

        plugin.enabled = True
        plugin.save()

        flash(
            _(
                "Plugin %(plugin)s enabled. Please restart FlaskBB now.",
                plugin=plugin.name
            ), "success"
        )
        return redirect(url_for("management.plugins"))


class DisablePlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, name):
        validate_plugin(name)
        plugin = PluginRegistry.query.filter_by(name=name).first_or_404()

        if not plugin.enabled:
            flash(
                _("Plugin %(plugin)s is already disabled.", plugin=plugin.name),
                "info"
            )
            return redirect(url_for("management.plugins"))

        plugin.enabled = False
        plugin.save()
        flash(
            _(
                "Plugin %(plugin)s disabled. Please restart FlaskBB now.",
                plugin=plugin.name
            ), "success"
        )
        return redirect(url_for("management.plugins"))


class UninstallPlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, name):
        validate_plugin(name)
        plugin = PluginRegistry.query.filter_by(name=name).first_or_404()
        PluginStore.query.filter_by(plugin_id=plugin.id).delete()
        db.session.commit()
        flash(_("Plugin has been uninstalled."), "success")
        return redirect(url_for("management.plugins"))


class InstallPlugin(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to modify plugins"),
                level="danger",
                endpoint="management.overview"
            )
        )
    ]

    def post(self, name):
        plugin_module = validate_plugin(name)
        plugin = PluginRegistry.query.filter_by(name=name).first_or_404()

        if not plugin.enabled:
            flash(
                _(
                    "Can't install plugin. Enable '%(plugin)s' plugin first.",
                    plugin=plugin.name
                ), "danger"
            )
            return redirect(url_for("management.plugins"))

        plugin.add_settings(plugin_module.SETTINGS)
        flash(_("Plugin has been installed."), "success")
        return redirect(url_for("management.plugins"))


@impl(tryfirst=True)
def flaskbb_load_blueprints(app):
    management = Blueprint("management", __name__)

    @management.before_request
    def check_fresh_login():
        """Checks if the login is fresh for the current user, otherwise the user
        has to reauthenticate."""
        if not login_fresh():
            return current_app.login_manager.needs_refresh()

    # Categories
    register_view(
        management,
        routes=['/category/add'],
        view_func=AddCategory.as_view('add_category')
    )
    register_view(
        management,
        routes=["/category/<int:category_id>/delete"],
        view_func=DeleteCategory.as_view('delete_category')
    )
    register_view(
        management,
        routes=['/category/<int:category_id>/edit'],
        view_func=EditCategory.as_view('edit_category')
    )

    # Forums
    register_view(
        management,
        routes=['/forums/add', '/forums/<int:category_id>/add'],
        view_func=AddForum.as_view('add_forum')
    )
    register_view(
        management,
        routes=['/forums/<int:forum_id>/delete'],
        view_func=DeleteForum.as_view('delete_forum')
    )
    register_view(
        management,
        routes=['/forums/<int:forum_id>/edit'],
        view_func=EditForum.as_view('edit_forum')
    )
    register_view(
        management, routes=['/forums'], view_func=Forums.as_view('forums')
    )

    # Groups
    register_view(
        management,
        routes=['/groups/add'],
        view_func=AddGroup.as_view('add_group')
    )
    register_view(
        management,
        routes=['/groups/<int:group_id>/delete', '/groups/delete'],
        view_func=DeleteGroup.as_view('delete_group')
    )
    register_view(
        management,
        routes=['/groups/<int:group_id>/edit'],
        view_func=EditGroup.as_view('edit_group')
    )
    register_view(
        management, routes=['/groups'], view_func=Groups.as_view('groups')
    )

    # Plugins
    register_view(
        management,
        routes=['/plugins/<path:name>/disable'],
        view_func=DisablePlugin.as_view('disable_plugin')
    )
    register_view(
        management,
        routes=['/plugins/<path:name>/enable'],
        view_func=EnablePlugin.as_view('enable_plugin')
    )
    register_view(
        management,
        routes=['/plugins/<path:name>/install'],
        view_func=InstallPlugin.as_view('install_plugin')
    )
    register_view(
        management,
        routes=['/plugins/<path:name>/uninstall'],
        view_func=UninstallPlugin.as_view('uninstall_plugin')
    )
    register_view(
        management,
        routes=['/plugins'],
        view_func=PluginsView.as_view('plugins')
    )

    # Reports
    register_view(
        management,
        routes=['/reports/<int:report_id>/delete', '/reports/delete'],
        view_func=DeleteReport.as_view('delete_report')
    )
    register_view(
        management,
        routes=['/reports/<int:report_id>/markread', '/reports/markread'],
        view_func=MarkReportRead.as_view('report_markread')
    )
    register_view(
        management,
        routes=['/reports/unread'],
        view_func=UnreadReports.as_view('unread_reports')
    )
    register_view(
        management, routes=['/reports'], view_func=Reports.as_view('reports')
    )

    # Settings
    register_view(
        management,
        routes=[
            '/settings', '/settings/<path:slug>',
            '/settings/plugin/<path:plugin>'
        ],
        view_func=ManagementSettings.as_view('settings')
    )

    # Users
    register_view(
        management,
        routes=['/users/add'],
        view_func=AddUser.as_view('add_user')
    )
    register_view(
        management,
        routes=['/users/banned'],
        view_func=BannedUsers.as_view('banned_users')
    )
    register_view(
        management,
        routes=['/users/ban', '/users/<int:user_id>/ban'],
        view_func=BanUser.as_view('ban_user')
    )
    register_view(
        management,
        routes=['/users/delete', '/users/<int:user_id>/delete'],
        view_func=DeleteUser.as_view('delete_user')
    )
    register_view(
        management,
        routes=['/users/<int:user_id>/edit'],
        view_func=EditUser.as_view('edit_user')
    )
    register_view(
        management,
        routes=['/users/unban', '/users/<int:user_id>/unban'],
        view_func=UnbanUser.as_view('unban_user')
    )
    register_view(
        management, routes=['/users'], view_func=ManageUsers.as_view('users')
    )
    register_view(
        management,
        routes=['/celerystatus'],
        view_func=CeleryStatus.as_view('celery_status')
    )
    register_view(
        management,
        routes=['/'],
        view_func=ManagementOverview.as_view('overview')
    )

    app.register_blueprint(
        management, url_prefix=app.config["ADMIN_URL_PREFIX"]
    )
