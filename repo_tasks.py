"""
VibePlanner v2 - Repositorio de tareas (repo_tasks.py)
--------------------------------------------------------
DUENA DE ESTE ARCHIVO: Lucero Ayala (Modulo B - Planner y Kanban)

CONTRATOS CONGELADOS - no cambiar estas firmas sin avisar al grupo:
    get_owned(task_id, user_id)                -> dict | None
    list_by_user(user_id, column=None)         -> list[dict]
    list_by_day(user_id, date_iso)             -> list[dict]
    list_board(user_id)                        -> dict[str, list[dict]]
    list_assigned_by(leader_id)               -> list[dict]
    create(data, owner_id, assigned_by=None)   -> int
    update_owned(task_id, user_id, data)       -> bool
    move_column(task_id, user_id, column)      -> bool
    delete_owned(task_id, user_id)             -> bool
    daily_progress(user_id, date_iso)          -> dict {total, completed, percent}

REGLA CRITICA (TC-08 / TC-11):
    TODA consulta lleva user_id DENTRO del WHERE.
    Traer filas y filtrar en Python NO cuenta: si la fila llego a memoria,
    ya se filtro mal y la tarea ajena ya salio de la base de datos.

COLUMNAS VALIDAS del Kanban (fuente unica de verdad):
    backlog | todo | ongoing | done
    backlog = intencion, NO cuenta para el progreso del dia (TC-22).
"""

from database import get_db

# Columnas validas del tablero Kanban. Se validan AQUI y en planner.py.
KANBAN_COLUMNS = ("backlog", "todo", "ongoing", "done")

# Columnas que cuentan para el progreso del dia (excluye backlog - TC-22).
PROGRESS_COLUMNS = ("todo", "ongoing", "done")


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------

def get_owned(task_id, user_id):
    """
    Devuelve la tarea si pertenece a user_id, None en caso contrario.
    El WHERE doble (id + user_id) es lo que evita TC-08 y TC-11.
    Un 404 es mas seguro que un 403: el 403 confirma que el id existe.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM tasks_v2 WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def list_by_user(user_id, column=None):
    """
    Lista todas las tareas del usuario, opcionalmente filtradas por columna.
    Ordenadas por puntaje descendente (el motor de scoring las reordena despues).
    """
    db = get_db()
    if column:
        rows = db.execute(
            """SELECT * FROM tasks_v2
               WHERE user_id = ? AND kanban_column = ?
               ORDER BY due_date ASC, id ASC""",
            (user_id, column),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT * FROM tasks_v2
               WHERE user_id = ?
               ORDER BY due_date ASC, id ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_by_day(user_id, date_iso):
    """
    Devuelve las tareas del usuario para una fecha concreta (YYYY-MM-DD).
    Ordenadas por hora de inicio (start_time) para la pantalla de revision del dia (US8).
    Excluye backlog: es intencion, no compromiso del dia.
    """
    db = get_db()
    rows = db.execute(
        """SELECT * FROM tasks_v2
           WHERE user_id = ? AND due_date = ? AND kanban_column != 'backlog'
           ORDER BY COALESCE(start_time, '99:99') ASC, id ASC""",
        (user_id, date_iso),
    ).fetchall()
    return [dict(r) for r in rows]


def list_board(user_id):
    """
    Devuelve un dict con las 4 columnas SIEMPRE, aunque esten vacias (TC-19).
    Si falta una clave, la plantilla kanban.html revienta cuando el usuario
    no tiene tareas en esa columna.
    """
    db = get_db()
    rows = db.execute(
        """SELECT * FROM tasks_v2
           WHERE user_id = ?
           ORDER BY due_date ASC, id ASC""",
        (user_id,),
    ).fetchall()

    board = {col: [] for col in KANBAN_COLUMNS}
    for row in rows:
        col = row["kanban_column"] if row["kanban_column"] in KANBAN_COLUMNS else "backlog"
        board[col].append(dict(row))
    return board


def list_assigned_by(leader_id):
    """
    Devuelve las tareas que este usuario asigno a otros (US10).
    Agrupa por destinatario para la vista de equipo.
    """
    db = get_db()
    rows = db.execute(
        """SELECT t.*, u.username AS assignee_username
           FROM tasks_v2 t
           JOIN users u ON u.id = t.user_id
           WHERE t.assigned_by = ?
           ORDER BY u.username ASC, t.due_date ASC, t.id ASC""",
        (leader_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def daily_progress(user_id, date_iso):
    """
    Progreso del dia: solo columnas todo/ongoing/done, EXCLUYE backlog (TC-22).
    Devuelve dict con claves: total, completed, percent.
    """
    db = get_db()
    # Total = todo lo que el usuario se comprometio hoy (sin backlog)
    total_row = db.execute(
        """SELECT COUNT(*) AS n FROM tasks_v2
           WHERE user_id = ? AND due_date = ? AND kanban_column != 'backlog'""",
        (user_id, date_iso),
    ).fetchone()
    done_row = db.execute(
        """SELECT COUNT(*) AS n FROM tasks_v2
           WHERE user_id = ? AND due_date = ? AND kanban_column = 'done'""",
        (user_id, date_iso),
    ).fetchone()

    total = total_row["n"] if total_row else 0
    completed = done_row["n"] if done_row else 0
    percent = round((completed / total) * 100) if total > 0 else 0

    return {"total": total, "completed": completed, "percent": percent}


# --------------------------------------------------------------------------
# Escritura
# --------------------------------------------------------------------------

def create(data, owner_id, assigned_by=None):
    """
    Inserta una nueva tarea. Devuelve el id de la fila creada.
    owner_id viene de la sesion, NUNCA del formulario.
    assigned_by: id de quien asigna (US10), o None si es propia.
    """
    db = get_db()
    cursor = db.execute(
        """INSERT INTO tasks_v2
           (user_id, title, category, priority_level, due_date,
            estimated_minutes, kanban_column, start_time, end_time,
            description, assigned_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            owner_id,
            data["title"],
            data.get("category", "General"),
            data.get("priority_level", 2),
            data["due_date"],
            data.get("estimated_minutes", 30),
            data.get("kanban_column", "todo"),
            data.get("start_time") or None,
            data.get("end_time") or None,
            data.get("description", ""),
            assigned_by,
        ),
    )
    db.commit()
    return cursor.lastrowid


def update_owned(task_id, user_id, data):
    """
    Actualiza los campos de una tarea que pertenece a user_id.
    El WHERE doble garantiza que solo el dueno puede editar (TC-08).
    Devuelve True si la fila exisitia y se modifico.
    """
    db = get_db()
    cursor = db.execute(
        """UPDATE tasks_v2
           SET title = ?, category = ?, priority_level = ?,
               due_date = ?, estimated_minutes = ?,
               start_time = ?, end_time = ?, description = ?
           WHERE id = ? AND user_id = ?""",
        (
            data["title"],
            data.get("category", "General"),
            data.get("priority_level", 2),
            data["due_date"],
            data.get("estimated_minutes", 30),
            data.get("start_time") or None,
            data.get("end_time") or None,
            data.get("description", ""),
            task_id,
            user_id,
        ),
    )
    db.commit()
    return cursor.rowcount > 0


def move_column(task_id, user_id, column):
    """
    Mueve la tarea a una columna del Kanban.
    La columna debe estar en KANBAN_COLUMNS (validada en planner.py antes de llegar aqui).
    Devuelve True si la fila existia y le pertenecia al usuario.
    """
    db = get_db()
    cursor = db.execute(
        "UPDATE tasks_v2 SET kanban_column = ? WHERE id = ? AND user_id = ?",
        (column, task_id, user_id),
    )
    db.commit()
    return cursor.rowcount > 0


def delete_owned(task_id, user_id):
    """
    Elimina la tarea si pertenece a user_id.
    Devuelve True si se elimino alguna fila.
    """
    db = get_db()
    cursor = db.execute(
        "DELETE FROM tasks_v2 WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    )
    db.commit()
    return cursor.rowcount > 0
