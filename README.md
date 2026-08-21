# Remedial Monitoring System (Python edition)

A Python/Flask port of the original React app. Same data, same views
(Dashboard, Projects, Tasks, Calendar, Gantt, Team, Reports, Settings),
server-rendered instead of client-side React.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

(On Windows, if `python` isn't on PATH, use `py app.py` instead.)

Then open **http://127.0.0.1:5000** in your browser.

## Project layout

```
app.py                 app factory / entry point — just creates the Flask
                        app and registers each page's blueprint
data.py                 seed data (projects, tasks, staff, i18n strings)
                        and small helper functions, shared by every page
views/
  core.py               session prefs, dark/lang/sidebar toggles, the
                        context processor that feeds the sidebar & nav
  dashboard.py           /dashboard
  projects.py            /projects, /projects/<id>, create/delete
  tasks.py                /tasks, create task, update status
  calendar.py             /calendar
  gantt.py                /gantt
  team.py                 /team
  reports.py              /reports, /reports/export.csv
  settings.py             /settings, role switch, language
templates/               one .html per page (Jinja2), extending base.html
static/style.css         all the styling
```

Each page is a self-contained Flask **blueprint** — its own routes, its
own module — so you can open, edit, or hand off `views/tasks.py` without
touching anything else.

## Notes

- All data (projects, tasks) lives in memory in `data.py` — it resets
  every time you restart the server, same as the original in-browser demo.
- Dark mode / language / role / sidebar state is stored in a signed
  session cookie.
- The Kanban board uses per-card status dropdowns instead of drag-and-drop
  (kept the app framework-free — no JS build step needed).
- "Export CSV" on the Reports page streams a real file download.
