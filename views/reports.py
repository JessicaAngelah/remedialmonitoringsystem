"""Reports page — cross-project summary, staff productivity, monthly trends, CSV export."""
import csv
import io
from collections import OrderedDict

from flask import Blueprint, Response, render_template

from data import PRIORITY_META, PROJECTS, STAFF, STATUS_META, TASKS, is_done, is_overdue, parse_date, project_of

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("")
def reports_view():
    done = len([tk for tk in TASKS if is_done(tk)])
    overdue = len([tk for tk in TASKS if is_overdue(tk)])
    progress_pct = round((done / len(TASKS)) * 100) if TASKS else 0

    by_project = []
    for p in PROJECTS:
        pts = [tk for tk in TASKS if tk["projectId"] == p["id"]]
        pdone = len([tk for tk in pts if is_done(tk)])
        povr = len([tk for tk in pts if is_overdue(tk)])
        pct = round((pdone / len(pts)) * 100) if pts else 0
        by_project.append({"project": p, "total": len(pts), "done": pdone, "overdue": povr, "pct": pct})

    # Staff Productivity Overview
    by_staff = []
    for name in STAFF:
        mine = [tk for tk in TASKS if tk["assignee"] == name]
        sdone = len([tk for tk in mine if is_done(tk)])
        sovr = len([tk for tk in mine if is_overdue(tk)])
        spct = round((sdone / len(mine)) * 100) if mine else 0
        by_staff.append({"name": name, "total": len(mine), "done": sdone, "overdue": sovr, "pct": spct})

    # Monthly Task Trends — tasks due per calendar month, split done vs open
    months = OrderedDict()
    for tk in TASKS:
        d = parse_date(tk["dueDate"])
        key = d.strftime("%Y-%m")
        label = d.strftime("%b %Y")
        bucket = months.setdefault(key, {"label": label, "total": 0, "done": 0})
        bucket["total"] += 1
        if is_done(tk):
            bucket["done"] += 1
    monthly_trends = list(months.values())
    max_month = max([1] + [m["total"] for m in monthly_trends])

    return render_template(
        "reports.html", view="reports", done=done, overdue=overdue,
        progress_pct=progress_pct, by_project=by_project, total_tasks=len(TASKS),
        by_staff=by_staff, monthly_trends=monthly_trends, max_month=max_month,
    )


@reports_bp.route("/export.csv")
def export_csv():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Title", "Project", "Assignee", "Status", "Priority", "Due date", "Type", "Comments"])
    for tk in TASKS:
        p = project_of(tk["projectId"])
        # Newest-first, one "Author: text" line per comment — same order
        # and format used on the task detail page and the per-project
        # Excel download, so a task's discussion travels with it here too.
        comments = sorted(tk.get("comments", []), key=lambda c: c["id"], reverse=True)
        comments_text = "\n".join(f"{c['author']}: {c['text']}" for c in comments)
        writer.writerow([
            tk["id"], tk["title"], p["name"] if p else "", tk["assignee"],
            STATUS_META[tk["status"]]["label"], PRIORITY_META[tk["priority"]]["label"],
            tk["dueDate"], tk["type"], comments_text,
        ])
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=remedial-tasks-report.csv"},
    )
