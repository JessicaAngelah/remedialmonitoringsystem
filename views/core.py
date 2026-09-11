"""
Core blueprint — the landing redirect, dark-mode/language/sidebar toggles,
and the context processor that injects sidebar/nav/i18n data into every
template (equivalent to the top-level state in the original App.jsx).
"""
from flask import Blueprint, redirect, request, session, url_for

from data import (
    BUILTIN_FOLDERS, CRITICAL_OPTIONS, CUSTOM_FOLDERS, MEETING_STATUS_OPTIONS, NAV, NOTIFICATIONS,
    OBJEKTIF_OPTIONS, PROJECTS, PRIORITY_META, RATING_OPTIONS, STAFF, STATUS_META, STATUS_OPTIONS, T, TASKS,
    TIPE_OPTIONS, URGENCY_OPTIONS, assignable_people, known_surveyors,
)

core_bp = Blueprint("core", __name__)


def prefs():
    session.setdefault("dark", False)
    session.setdefault("lang", "en")
    session.setdefault("collapsed", False)
    # role/staff_name are set at login (views/auth.py); these defaults are
    # just a safety net and shouldn't normally be hit since app.py's
    # before_request sends anyone without a session to /login first.
    session.setdefault("role", "Administrator")
    session.setdefault("staff_name", STAFF[0])
    return session


def is_manager_or_admin():
    """Managers and Administrators can create/delete records; Staff can't."""
    return prefs()["role"] != "Staff"


def is_assigned_to_project(project, staff_name=None):
    """A Staff member counts as 'assigned' to a project if they're its
    PIC/collector, or have any task assigned to them within it. Used to
    scope the default Projects list to Staff's own cases and to gate
    project-edit access for them."""
    if not project:
        return False
    staff_name = staff_name or prefs()["staff_name"]
    if project.get("pic") == staff_name or project.get("collector") == staff_name:
        return True
    return any(tk["assignee"] == staff_name for tk in TASKS if tk["projectId"] == project["id"])


def can_edit_project(project):
    """Managers/Admins can edit any project; Staff can only edit projects
    they're assigned to (view-only otherwise, but they can still comment
    on its tasks)."""
    return is_manager_or_admin() or is_assigned_to_project(project)


def can_edit_task(task):
    """Managers/Admins can edit any task; Staff can only change status/
    progress/notes on tasks assigned to them (view-only otherwise, but
    they can still comment)."""
    if is_manager_or_admin():
        return True
    return bool(task) and task.get("assignee") == prefs()["staff_name"]


@core_bp.app_context_processor
def inject_globals():
    p = prefs()
    lang = p["lang"] if p["lang"] in T else "en"
    # A notification with no recipient is a broadcast (shown to everyone);
    # otherwise it's only shown to the person it was sent to.
    my_notifications = [
        n for n in NOTIFICATIONS
        if not n.get("recipient") or n["recipient"] == p["staff_name"]
    ]
    return {
        "dark": p["dark"],
        "lang": lang,
        "role": p["role"],
        "staff_name": p["staff_name"],
        "collapsed": p["collapsed"],
        "can_manage": p["role"] != "Staff",
        "can_admin": p["role"] == "Administrator",
        "can_edit_project": can_edit_project,
        "can_edit_task": can_edit_task,
        "t": T[lang],
        "NAV": NAV,
        "STATUS_META": STATUS_META,
        "PRIORITY_META": PRIORITY_META,
        "STAFF": STAFF,
        "ASSIGNEES": assignable_people(),
        "PROJECTS": PROJECTS,
        "CUSTOM_FOLDERS": CUSTOM_FOLDERS,
        "BUILTIN_FOLDERS": BUILTIN_FOLDERS,
        "URGENCY_OPTIONS": URGENCY_OPTIONS,
        "STATUS_OPTIONS": STATUS_OPTIONS,
        "TIPE_OPTIONS": TIPE_OPTIONS,
        "OBJEKTIF_OPTIONS": OBJEKTIF_OPTIONS,
        "MEETING_STATUS_OPTIONS": MEETING_STATUS_OPTIONS,
        "CRITICAL_OPTIONS": CRITICAL_OPTIONS,
        "RATING_OPTIONS": RATING_OPTIONS,
        "SURVEYORS": known_surveyors(),
        "notifications": my_notifications,
        "unread_count": len([n for n in my_notifications if not n["read"]]),
    }


@core_bp.route("/")
def index():
    return redirect(url_for("dashboard.dashboard"))


@core_bp.post("/toggle-dark")
def toggle_dark():
    p = prefs()
    p["dark"] = not p["dark"]
    return redirect(request.referrer or url_for("dashboard.dashboard"))


@core_bp.post("/toggle-lang")
def toggle_lang():
    p = prefs()
    p["lang"] = "id" if p["lang"] == "en" else "en"
    return redirect(request.referrer or url_for("dashboard.dashboard"))


@core_bp.post("/toggle-sidebar")
def toggle_sidebar():
    p = prefs()
    p["collapsed"] = not p["collapsed"]
    return redirect(request.referrer or url_for("dashboard.dashboard"))


# Notifications — same bell + panel is shown to every role, but each
# person only marks their own (broadcast + anything sent to them) as read.
@core_bp.post("/notifications/mark-all-read")
def mark_all_notifications_read():
    p = prefs()
    for n in NOTIFICATIONS:
        if not n.get("recipient") or n["recipient"] == p["staff_name"]:
            n["read"] = True
    return redirect(request.form.get("redirect_to") or request.referrer or url_for("dashboard.dashboard"))


@core_bp.post("/notifications/<nid>/read")
def mark_notification_read(nid):
    for n in NOTIFICATIONS:
        if n["id"] == nid:
            n["read"] = True
            break
    return redirect(request.form.get("redirect_to") or request.referrer or url_for("dashboard.dashboard"))
