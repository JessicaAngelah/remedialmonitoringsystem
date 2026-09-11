"""Gantt chart page — main-task timelines across the project window."""
import calendar as cal
from datetime import date, timedelta

from flask import Blueprint, render_template, request

from data import MAIN_TASKS, PROJECTS, TASKS, TODAY, is_done, parse_date, project_of

gantt_bp = Blueprint("gantt", __name__)

DAY_WIDTH = 16  # px per day of the scrollable track


@gantt_bp.route("/gantt")
def gantt_view():
    f_project = request.args.get("project", "all")

    # "All projects" shows one bar per main task (aggregated across its
    # subtasks) so the whole portfolio fits on screen. Selecting a single
    # project drills down to one bar per individual task instead, so its
    # actual task-by-task timeline is visible.
    all_dates = []
    task_spans = []  # (label, project, done, start, end)

    if f_project == "all":
        for m in MAIN_TASKS:
            mts = [tk for tk in TASKS if tk["mainTaskId"] == m["id"]]
            if not mts:
                continue
            dates = [parse_date(tk["dueDate"]) for tk in mts]
            start = min(dates) - timedelta(days=4)
            end = max(dates)
            p = project_of(m["projectId"])
            task_spans.append((m["title"], p, all(is_done(tk) for tk in mts), start, end))
            all_dates.append(start)
            all_dates.append(end)
    else:
        p = project_of(f_project)
        for tk in TASKS:
            if tk["projectId"] != f_project:
                continue
            start = parse_date(tk.get("startDate") or tk["dueDate"])
            end = parse_date(tk["dueDate"])
            if end < start:
                start, end = end, start
            task_spans.append((tk["title"], p, is_done(tk), start, end))
            all_dates.append(start)
            all_dates.append(end)

    range_start = min([TODAY - timedelta(days=45)] + all_dates)
    range_end = max([TODAY + timedelta(days=75)] + all_dates)
    # Snap to full months so the month bands line up cleanly.
    range_start = range_start.replace(day=1)
    last_day = cal.monthrange(range_end.year, range_end.month)[1]
    range_end = range_end.replace(day=last_day)

    total_days = (range_end - range_start).days
    today_pct = min(100, max(0, ((TODAY - range_start).days / total_days) * 100))

    # Month bands (alternating background shading + month label).
    months = []
    cursor = date(range_start.year, range_start.month, 1)
    while cursor <= range_end:
        last = cal.monthrange(cursor.year, cursor.month)[1]
        m_start = max(cursor, range_start)
        m_end = min(date(cursor.year, cursor.month, last), range_end)
        left = ((m_start - range_start).days / total_days) * 100
        width = (((m_end - m_start).days + 1) / total_days) * 100
        months.append({"label": cursor.strftime("%B %Y"), "left": left, "width": width})
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)

    # Weekly ticks for the date scale.
    ticks = []
    cursor = range_start
    while cursor <= range_end:
        ticks.append({"label": cursor.strftime("%d %b"), "left": ((cursor - range_start).days / total_days) * 100})
        cursor += timedelta(days=7)

    rows = []
    for title, p, done, start, end in task_spans:
        left_days = min(total_days, max(0, (start - range_start).days))
        end_days = min(total_days, max(left_days, (end - range_start).days))
        left = (left_days / total_days) * 100
        width = max(((end_days - left_days) / total_days) * 100, 3)
        width = min(width, 100 - left)  # never let the bar overshoot the track
        rows.append({
            "title": title, "project": p, "start": start, "end": end,
            "done": done,
            "left": left, "width": width,
        })

    track_width = total_days * DAY_WIDTH

    return render_template(
        "gantt.html", view="gantt", rows=rows, today_pct=today_pct,
        projects=PROJECTS, f_project=f_project, months=months, ticks=ticks,
        track_width=track_width, range_start=range_start, range_end=range_end,
        today_left_px=(today_pct / 100) * track_width,
    )
