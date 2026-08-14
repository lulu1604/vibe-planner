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

---------------------------------------------------------------------------
AMPLIACION v2 (Piero Calderon, Modulo A) - 2026-08-13
    Las 6 firmas de arriba NO se han tocado. Lo unico anadido es capa de
    conexion, que es territorio del nucleo:
        _aplicar_pragmas(conn)   PRAGMAs obligatorios de cada conexion
        raw_connection()         conexion fuera del ciclo de peticion
        init_db()                ahora ejecuta ademas schema_v2.sql
    Nada de esto cambia el comportamiento de las consultas de tareas: los 4
    asserts del final de este archivo y los 11 de `python app.py test` siguen
    pasando igual.
---------------------------------------------------------------------------
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


# Esquema de identidad del Modulo A (Piero). Vive en un .sql aparte porque es
# la fuente unica de verdad del nucleo y lo revisa Jose como dueno del esquema.
SCHEMA_V2_PATH = os.path.join(BASE_DIR, "schema_v2.sql")


def _aplicar_pragmas(conn):
    """
    Los tres PRAGMAs de cada conexion. NO son persistentes: se guardan en la
    conexion, no en el archivo, asi que hay que repetirlos SIEMPRE -- tambien
    en seed.py y en las pruebas.

    El primero es el que duele: sin `foreign_keys = ON`, SQLite ignora las
    claves foraneas EN SILENCIO. Borras un usuario y sus filas de user_roles
    quedan apuntando a un id que ya no existe, sin un solo error.
    """
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL permite leer mientras alguien escribe (riesgo R8). Si en
    # PythonAnywhere apareciera "database is locked", el plan B documentado es
    # volver a `journal_mode = DELETE` y subir el timeout a 20 s.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")   # 10 s antes de rendirse
    return conn


def get_db():
    """Una conexión por petición. NO usar una conexión global compartida."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
        _aplicar_pragmas(g.db)
    return g.db


def raw_connection():
    """
    Conexion FUERA del ciclo de peticion, con los mismos PRAGMAs.
    La usan seed.py, migraciones y las pruebas, que corren sin contexto Flask
    y por tanto no pueden tocar `g`. Quien la abre, la cierra.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return _aplicar_pragmas(conn)


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Crea el esquema v1 (tasks) y, si existe, el de identidad v2.

    Los dos son CREATE TABLE IF NOT EXISTS, asi que llamarlo mil veces no hace
    nada. schema_v2.sql es ESTRICTAMENTE ADITIVO: anade sus 5 tablas y no
    modifica `tasks`, para que la v1 siga funcionando mientras se construye
    el nucleo.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    _aplicar_pragmas(conn)
    conn.executescript(SCHEMA)

    if os.path.exists(SCHEMA_V2_PATH):
        with open(SCHEMA_V2_PATH, "r", encoding="utf-8") as archivo:
            conn.executescript(archivo.read())

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
    cursor = db.execute(
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
    return cursor.lastrowid if cursor.lastrowid else True


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


# --------------------------------------------------------------------------
# PRUEBAS UNITARIAS Y SUITE DE ASSERTS (EVIDENCIA DE TESTING DE JOSE)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # Test directo fuera de contexto Flask usando conexión SQLite pura
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Assert 1: Inserción directa
    cursor = conn.execute(
        "INSERT INTO tasks (title, category, priority_level, due_date, estimated_minutes) VALUES (?, ?, ?, ?, ?)",
        ("Tarea Test Jose", "Academic", 1, "2026-08-15", 45)
    )
    conn.commit()
    test_id = cursor.lastrowid
    assert test_id is not None, "Assert 1 Falló: Inserción de tarea"
    
    # Assert 2: Lectura
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (test_id,)).fetchone()
    assert row["title"] == "Tarea Test Jose" and row["priority_level"] == 1, "Assert 2 Falló: Lectura de tarea"
    
    # Assert 3: Actualización de estado
    conn.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (test_id,))
    conn.commit()
    row_up = conn.execute("SELECT status FROM tasks WHERE id = ?", (test_id,)).fetchone()
    assert row_up["status"] == "completed", "Assert 3 Falló: Actualización de estado"
    
    # Assert 4: Limpieza/Eliminación
    conn.execute("DELETE FROM tasks WHERE id = ?", (test_id,))
    conn.commit()
    row_del = conn.execute("SELECT * FROM tasks WHERE id = ?", (test_id,)).fetchone()
    assert row_del is None, "Assert 4 Falló: Eliminación de tarea"
    
    conn.close()
    print("SUCCESS: Todas las 4 pruebas de assert para database.py pasaron exitosamente!")
