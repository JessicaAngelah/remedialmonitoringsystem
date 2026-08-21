"""
Remedial Monitoring System — Python/Flask port
Run with:  python app.py
Then open: http://127.0.0.1:5000

App setup only — each page lives in its own module under views/,
and all seed data + helpers live in data.py.
"""
from flask import Flask, redirect, request, session, url_for
import os

from data import fmt_date, fmt_money, grouped_number, initials, task_of
from views.auth import auth_bp
from views.core import core_bp
from views.dashboard import dashboard_bp
from views.projects import projects_bp
from views.tasks import tasks_bp
from views.calendar import calendar_bp
from views.gantt import gantt_bp
from views.team import team_bp
from views.reports import reports_bp
from views.settings import settings_bp
from views.history import history_bp
from views.admin import admin_bp

app = Flask(__name__)
app.secret_key = "remedial-monitoring-system-demo-secret"

# Flask's default static-file caching is aggressive (long max-age), so
# browsers can go on serving a stale cached copy of style.css/xl-grid.js
# indefinitely after a deploy, even past a normal reload — only a hard
# refresh (or clearing the cache) would ever pick up the new file. Turn
# that off so every deploy actually reaches users' browsers.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

app.jinja_env.filters["fmt_date"] = fmt_date
app.jinja_env.filters["fmt_money"] = fmt_money
app.jinja_env.filters["grouped_number"] = grouped_number
app.jinja_env.filters["initials"] = initials


def static_v(filename):
    """url_for('static', ...) but with a ?v=<file mtime> query string, so
    the URL itself changes whenever the file on disk changes. Turning off
    SEND_FILE_MAX_AGE_DEFAULT only affects new requests — browsers that
    already cached style.css/xl-grid.js under the old far-future expiry
    won't re-request them on their own. Changing the URL sidesteps that:
    a different URL is always a cache miss, no matter what headers the
    old cached response had."""
    path = os.path.join(app.static_folder, filename)
    try:
        v = int(os.path.getmtime(path))
    except OSError:
        v = 0
    return url_for("static", filename=filename, v=v)


app.jinja_env.globals["static_v"] = static_v


def activity_url(entry):
    """Where clicking an activity/history row (dashboard's Recent Activity
    card, or the full History page) should go. An explicit `url` on the
    entry always wins (set for events like bulk imports that don't map to
    one task/project); otherwise a task takes priority over a project
    since it's the more specific target, and the task must still exist
    (it could have since been deleted). Falls back to None — a plain,
    unlinked row — when there's nowhere sensible to send someone."""
    if entry.get("url"):
        return entry["url"]
    tid = entry.get("taskId")
    if tid and task_of(tid):
        return url_for("tasks.task_detail", tid=tid)
    pid = entry.get("projectId")
    if pid:
        return url_for("projects.project_detail", pid=pid)
    return None


app.jinja_env.globals["activity_url"] = activity_url

app.register_blueprint(auth_bp)
app.register_blueprint(core_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(gantt_bp)
app.register_blueprint(team_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(history_bp)
app.register_blueprint(admin_bp)

# Every page needs a signed-in session except the login form itself and
# static assets (css/js) — everything else redirects to /login if the
# session hasn't been through views.auth.login yet.
_PUBLIC_ENDPOINTS = {"auth.login", "auth.logout", "static"}


@app.before_request
def require_login():
    if request.endpoint in _PUBLIC_ENDPOINTS:
        return
    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.full_path if request.query_string else request.path))

if __name__ == "__main__":
    app.run(debug=True)
