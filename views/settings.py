"""Settings page — appearance/language prefs."""
from flask import Blueprint, redirect, render_template, request, url_for

from data import T
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
