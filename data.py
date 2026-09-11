"""
Seed data + small pure-function helpers shared by every page module.
Ported from src/data/seed.js and src/utils/helpers.js.
"""
import os
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# Seed / mock data
# ---------------------------------------------------------------------------

TODAY = date(2026, 8, 3)

STAFF = ["Andre", "John", "Frans"]

PROJECTS = []

MAIN_TASKS = []

TASKS = []

# Raw copies of every Master/Weekly workbook that's been imported, so the
# original spreadsheet can be reopened later instead of only seeing the data
# it produced. Each entry: {id, kind, filename, stored_name, uploaded_by,
# uploaded_at}. Files themselves live in UPLOAD_DIR under stored_name.
IMPORTS = []

# User-created folders (beyond the built-in Master/Weekly/Manual ones) for
# grouping projects. Each entry: {id, name, color}. A project is placed in
# one of these via its "origin" field, same as "master"/"weekly"/"manual".
CUSTOM_FOLDERS = []

# The three built-in folders can be renamed/recolored like custom ones, but
# unlike custom folders they can't be removed as a category — "origin" has
# to fall back to *something* — so their name/color live here instead of a
# list, keyed by the fixed origin id. Deleting one of these (see
# views.projects.delete_folder) wipes the projects+tasks inside it but
# leaves the category itself in place, empty.
BUILTIN_FOLDERS = {
    "master": {"name": "Master data", "color": "#004BFF"},
    "weekly": {"name": "Weekly updates", "color": "#D6C100"},
    "manual": {"name": "Manually added", "color": "#00FFA6"},
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# ---------------------------------------------------------------------------
# Task detail — fill in the fields the seed rows above don't spell out
# (start date, progress, notes) plus empty activity/comment/attachment
# threads for every subtask, so the task-detail page always has something
# sane to render.
# ---------------------------------------------------------------------------
_DEFAULT_PROGRESS = {"pending": 0, "in-progress": 55, "completed": 100, "cancelled": 0, "overdue": 0}

_SEED_NOTES = {}

_SEED_COMMENTS = {}

ACTIVITY = []

# Bell notifications shown from the topbar bell. Same in-memory-mutation
# pattern as TASKS/PROJECTS: "read" flips in place. Entries with no
# "recipient" (or recipient=None) are broadcast to everyone; entries with
# a recipient (a name from STAFF/USERS) are only shown to that person —
# see views.core.inject_globals, which filters NOTIFICATIONS by recipient
# before handing them to a template.
NOTIFICATIONS = []

# Full activity/audit log — Admin & Manager see everything, Staff only see
# entries where they are the actor. "actor" matches a name in STAFF.
HISTORY = []

# Admin-only user directory — demo credentials, kept in-memory like everything else.
USERS = [
    {"id": "u1", "name": "Puput", "username": "puput", "password": "puput123", "role": "Administrator"},
    {"id": "u2", "name": "Jafar", "username": "jafar", "password": "jafar123", "role": "Manager"},
    {"id": "u3", "name": "Andre", "username": "andre", "password": "andre123", "role": "Staff"},
    {"id": "u4", "name": "John", "username": "john", "password": "john123", "role": "Staff"},
    {"id": "u5", "name": "Frans", "username": "frans", "password": "frans123", "role": "Staff"},
]


def assignable_people():
    """Everyone a task can be assigned to, and everyone shown in the
    'Tasks per staff member' breakdown: the Staff roster plus any
    Manager- or Administrator-role users (who also carry casework, not
    just Staff)."""
    names = list(STAFF)
    for u in USERS:
        if u["role"] in ("Manager", "Administrator") and u["name"] not in names:
            names.append(u["name"])
    return names

STATUS_META = {
    "pending": {"label": "Pending", "cls": "st-todo"},
    "in-progress": {"label": "In Progress", "cls": "st-progress"},
    "completed": {"label": "Completed", "cls": "st-done"},
    "cancelled": {"label": "Cancelled", "cls": "st-cancelled"},
    "overdue": {"label": "Overdue", "cls": "st-overdue"},
}
PRIORITY_META = {
    "low": {"label": "Low", "cls": "pr-low"},
    "medium": {"label": "Medium", "cls": "pr-medium"},
    "high": {"label": "High", "cls": "pr-high"},
    "critical": {"label": "Critical", "cls": "pr-critical"},
}

# ---------------------------------------------------------------------------
# Case-details dropdown option lists — every field below is rendered as a
# <select> (with an "editable" combobox for Surveyor, since that roster
# isn't limited to the app's own Users) in the New project / Edit project
# forms, and reused by the project-excel editor's inline cell dropdowns.
# ---------------------------------------------------------------------------
URGENCY_OPTIONS = ["Medium", "High", "Low", "Monitor", "Lunas"]
STATUS_OPTIONS = [
    "Skip Tracing", "Push", "No Capacity", "Monitor Payment", "Monitor PKPU",
    "Monitor Case", "Lelang", "Restructure", "Lunas",
]
TIPE_OPTIONS = ["Rumah", "Kantor", "Rumah/Kantor", "Bank Amar", "Call/WA", "Lainnya"]
OBJEKTIF_OPTIONS = ["Penagihan", "Penekanan", "Validasi"]
MEETING_STATUS_OPTIONS = ["Bertemu", "Tidak Bertemu"]
CRITICAL_OPTIONS = ["Info Baru", "Janji Temu", "Pembayaran", "Response Debitur"]
RATING_OPTIONS = ["0", "1", "2", "3", "4", "5"]

# Seed names for the Surveyor suggestion list — combined at runtime with
# assignable_people() and any surveyor names already saved on a project, so
# the dropdown/datalist always includes real people beyond just app Users.
SURVEYOR_SEED = []


def known_surveyors():
    """Every name that's shown up as a Surveyor so far, plus the assignable
    Staff/Manager/Administrator roster — used to populate the Surveyor
    combobox's suggestion list without restricting it to just app Users."""
    names = list(dict.fromkeys(SURVEYOR_SEED + assignable_people()))
    for p in PROJECTS:
        s = p.get("surveyor")
        if s and s not in names:
            names.append(s)
    return names

T = {
    "en": {"dashboard": "Dashboard", "projects": "Projects", "tasks": "Tasks", "calendar": "Calendar",
           "gantt": "Gantt Chart", "team": "Team", "reports": "Reports", "settings": "Settings",
           "history": "History", "admin": "Admin",
           "welcome": "Welcome back. Here's what needs attention today.",
           "welcomeManager": "Welcome back! Here's your team's overview.",
           "overdueTasks": "overdue tasks",
           "dueToday": "due today", "totalProjects": "Total projects", "completed": "Completed",
           "inProgress": "In progress", "overdue": "Overdue", "projectProgress": "Project progress",
           "statusDist": "Task status distribution", "perStaff": "Tasks per staff member",
           "recentActivity": "Recent activity", "notifications": "Notifications",
           "markAllRead": "Mark all read", "noNotifications": "You're all caught up.",
           "pm": {
               "newProject": "New project", "editProject": "Edit project", "newFolder": "New folder",
               "projectDebtorName": "Project / debtor name", "projectName": "Project name",
               "projectNamePlaceholder": "e.g. Collections process audit, or a debtor's name",
               "code": "Code", "codePlaceholder": "auto-generated if left blank",
               "category": "Category", "categoryPlaceholder": "e.g. Collections",
               "folder": "Folder", "manuallyAdded": "Manually added",
               "masterData": "Master data", "weeklyUpdates": "Weekly updates",
               "folderName": "Folder name", "folderNamePlaceholder": "e.g. Regional cases",
               "color": "Color", "accentColor": "Accent color",
               "debtorCheckbox": "This is a debtor / case project (adds PIC, overdue amount, Kol, monthly notes, etc.)",
               "addToFolderQ": "Add to folder?",
               "noFolder": "Don't add to a folder",
               "addToThisFolder": "Add to this folder", "addToAFolder": "Add to a folder",
               "createNewFolderForProject": "Create a new folder for this project",
               "caseDetails": "Case details", "additionalDetails": "Additional details",
               "monthlyNotesHead": "Monthly notes (e.g. \"Jun'26\", \"Jul'26\")",
               "pic": "PIC", "picPlaceholder": "e.g. Andre",
               "collector": "Collector", "collectorPlaceholder": "e.g. Internal",
               "status": "Status", "statusPlaceholder": "e.g. Skip Tracing",
               "urgency": "Urgency", "urgencyPlaceholder": "e.g. Medium",
               "contactable": "Contactable", "contactablePlaceholder": "Yes / No",
               "loanType": "Loan type", "loanTypePlaceholder": "e.g. Unsecured",
               "source": "Source", "jaminan": "Jaminan",
               "pokok": "Pokok", "overdueTotal": "Overdue amount / Total tagihan", "totalTagihan": "Total tagihan",
               "collected2025": "Collected 2025", "collected2026": "Collected 2026",
               "lvAgunan": "LV Agunan", "mvAgunan": "MV Agunan",
               "dpd": "DPD", "dueDate": "Due date",
               "woStage": "WO stage", "woDate": "WO date",
               "auctionStatus": "Auction status", "tanggalBast": "Tanggal BAST",
               "kol": "Kol", "kolPlaceholder": "e.g. LUNAS",
               "tipe": "Tipe", "tipePlaceholder": "Select tipe",
               "surveyor": "Surveyor", "surveyorPlaceholder": "Type or pick a name",
               "objektif": "Objektif", "objektifPlaceholder": "Select objektif",
               "meetingStatus": "Meeting status", "meetingStatusPlaceholder": "Select status",
               "critical": "Critical", "criticalPlaceholder": "Select critical",
               "rating": "Rating", "ratingPlaceholder": "Select rating",
               "chooseOption": "Select…",
               "remark": "Remark", "planNextWeek": "Plan next week",
               "addMonthlyNote": "Add monthly note", "addDetail": "Add detail",
               "detailTitle": "Detail title", "detailDescription": "Detail description",
               "monthNotePlaceholder": "e.g. Jul'26", "monthNoteDescPlaceholder": "What happened this month",
               "cancel": "Cancel", "createProject": "Create project", "createFolder": "Create folder",
               "saveChanges": "Save changes",
           }},
    "id": {"dashboard": "Dasbor", "projects": "Proyek", "tasks": "Tugas", "calendar": "Kalender",
           "gantt": "Bagan Gantt", "team": "Tim", "reports": "Laporan", "settings": "Pengaturan",
           "history": "Riwayat", "admin": "Admin",
           "welcome": "Selamat datang kembali. Berikut yang perlu perhatian hari ini.",
           "welcomeManager": "Selamat datang kembali! Berikut ringkasan tim Anda.",
           "overdueTasks": "tugas terlambat", "dueToday": "jatuh tempo hari ini",
           "totalProjects": "Total proyek", "completed": "Selesai", "inProgress": "Sedang berjalan",
           "overdue": "Terlambat", "projectProgress": "Progres proyek",
           "statusDist": "Distribusi status tugas", "perStaff": "Tugas per anggota tim",
           "recentActivity": "Aktivitas terbaru", "notifications": "Notifikasi",
           "markAllRead": "Tandai semua dibaca", "noNotifications": "Semua sudah dibaca.",
           "pm": {
               "newProject": "Proyek baru", "editProject": "Edit proyek", "newFolder": "Folder baru",
               "projectDebtorName": "Nama proyek / debitur", "projectName": "Nama proyek",
               "projectNamePlaceholder": "mis. audit proses penagihan, atau nama debitur",
               "code": "Kode", "codePlaceholder": "dibuat otomatis jika dikosongkan",
               "category": "Kategori", "categoryPlaceholder": "mis. Penagihan",
               "folder": "Folder", "manuallyAdded": "Ditambahkan manual",
               "masterData": "Data master", "weeklyUpdates": "Pembaruan mingguan",
               "folderName": "Nama folder", "folderNamePlaceholder": "mis. Kasus Regional",
               "color": "Warna", "accentColor": "Warna aksen",
               "debtorCheckbox": "Ini adalah proyek debitur / kasus (menambahkan PIC, jumlah tunggakan, Kol, catatan bulanan, dll.)",
               "addToFolderQ": "Tambahkan ke folder?",
               "noFolder": "Jangan tambahkan ke folder",
               "addToThisFolder": "Tambahkan ke folder ini", "addToAFolder": "Tambahkan ke folder",
               "createNewFolderForProject": "Buat folder baru untuk proyek ini",
               "caseDetails": "Detail kasus", "additionalDetails": "Detail tambahan",
               "monthlyNotesHead": "Catatan bulanan (mis. \"Jun'26\", \"Jul'26\")",
               "pic": "PIC", "picPlaceholder": "mis. Andre",
               "collector": "Kolektor", "collectorPlaceholder": "mis. Internal",
               "status": "Status", "statusPlaceholder": "mis. Skip Tracing",
               "urgency": "Urgensi", "urgencyPlaceholder": "mis. Sedang",
               "contactable": "Dapat dihubungi", "contactablePlaceholder": "Ya / Tidak",
               "loanType": "Jenis pinjaman", "loanTypePlaceholder": "mis. Tanpa agunan",
               "source": "Sumber", "jaminan": "Jaminan",
               "pokok": "Pokok", "overdueTotal": "Jumlah tunggakan / Total tagihan", "totalTagihan": "Total tagihan",
               "collected2025": "Tertagih 2025", "collected2026": "Tertagih 2026",
               "lvAgunan": "LV Agunan", "mvAgunan": "MV Agunan",
               "dpd": "DPD", "dueDate": "Tanggal jatuh tempo",
               "woStage": "Tahap WO", "woDate": "Tanggal WO",
               "auctionStatus": "Status lelang", "tanggalBast": "Tanggal BAST",
               "kol": "Kol", "kolPlaceholder": "mis. LUNAS",
               "tipe": "Tipe", "tipePlaceholder": "Pilih tipe",
               "surveyor": "Surveyor", "surveyorPlaceholder": "Ketik atau pilih nama",
               "objektif": "Objektif", "objektifPlaceholder": "Pilih objektif",
               "meetingStatus": "Status pertemuan", "meetingStatusPlaceholder": "Pilih status",
               "critical": "Critical", "criticalPlaceholder": "Pilih critical",
               "rating": "Rating", "ratingPlaceholder": "Pilih rating",
               "chooseOption": "Pilih…",
               "remark": "Catatan", "planNextWeek": "Rencana minggu depan",
               "addMonthlyNote": "Tambah catatan bulanan", "addDetail": "Tambah detail",
               "detailTitle": "Judul detail", "detailDescription": "Deskripsi detail",
               "monthNotePlaceholder": "mis. Jul'26", "monthNoteDescPlaceholder": "Apa yang terjadi bulan ini",
               "cancel": "Batal", "createProject": "Buat proyek", "createFolder": "Buat folder",
               "saveChanges": "Simpan perubahan",
           }},
}

# (nav key, i18n label key, icon name, endpoint — blueprint.view_func)
NAV = [
    ("dashboard", "dashboard", "dashboard", "dashboard.dashboard"),
    ("projects", "projects", "projects", "projects.projects_list"),
    ("tasks", "tasks", "tasks", "tasks.tasks_view"),
    ("calendar", "calendar", "calendar", "calendar.calendar_view"),
    ("gantt", "gantt", "gantt", "gantt.gantt_view"),
    ("team", "team", "team", "team.team_view"),
    ("reports", "reports", "reports", "reports.reports_view"),
    ("history", "history", "history", "history.history_view"),
    ("settings", "settings", "settings", "settings.settings_view"),
]

# simple in-memory id counters for records created during the session
_next_task_seq = [len(TASKS)]
_next_project_seq = [0]
_next_user_seq = [0]
_next_comment_seq = [0]
_next_attachment_seq = [0]
_next_import_seq = [0]
_next_folder_seq = [0]


def next_task_id():
    _next_task_seq[0] += 1
    return f"t{_next_task_seq[0]}-{int(datetime.utcnow().timestamp())}"


def next_project_id():
    _next_project_seq[0] += 1
    return f"p{TODAY.isoformat()}-{_next_project_seq[0]}"


def next_import_id():
    _next_import_seq[0] += 1
    return f"imp{_next_import_seq[0]}-{int(datetime.utcnow().timestamp())}"


def next_folder_id():
    _next_folder_seq[0] += 1
    return f"folder-{_next_folder_seq[0]}-{int(datetime.utcnow().timestamp())}"


def next_user_id():
    _next_user_seq[0] += 1
    return f"u{_next_user_seq[0]}-{int(datetime.utcnow().timestamp())}"


def next_comment_id():
    _next_comment_seq[0] += 1
    return f"c{_next_comment_seq[0]}-{int(datetime.utcnow().timestamp())}"


def now_stamp():
    """WhatsApp-style local timestamp used on comments — 'DD/MM/YYYY, HH.MM'
    (dot between hour/minute, like the chat exports this app is meant to
    mirror) — stamped once at post time and reused as-is everywhere the
    comment shows up (task detail page, per-project Excel, tasks Excel)."""
    return datetime.now().strftime("%d/%m/%Y, %H.%M")


def next_attachment_id():
    _next_attachment_seq[0] += 1
    return f"f{_next_attachment_seq[0]}-{int(datetime.utcnow().timestamp())}"


_next_activity_seq = [0]


def log_activity(actor, text, icon="clock", project_id=None, task_id=None, url=None):
    """Record one event in both feeds at once:
    - ACTIVITY: the dashboard's "Recent activity" card (everyone sees the
      same feed, newest first, capped so it can't grow unbounded).
    - HISTORY: the full audit log on the History page (Admin/Manager see
      everything there; Staff only see rows where they're the actor).
    `actor` should match a name from STAFF/USERS so that Staff-scoped
    filtering on the History page works.

    `project_id`/`task_id` let the entry link back to the record it's
    about (see app.py's activity_url()), so clicking a row in either feed
    jumps straight to the relevant task or project. `url` overrides that
    default resolution for events that don't map to a single task/project
    (e.g. a bulk import touching many projects) — pass an explicit
    destination (built with url_for) instead."""
    _next_activity_seq[0] += 1
    entry = {
        "id": f"a{_next_activity_seq[0]}-{int(datetime.utcnow().timestamp())}",
        "actor": actor, "text": text, "icon": icon,
        "time": "Just now", "projectId": project_id, "taskId": task_id, "url": url,
    }
    ACTIVITY.insert(0, dict(entry))
    del ACTIVITY[50:]
    HISTORY.insert(0, dict(entry))
    del HISTORY[300:]


_next_notification_seq = [0]


def next_notification_id():
    _next_notification_seq[0] += 1
    return f"n{_next_notification_seq[0]}-{int(datetime.utcnow().timestamp())}"


def notify(recipient, text, icon="alert"):
    """Push a bell notification to a specific person (by their STAFF/USERS
    name). No-ops quietly if there's no one to notify."""
    if not recipient:
        return False
    NOTIFICATIONS.insert(0, {
        "id": next_notification_id(), "recipient": recipient,
        "text": text, "icon": icon, "time": "Just now", "read": False,
    })
    return True


# ---------------------------------------------------------------------------
# Helpers (ported from src/utils/helpers.js)
# ---------------------------------------------------------------------------

def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def fmt_date(s):
    return parse_date(s).strftime("%d %b %Y")


def days_between(a, b):
    """Matches JS daysBetween(a, b) = round((a - b) / 1 day)."""
    return (a - b).days


def is_done(task):
    return task["status"] in ("completed", "cancelled")


def is_overdue(task):
    """True if the task is explicitly marked Overdue, or is still open
    (not completed/cancelled) and its due date has already passed — so a
    pending/in-progress task automatically reads as overdue without anyone
    having to flip its status by hand, while also honoring a manual
    'overdue' status set directly on the task."""
    if task["status"] == "overdue":
        return True
    return not is_done(task) and parse_date(task["dueDate"]) < TODAY


def is_due_today(task):
    return not is_done(task) and parse_date(task["dueDate"]) == TODAY


def grouped_number(v):
    """Thousands-separated display of a plain number, with no currency
    prefix or abbreviation — for the generic imported-spreadsheet grid,
    where a column could be an amount, an ID, a count, anything; we don't
    know its meaning, just that a bare 12-digit number is hard to read
    without separators. Returns None (not a placeholder string) for
    anything that isn't actually numeric, so the caller can fall back to
    displaying the original value untouched."""
    if isinstance(v, bool):
        return None  # bool is technically an int subclass in Python — exclude it
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        # Keep the fractional part as-is (not rounded away) — only the
        # integer portion gets thousands separators, matching how Excel's
        # own "#,##0.###" number format behaves.
        sign = "-" if v < 0 else ""
        whole, _, frac = f"{abs(v)!r}".partition(".")
        if frac and frac != "0" and len(frac) >= 4:
            # A fractional part this long isn't a real decimal amount (like
            # cents) — it's almost always a big number that lost its
            # thousands separators and got read back in as one float with a
            # stray decimal point (e.g. 655.205634 really means 655205634).
            # Treat the whole+frac digits as a single integer and group
            # them in 3s, dropping the "." entirely — 655.205634 -> 655,205,634.
            grouped = f"{int(whole + frac):,}"
            return f"{sign}{grouped}"
        grouped = f"{int(whole):,}"
        return f"{sign}{grouped}.{frac}" if frac and frac != "0" else f"{sign}{grouped}"
    return None


def fmt_money(v):
    """Rp-formatted amount, abbreviated to Jt/M/T (juta/miliar/triliun) for
    the big NPL figures — e.g. 1476532533 -> 'Rp 1.48 M'."""
    if v is None or v == "":
        return "—"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    except Exception:
        # Covers Jinja's Undefined (missing dict key) raising UndefinedError
        # on float(), so a field that's absent on a record never crashes
        # the page — it just renders as "—" like a None value would.
        return "—"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000_000_000:
        return f"{sign}Rp {v / 1_000_000_000_000:.2f} T"
    if v >= 1_000_000_000:
        return f"{sign}Rp {v / 1_000_000_000:.2f} M"
    if v >= 1_000_000:
        return f"{sign}Rp {v / 1_000_000:.0f} Jt"
    return f"{sign}Rp {v:,.0f}"


def initials(name):
    if not name:
        return "?"
    parts = name.split(" ")
    return "".join(p[0] for p in parts if p).upper()[:2]


def main_task_of(mid):
    for m in MAIN_TASKS:
        if m["id"] == mid:
            return m
    return None


def task_of(tid):
    for tk in TASKS:
        if tk["id"] == tid:
            return tk
    return None


# ---------------------------------------------------------------------------
# Backfill task-detail fields (startDate, progress, notes, comments,
# attachments) for every subtask seeded above, so the task-detail page
# always has something sane to work with.
# ---------------------------------------------------------------------------
for _tk in TASKS:
    _tk.setdefault("startDate", (parse_date(_tk["dueDate"]) - timedelta(
        days=10 if _tk["status"] == "in-progress" else 5
    )).isoformat())
    _tk.setdefault("progress", _DEFAULT_PROGRESS.get(_tk["status"], 0))
    _tk.setdefault("notes", _SEED_NOTES.get(_tk["id"], ""))
    _tk.setdefault("comments", list(_SEED_COMMENTS.get(_tk["id"], [])))
    _tk.setdefault("attachments", [])


def project_of(pid, projects=None):
    projects = projects if projects is not None else PROJECTS
    for p in projects:
        if p["id"] == pid:
            return p
    return None
