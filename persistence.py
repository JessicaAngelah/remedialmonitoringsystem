"""
Lightweight persistence layer.

The rest of the app (data.py, views/*) keeps working exactly the way it
always has: PROJECTS, TASKS, MAIN_TASKS, IMPORTS, CUSTOM_FOLDERS,
BUILTIN_FOLDERS, ACTIVITY, NOTIFICATIONS, HISTORY, and USERS are still
plain Python lists/dicts that views mutate in place (tk["status"] = ...,
TASKS.append(...), CUSTOM_FOLDERS[:] = ..., etc.) — nothing about that
changes, so no view file needs to be touched.

What this module adds: after every request that could have changed
something, it snapshots each of those collections and writes it to a
real database (SQLite locally, Postgres in production via the
DATABASE_URL env var) as one JSON blob per collection. On startup, it
reads those blobs back and replaces the in-memory collections' contents
in place, so data survives restarts and deploys instead of resetting
every time the process starts.

Known limitation: uploaded files (task attachments, imported
spreadsheets) still live on local disk under uploads/, not in the
database. That's fine on a normal server, but on a host with an
ephemeral filesystem (e.g. Render's free tier between deploys) those
files won't survive a redeploy even though the metadata about them
will. Revisit with an object-storage bucket if that becomes a problem.
"""
import json
import os

from flask import request
from sqlalchemy import Column, MetaData, String, Table, Text, create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

import data

# Name used in the database -> the actual list/dict object in data.py that
# it should be loaded into / saved from. These are the *same* objects every
# other module already imported, so mutating them in place here is enough
# for the change to show up everywhere.
_COLLECTIONS = {
    "projects": data.PROJECTS,
    "main_tasks": data.MAIN_TASKS,
    "tasks": data.TASKS,
    "imports": data.IMPORTS,
    "custom_folders": data.CUSTOM_FOLDERS,
    "builtin_folders": data.BUILTIN_FOLDERS,
    "activity": data.ACTIVITY,
    "notifications": data.NOTIFICATIONS,
    "history": data.HISTORY,
    "users": data.USERS,
}

# Requests that can't possibly have changed anything — skip the write on
# these so a normal page view doesn't pay for a database round trip.
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

_metadata = MetaData()
_state_table = Table(
    "app_state", _metadata,
    Column("collection", String(64), primary_key=True),
    Column("data", Text, nullable=False),
)

_engine = None


def _database_url():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        # Local default: a SQLite file that lives next to data.py.
        db_path = os.path.join(data.BASE_DIR, "app.db")
        return f"sqlite:///{db_path}"
    # Render (like Heroku before it) hands out "postgres://" URLs, but
    # SQLAlchemy 1.4+ only accepts the "postgresql://" scheme.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_database_url(), future=True)
        _metadata.create_all(_engine)
    return _engine


def load_state():
    """Read every saved collection back into data.py's in-memory objects.
    Safe to call with nothing saved yet (e.g. a brand-new database) — the
    collections are just left as data.py's own empty defaults."""
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(_state_table.select()).fetchall()
    saved = {row.collection: json.loads(row.data) for row in rows}
    for name, target in _COLLECTIONS.items():
        if name not in saved:
            continue
        value = saved[name]
        if isinstance(target, list):
            target[:] = value
        elif isinstance(target, dict):
            target.clear()
            target.update(value)


def save_state():
    """Snapshot every collection to the database, overwriting whatever was
    stored for it before."""
    engine = _get_engine()
    is_sqlite = engine.dialect.name == "sqlite"
    with engine.begin() as conn:
        for name, target in _COLLECTIONS.items():
            payload = json.dumps(target)
            insert = sqlite_insert if is_sqlite else pg_insert
            stmt = insert(_state_table).values(collection=name, data=payload)
            stmt = stmt.on_conflict_do_update(
                index_elements=["collection"], set_={"data": payload}
            )
            conn.execute(stmt)


def init_app(app):
    """Call once at startup: restore whatever was saved last time, then
    keep saving after every request that could have made a change."""
    load_state()

    @app.after_request
    def _save_after_request(response):
        if request.method not in _SAFE_METHODS:
            try:
                save_state()
            except Exception:
                # Never let a persistence hiccup take down the page the
                # user was actually trying to see.
                app.logger.exception("Failed to persist app state")
        return response

    return app
