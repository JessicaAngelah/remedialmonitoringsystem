"""Team page — workload and productivity per team member (Staff, plus
Managers/Administrators who also carry casework)."""
from flask import Blueprint, render_template

from data import TASKS, USERS, assignable_people, is_done, is_overdue, project_of

team_bp = Blueprint("team", __name__)


@team_bp.route("/team")
def team_view():
    role_of = {u["name"]: u["role"] for u in USERS}
    cards = []
    for name in assignable_people():
        mine = [tk for tk in TASKS if tk["assignee"] == name]
        done = len([tk for tk in mine if is_done(tk)])
        overdue = len([tk for tk in mine if is_overdue(tk)])
        active = len(mine) - done
        recent = [tk for tk in mine if not is_done(tk)][:4]
        cards.append({
            "name": name, "role": role_of.get(name, "Staff"),
            "total": len(mine), "done": done, "overdue": overdue,
            "active": active,
            "recent": [{"task": tk, "project": project_of(tk["projectId"])} for tk in recent],
        })
    return render_template("team.html", view="team", cards=cards)
