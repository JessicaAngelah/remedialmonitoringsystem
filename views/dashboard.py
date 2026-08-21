"""Dashboard page — KPIs, alerts, project progress, activity feed, and the
Task Status / per-staff (or per-priority, for Staff) charts."""
import math

from flask import Blueprint, render_template, request

from data import (
    ACTIVITY, PRIORITY_META, PROJECTS, STAFF, TASKS, TODAY,
    assignable_people, days_between, is_done, is_due_today, is_overdue, parse_date, project_of,
)
from views.core import is_assigned_to_project, prefs

dashboard_bp = Blueprint("dashboard", __name__)

# Derived task-status buckets used by the donut + per-staff charts.
# "Overdue" wins over status field; "Completed" folds in cancelled tasks.
# Colors picked for contrast against thin bar segments (small color swatches
# read much less saturated than large ones), so these are punchier than the
# muted tones used elsewhere in the app.
STATUS_CATEGORIES = [
    ("Completed", "#00FFA6"),
    ("In Progress", "#004BFF"),
    ("Pending", "#D6C100"),
    ("Overdue", "#FF003C"),
]

PRIORITY_COLORS = {"low": "#00FFA6", "medium": "#004BFF", "high": "#D6C100", "critical": "#FF003C"}

DONUT_R = 70
DONUT_CIRCUMFERENCE = 2 * math.pi * DONUT_R


def _task_category(tk):
    if is_overdue(tk):
        return "Overdue"
    if tk["status"] in ("completed", "cancelled"):
        return "Completed"
    if tk["status"] == "pending":
        return "Pending"
    return "In Progress"


def _donut_segments(counts):
    """counts: list[(label, value, color)] -> stroke-dasharray/-offset per
    segment for an SVG ring drawn on a r=DONUT_R circle."""
    total = sum(v for _, v, _ in counts)
    segments = []
    offset = 0.0
    for label, value, color in counts:
        frac = (value / total) if total else 0
        raw = frac * DONUT_CIRCUMFERENCE
        gap = 3 if 0 < raw < DONUT_CIRCUMFERENCE else 0
        length = max(0, raw - gap)
        segments.append({
            "label": label, "value": value, "color": color,
            "dasharray": f"{length:.2f} {max(0, DONUT_CIRCUMFERENCE - length):.2f}",
            "dashoffset": f"{-offset:.2f}",
        })
        offset += raw
    return segments, total


@dashboard_bp.route("/dashboard")
def dashboard():
    p = prefs()
    is_staff = p["role"] == "Staff"

    overdue = [tk for tk in TASKS if is_overdue(tk)]
    due_today = [tk for tk in TASKS if is_due_today(tk)]
    if is_staff:
        my_name = p["staff_name"]
        overdue = [tk for tk in overdue if tk["assignee"] == my_name]
        due_today = [tk for tk in due_today if tk["assignee"] == my_name]
    done = len([tk for tk in TASKS if is_done(tk)])
    in_progress = len([tk for tk in TASKS if not is_done(tk) and not is_overdue(tk)])

    # ---- Task Status Distribution donut (own tasks for Staff, all for Manager/Admin)
    scope_tasks = [tk for tk in TASKS if tk["assignee"] == p["staff_name"]] if is_staff else TASKS
    cat_counts = {label: 0 for label, _ in STATUS_CATEGORIES}
    for tk in scope_tasks:
        cat_counts[_task_category(tk)] += 1
    donut_segments, donut_total = _donut_segments(
        [(label, cat_counts[label], color) for label, color in STATUS_CATEGORIES]
    )

    # ---- Manager/Admin: horizontal per-staff status breakdown, filterable
    staff_filter = request.args.get("staff", "all")
    by_staff = []
    for s in assignable_people():
        s_tasks = [tk for tk in TASKS if tk["assignee"] == s]
        s_counts = {label: 0 for label, _ in STATUS_CATEGORIES}
        for tk in s_tasks:
            s_counts[_task_category(tk)] += 1
        by_staff.append({
            "name": s, "total": len(s_tasks),
            "segments": [{"label": l, "value": s_counts[l], "color": c} for l, c in STATUS_CATEGORIES],
        })
    max_staff_total = max([1] + [s["total"] for s in by_staff])
    if staff_filter != "all":
        by_staff = [s for s in by_staff if s["name"] == staff_filter]

    # ---- Staff: "My Tasks by Priority" replaces the per-staff chart
    my_priority = []
    my_priority_total = 0
    if is_staff:
        pr_counts = {k: 0 for k in PRIORITY_META}
        for tk in scope_tasks:
            pr_counts[tk["priority"]] = pr_counts.get(tk["priority"], 0) + 1
        my_priority_total = sum(pr_counts.values())
        max_pr = max([1] + list(pr_counts.values()))
        for k, meta in PRIORITY_META.items():
            my_priority.append({
                "key": k, "label": meta["label"], "value": pr_counts.get(k, 0),
                "color": PRIORITY_COLORS.get(k, "#71808F"), "max": max_pr,
            })

    overdue_rows = []
    for tk in overdue:
        pr = project_of(tk["projectId"])
        days = days_between(TODAY, parse_date(tk["dueDate"]))
        overdue_rows.append({"task": tk, "project": pr, "days": days})

    project_progress = []
    for pj in PROJECTS:
        if is_staff and not is_assigned_to_project(pj, p["staff_name"]):
            continue
        pts = [tk for tk in TASKS if tk["projectId"] == pj["id"]]
        pdone = len([tk for tk in pts if is_done(tk)])
        pct = round((pdone / len(pts)) * 100) if pts else 0
        project_progress.append({
            "project": pj, "total": len(pts), "done": pdone, "pct": pct,
            "pinned": bool(pj.get("pinned")),
            "almost_done": pts and pct >= 80 and pct < 100,
        })
    # Pinned cases always lead; after that, cases closest to done surface
    # first so almost-finished work doesn't get buried by insertion order.
    project_progress.sort(key=lambda pp: (not pp["pinned"], -pp["pct"]))

    return render_template(
        "dashboard.html",
        view="dashboard",
        is_staff=is_staff,
        overdue_rows=overdue_rows,
        due_today=due_today,
        done=done,
        in_progress=in_progress,
        overdue_count=len(overdue),
        donut_segments=donut_segments,
        donut_total=donut_total,
        status_categories=STATUS_CATEGORIES,
        by_staff=by_staff,
        max_staff_total=max_staff_total,
        staff_filter=staff_filter,
        my_priority=my_priority,
        my_priority_total=my_priority_total,
        project_progress=project_progress,
        activity=ACTIVITY[:8],
        projects=PROJECTS,
    )
