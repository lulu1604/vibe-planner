"""
VibePlanner - Capa de persistencia (database.py)
-----------------------------------------------------
DUEÑO DE ESTE ARCHIVO: Jose Cabrera (dueño único del esquema SQL)

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
# IMPLEMENTACIÓN DE CONSULTAS Y OPERACIONES PERSISTENTES (JOSE CABRERA)
# --------------------------------------------------------------------------

def get_tasks(filter_status=None):
    """Devuelve las tareas registradas en SQLite, opcionalmente filtradas por estado."""
    db = get_db()
    if filter_status:
        rows = db.execute("SELECT * FROM tasks WHERE status = ? ORDER BY id DESC", (filter_status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def get_task_by_id(task_id):
    """Obtiene un diccionario completo de la tarea especificada por id o None si no existe."""
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def add_task(task_data):
    """Inserta una nueva actividad en SQLite con status 'pending' de forma segura."""
    db = get_db()
    db.execute(
        """INSERT INTO tasks
           (title, category, priority_level, due_date, estimated_minutes, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            task_data["title"],
            task_data.get("category", "General"),
            task_data.get("priority_level", 2),
            task_data["due_date"],
            task_data.get("estimated_minutes", 30),
            task_data.get("status", "pending")
        ),
    )
    db.commit()
    return True


def update_status(task_id, new_status):
    """
    Actualiza el estado de una tarea. 
    Valida que new_status sea uno de: 'pending', 'in_progress' o 'completed'.
    Devuelve True si la fila existió y se actualizó correctamente, de lo contrario False.
    """
    allowed_statuses = ["pending", "in_progress", "completed"]
    if new_status not in allowed_statuses:
        return False
        
    db = get_db()
    cursor = db.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (new_status, task_id)
    )
    db.commit()
    return cursor.rowcount > 0


def delete_task(task_id):
    """Elimina una tarea por su id. Devuelve True si se eliminó alguna fila."""
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return cursor.rowcount > 0


def get_daily_progress():
    """
    Calcula el total de tareas, tareas completadas y porcentaje de cumplimiento.
    Previene la división por cero cuando no existen registros.
    """
    db = get_db()
    total_row = db.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()
    completed_row = db.execute("SELECT COUNT(*) AS completed FROM tasks WHERE status = 'completed'").fetchone()
    
    total = total_row["total"] if total_row else 0
    completed = completed_row["completed"] if completed_row else 0
    
    percent = round((completed / total) * 100, 1) if total > 0 else 0.0
    
    return {
        "total": total,
        "completed": completed,
        "percent": percent
    }
