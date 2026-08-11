"""
VibePlanner - Capa de persistencia (walking skeleton)
-----------------------------------------------------
DUEÑO DE ESTE ARCHIVO: Jose (dueño único del esquema SQL)

CONTRATOS CONGELADOS - no cambiar estas firmas sin avisar al grupo:
    get_tasks(filter_status=None)      -> list[dict]
    get_task_by_id(task_id)            -> dict | None
    add_task(task_data)                -> bool
    update_status(task_id, new_status) -> bool
    delete_task(task_id)               -> bool
    get_daily_progress()               -> dict con claves: total, completed, percent

Cada tarea es un dict con las claves:
    id, title, category, priority_level, due_date, estimated_minutes,
    status, created_at
"""

import os
import sqlite3

from flask import g

# Ruta ABSOLUTA: una ruta relativa funciona en local y falla en PythonAnywhere.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vibe_planner.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    NOT NULL,
    category          TEXT    DEFAULT 'General',
    priority_level    INTEGER NOT NULL DEFAULT 2,   -- 1 Alta, 2 Media, 3 Baja
    due_date          TEXT    NOT NULL,             -- YYYY-MM-DD
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    status            TEXT    DEFAULT 'pending',    -- pending|in_progress|completed
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    """Una conexión por petición. NO usar una conexión global compartida."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# STUBS - Jose implementa el cuerpo. Las firmas ya están congeladas.
# --------------------------------------------------------------------------
def get_tasks(filter_status=None):
    """TODO: SELECT * FROM tasks (filtrando por status si viene)."""
    db = get_db()
    rows = db.execute("SELECT * FROM tasks").fetchall()
    return [dict(r) for r in rows]


def get_task_by_id(task_id):
    """TODO: SELECT una sola fila."""
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def add_task(task_data):
    """TODO: INSERT. Devuelve True si se insertó."""
    db = get_db()
    db.execute(
        """INSERT INTO tasks
           (title, category, priority_level, due_date, estimated_minutes)
           VALUES (?, ?, ?, ?, ?)""",
        (
            task_data["title"],
            task_data["category"],
            task_data["priority_level"],
            task_data["due_date"],
            task_data["estimated_minutes"],
        ),
    )
    db.commit()
    return True


def update_status(task_id, new_status):
    """TODO: UPDATE del campo status."""
    return False


def delete_task(task_id):
    """TODO: DELETE por id."""
    return False


def get_daily_progress():
    """TODO: contar completadas vs total. US3."""
    return {"total": 0, "completed": 0, "percent": 0}
