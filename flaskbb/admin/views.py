# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from flaskbb.decorators import admin_required

admin = Blueprint("admin", __name__)

@admin.route("/")
@admin_required
def overview():
    return render_template("admin/overview.html")

@admin.route("/users")
@admin_required
def manage_users():
    pass

@admin.route("/posts")
@admin_required
def manage_posts():
    pass

@admin.route("/pages")
@admin_required
def manage_pages():
    pass
