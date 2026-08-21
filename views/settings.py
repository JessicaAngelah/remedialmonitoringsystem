"""Settings page — demo role switcher and appearance/language prefs."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from data import STAFF, T
from views.core import prefs

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("")
def settings_view():
    return render_template("settings.html", view="settings")


@settings_bp.post("/lang")
def settings_set_lang():
    lang = request.form.get("lang", "en")
    if lang in T:
        prefs()["lang"] = lang
    return redirect(url_for("settings.settings_view"))


@settings_bp.post("/role")
def set_role():
    role = request.form.get("role", "Administrator")
    if role in ("Administrator", "Manager", "Staff"):
        prefs()["role"] = role
        flash(f"Role switched to {role}")
    return redirect(url_for("settings.settings_view"))


@settings_bp.post("/staff-name")
def set_staff_name():
    name = request.form.get("staff_name", STAFF[0])
    if name in STAFF:
        prefs()["staff_name"] = name
        flash(f"Now signed in as {name}")
    return redirect(url_for("settings.settings_view"))
