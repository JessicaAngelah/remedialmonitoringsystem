"""Calendar page — month grid with tasks plotted by due date, navigable
between months."""
import calendar as pycalendar
from datetime import date

from flask import Blueprint, render_template, request

from data import TASKS, TODAY, parse_date, project_of

calendar_bp = Blueprint("calendar", __name__)

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


@calendar_bp.route("/calendar")
def calendar_view():
    year = request.args.get("year", type=int, default=TODAY.year)
    month = request.args.get("month", type=int, default=TODAY.month)

    # Normalize in case of out-of-range navigation (e.g. month=13/0)
    if month > 12:
        year += (month - 1) // 12
        month = ((month - 1) % 12) + 1
    elif month < 1:
        year -= (-month) // 12 + 1
        month = 12 - ((-month) % 12)

    is_current_month = (year == TODAY.year and month == TODAY.month)
    default_day = TODAY.day if is_current_month else None
    selected_day = request.args.get("day", type=int, default=default_day)

    first_weekday = date(year, month, 1).weekday()  # Monday=0
    days_in_month = pycalendar.monthrange(year, month)[1]
    cells = [None] * first_weekday + list(range(1, days_in_month + 1))

    # Guard against an out-of-range day (e.g. jumping from the 31st of one
    # month into a shorter one via the date picker).
    if selected_day is not None and not (1 <= selected_day <= days_in_month):
        selected_day = min(max(selected_day, 1), days_in_month)

    def tasks_on(day):
        return [tk for tk in TASKS if parse_date(tk["dueDate"]) == date(year, month, day)]

    day_dots = {d: tasks_on(d)[:3] for d in range(1, days_in_month + 1)}
    selected_tasks = tasks_on(selected_day) if selected_day else []

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    return render_template(
        "calendar.html", view="calendar", cells=cells, day_dots=day_dots,
        selected_day=selected_day, selected_tasks=selected_tasks,
        project_of=project_of, year=year, month=month,
        month_label=f"{MONTH_NAMES[month - 1]} {year}",
        today_day=TODAY.day if is_current_month else None,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        MONTH_NAMES=MONTH_NAMES, days_in_month=days_in_month, today=TODAY,
    )
