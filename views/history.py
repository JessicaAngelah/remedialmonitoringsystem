"""History page — activity/audit log.

Manager and Administrator see every entry across all projects. Staff only
see entries where they are the actor (their own projects/tasks).
"""
from flask import Blueprint, render_template

from data import HISTORY, PROJECTS, project_of
from views.core import prefs

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history_view():
    p = prefs()
    role = p["role"]
    f_project = None
    from flask import request
    f_project = request.args.get("project", "all")

    if role == "Staff":
        entries = [h for h in HISTORY if h["actor"] == p["staff_name"]]
    else:
        entries = list(HISTORY)

    if f_project != "all":
        entries = [h for h in entries if h.get("projectId") == f_project]

    rows = [{"entry": h, "project": project_of(h["projectId"]) if h.get("projectId") else None} for h in entries]

    return render_template(
        "history.html", view="history", rows=rows, f_project=f_project,
        projects=PROJECTS, is_own=(role == "Staff"),
    )
