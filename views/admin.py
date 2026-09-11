"""Admin page — user directory: add/remove accounts, view & change passwords.

Administrator-only. Every route re-checks the role server-side (not just the
hidden nav item) so a non-admin can't reach it by guessing the URL.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from data import USERS, next_user_id
from views.core import prefs

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    return prefs()["role"] == "Administrator"


@admin_bp.route("")
def admin_view():
    if not _require_admin():
        flash("Administrators only")
        return redirect(url_for("dashboard.dashboard"))
    modal = request.args.get("modal")
    return render_template("admin.html", view="admin", users=USERS, modal=modal)


@admin_bp.post("/new")
def new_user():
    if not _require_admin():
        flash("Administrators only")
        return redirect(url_for("dashboard.dashboard"))
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "Staff")
    if name and username and password and role in ("Administrator", "Manager", "Staff"):
        USERS.append({
            "id": next_user_id(), "name": name, "username": username,
            "password": password, "role": role,
        })
        flash("User added")
    return redirect(url_for("admin.admin_view"))


@admin_bp.post("/<uid>/delete")
def delete_user(uid):
    if not _require_admin():
        flash("Administrators only")
        return redirect(url_for("dashboard.dashboard"))
    USERS[:] = [u for u in USERS if u["id"] != uid]
    flash("User removed")
    return redirect(url_for("admin.admin_view"))


@admin_bp.post("/<uid>/update")
def update_user(uid):
    if not _require_admin():
        flash("Administrators only")
        return redirect(url_for("dashboard.dashboard"))
    username = request.form.get("username")
    role = request.form.get("role")
    for u in USERS:
        if u["id"] == uid:
            if username is not None and username.strip():
                u["username"] = username.strip()
            if role in ("Administrator", "Manager", "Staff"):
                u["role"] = role
            break
    flash("User updated")
    return redirect(url_for("admin.admin_view"))


@admin_bp.post("/<uid>/password")
def change_password(uid):
    if not _require_admin():
        flash("Administrators only")
        return redirect(url_for("dashboard.dashboard"))
    new_password = request.form.get("password", "").strip()
    if new_password:
        for u in USERS:
            if u["id"] == uid:
                u["password"] = new_password
                break
        flash("Password updated")
    return redirect(url_for("admin.admin_view"))
