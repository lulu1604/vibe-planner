"""
VibePlanner v2 - Blueprint del Planner y Kanban (planner.py)
--------------------------------------------------------------
DUENA DE ESTE ARCHIVO: Lucero Ayala (Modulo B)

Rutas:
    GET  /planner                               -> Revision del dia (US8) + ranking (US2)
    POST /tasks                                 -> Crear tarea (US1)
    POST /tasks/<id>/edit                       -> Editar tarea (US1)
    POST /tasks/<id>/delete                     -> Eliminar tarea (US1)
    POST /tasks/<id>/column                     -> Mover columna Kanban (US3/US9)
    GET  /kanban                                -> Tablero Kanban (US9)
    GET  /equipo/tareas                         -> Tareas asignadas (US10)
    GET  /api/task/<id>/score-breakdown         -> Desglose del puntaje (US4)

REGLAS CRITICAS:
    - user_id SIEMPRE de current_user_id(), NUNCA del formulario.
    - @requires() comprueba PERMISOS, nunca nombres de rol.
    - Tarea ajena -> 404 (NO 403: el 403 confirma que el id existe).
    - CSRF token en todos los formularios POST.
    - Columna invalida -> HTTP 400 (TC-21).
"""

from datetime import datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

import repo_tasks
import scoring
import security
from repo_tasks import KANBAN_COLUMNS

planner = Blueprint("planner", __name__, url_prefix="")

# Columnas validas: fuente unica de verdad importada de repo_tasks.py
_TODAY_FMT = "%Y-%m-%d"
MAX_TITLE_LEN = 120
MAX_MINUTES = 480   # 8 horas: maximo razonable para una tarea


# --------------------------------------------------------------------------
# Helpers de validacion
# --------------------------------------------------------------------------

def _hoy():
    """Fecha de hoy en Lima (UTC-5). Heredada de scoring.py."""
    return scoring.today_local().isoformat()


def _validar_tarea(form):
    """Valida el formulario de alta/edicion. Devuelve (data_dict, errores)."""
    errores = []

    titulo = (form.get("title") or "").strip()
    if not titulo:
        errores.append("El titulo no puede estar vacio.")
    elif len(titulo) > MAX_TITLE_LEN:
        errores.append(f"El titulo supera los {MAX_TITLE_LEN} caracteres.")

    fecha = (form.get("due_date") or "").strip()
    if not fecha:
        errores.append("La fecha limite es obligatoria.")
    else:
        try:
            datetime.strptime(fecha, _TODAY_FMT)
        except ValueError:
            errores.append("La fecha debe tener formato AAAA-MM-DD.")

    minutos = form.get("estimated_minutes", type=int)
    if minutos is None or minutos <= 0:
        errores.append("La duracion debe ser mayor a 0 minutos.")
    elif minutos > MAX_MINUTES:
        errores.append(f"La duracion no puede superar {MAX_MINUTES} minutos.")

    prioridad = form.get("priority_level", 2, type=int)
    if prioridad not in (1, 2, 3):
        errores.append("La prioridad debe ser Alta (1), Media (2) o Baja (3).")

    if errores:
        return None, errores

    return {
        "title": titulo,
        "description": (form.get("description") or "").strip()[:500],
        "category": (form.get("category") or "General").strip()[:40] or "General",
        "priority_level": prioridad,
        "due_date": fecha,
        "estimated_minutes": minutos,
        "start_time": (form.get("start_time") or "").strip() or None,
        "end_time": (form.get("end_time") or "").strip() or None,
        "kanban_column": form.get("kanban_column", "todo"),
    }, []


# --------------------------------------------------------------------------
# US8 - Revision del dia + US2 ranking + progreso
# --------------------------------------------------------------------------

@planner.route("/planner")
@security.requires("planner.ver")
def dia():
    user_id = security.current_user_id()
    hoy = _hoy()
    available = request.args.get("available", 120, type=int)

    tareas_hoy = repo_tasks.list_by_day(user_id, hoy)
    ranked = scoring.rank_tasks(tareas_hoy, available)
    progreso = repo_tasks.daily_progress(user_id, hoy)

    import repo_users
    todos = repo_users.list_users(limit=100)
    usuarios = [u for u in todos if u["id"] != user_id and u.get("is_active", 1)]

    return render_template(
        "planner/dia.html",
        tareas=ranked,
        hoy=hoy,
        available_minutes=available,
        progreso=progreso,
        usuarios=usuarios,
    )


# --------------------------------------------------------------------------
# US1 - CRUD de tareas
# --------------------------------------------------------------------------

@planner.route("/v2/tasks", methods=["POST"])
@security.requires("planner.crear")
def crear_tarea():
    user_id = security.current_user_id()
    datos, errores = _validar_tarea(request.form)

    if errores:
        for e in errores:
            flash(e, "error")
        return redirect(url_for("planner.dia"))

    # US10: asignacion - solo si tiene el permiso y el campo viene relleno
    owner_id = user_id
    assigned_by = None
    assigned_to = request.form.get("assigned_to", type=int)
    if assigned_to and security.has_permission("tarea.asignar"):
        owner_id = assigned_to
        assigned_by = user_id

    repo_tasks.create(datos, owner_id, assigned_by)
    flash("Actividad creada.", "ok")
    return redirect(url_for("planner.dia"))


@planner.route("/v2/tasks/<int:task_id>/edit", methods=["POST"])
@security.requires("planner.editar")
def editar_tarea(task_id):
    user_id = security.current_user_id()
    tarea = repo_tasks.get_owned(task_id, user_id)
    if tarea is None:
        abort(404)   # 404, NO 403: TC-08

    datos, errores = _validar_tarea(request.form)
    if errores:
        for e in errores:
            flash(e, "error")
        return redirect(url_for("planner.dia"))

    repo_tasks.update_owned(task_id, user_id, datos)
    flash("Actividad actualizada.", "ok")
    return redirect(url_for("planner.dia"))


@planner.route("/v2/tasks/<int:task_id>/delete", methods=["POST"])
@security.requires("planner.eliminar")
def eliminar_tarea(task_id):
    user_id = security.current_user_id()
    if not repo_tasks.delete_owned(task_id, user_id):
        abort(404)
    flash("Actividad eliminada.", "ok")
    return redirect(url_for("planner.dia"))


# --------------------------------------------------------------------------
# US3/US9 - Mover columna Kanban
# --------------------------------------------------------------------------

@planner.route("/v2/tasks/<int:task_id>/column", methods=["POST"])
@security.requires("kanban.mover")
def mover_columna(task_id):
    user_id = security.current_user_id()
    column = (request.form.get("column") or request.json and request.json.get("column") or "").strip()

    if column not in KANBAN_COLUMNS:
        abort(400, description=f"Columna '{column}' no valida. Usa: {', '.join(KANBAN_COLUMNS)}.")

    if not repo_tasks.move_column(task_id, user_id, column):
        abort(404)

    # Si la peticion viene del kanban.js (fetch), responde JSON
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "column": column})

    return redirect(url_for("planner.kanban"))


# --------------------------------------------------------------------------
# US9 - Tablero Kanban
# --------------------------------------------------------------------------

@planner.route("/kanban")
@security.requires("kanban.ver")
def kanban():
    user_id = security.current_user_id()
    board = repo_tasks.list_board(user_id)
    return render_template("planner/kanban.html", board=board, columnas=KANBAN_COLUMNS)


# --------------------------------------------------------------------------
# US10 - Tareas asignadas por este usuario
# --------------------------------------------------------------------------

@planner.route("/equipo/tareas")
@security.requires("planner.ver")
def equipo_tareas():
    user_id = security.current_user_id()
    tareas = repo_tasks.list_assigned_by(user_id)

    # Agrupar por destinatario para la vista
    por_persona = {}
    for t in tareas:
        nombre = t.get("assignee_username", "Desconocido")
        por_persona.setdefault(nombre, []).append(t)

    return render_template("planner/equipo.html", por_persona=por_persona)


# --------------------------------------------------------------------------
# US4 - API de desglose del puntaje (TC-4.2: solo tareas propias)
# --------------------------------------------------------------------------

@planner.route("/v2/api/task/<int:task_id>/score-breakdown")
@security.login_required
def score_breakdown(task_id):
    user_id = security.current_user_id()
    available = request.args.get("available", 120, type=int)

    tarea = repo_tasks.get_owned(task_id, user_id)
    if tarea is None:
        import database
        tarea = database.get_task_by_id(task_id)
    if tarea is None:
        return jsonify({"error": "not found"}), 404

    total, breakdown = scoring.calculate_score(tarea, available)
    return jsonify({"id": task_id, "total": total, "breakdown": breakdown})
