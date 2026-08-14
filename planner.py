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

import i18n
import repo_tasks
import repo_users
import scoring
import security
import validators
from repo_tasks import KANBAN_COLUMNS

planner = Blueprint("planner", __name__, url_prefix="")

# Columnas validas: fuente unica de verdad importada de repo_tasks.py
_TODAY_FMT = "%Y-%m-%d"
_HORA_FMT = "%H:%M"
# El tope de titulo sale de validators.py, que es la fuente unica de los tres
# modulos. Antes cada uno tenia el suyo y no coincidian.
MAX_TITLE_LEN = validators.TITULO_MAX
MAX_DESC_LEN = validators.DESCRIPCION_MAX
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

    # Sin valor por defecto: `form.get("priority_level", 2, type=int)` devuelve
    # 2 cuando el texto no es un entero, asi que 'x', 'alta' y '2.5' se
    # guardaban como Media SIN avisar. Ahora un valor no numerico da None y se
    # rechaza igual que uno fuera de rango.
    prioridad = form.get("priority_level", type=int)
    if prioridad is None:
        prioridad = 2 if not (form.get("priority_level") or "").strip() else None
    if prioridad not in (1, 2, 3):
        errores.append("La prioridad debe ser Alta (1), Media (2) o Baja (3).")

    # Las horas son opcionales, pero si vienen tienen que ser horas. Antes se
    # guardaban '25:99' y 'abc' tal cual, y luego se pintaban en la pantalla.
    inicio = _parsear_hora(form.get("start_time"), "de inicio", errores)
    fin = _parsear_hora(form.get("end_time"), "de fin", errores)
    if inicio and fin and fin <= inicio:
        errores.append("La hora de fin debe ser posterior a la de inicio.")

    # Lista blanca contra la fuente unica de repo_tasks. Sin esto, un valor
    # fuera de rango llegaba al CHECK del esquema y salia un 500 crudo.
    columna = (form.get("kanban_column") or "todo").strip()
    if columna not in KANBAN_COLUMNS:
        errores.append("Esa columna del tablero no existe.")

    descripcion = (form.get("description") or "").strip()
    if len(descripcion) > MAX_DESC_LEN:
        errores.append(f"La descripcion no puede pasar de {MAX_DESC_LEN} caracteres.")

    if errores:
        return None, errores

    return {
        "title": titulo,
        "description": descripcion,
        "category": (form.get("category") or "General").strip()[:40] or "General",
        "priority_level": prioridad,
        "due_date": fecha,
        "estimated_minutes": minutos,
        "start_time": inicio,
        "end_time": fin,
        "kanban_column": columna,
    }, []


def _parsear_hora(valor, etiqueta, errores):
    """Devuelve 'HH:MM' normalizado, None si no vino, o anota el error."""
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, _HORA_FMT).strftime(_HORA_FMT)
    except ValueError:
        errores.append(f"La hora {etiqueta} no es valida. Usa el formato HH:MM.")
        return None


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
            flash(i18n.t(e), "error")
        return redirect(url_for("planner.dia"))

    # US10: asignacion - solo si tiene el permiso y el campo viene relleno
    owner_id = user_id
    assigned_by = None
    assigned_to = request.form.get("assigned_to", type=int)

    if assigned_to:
        if not security.has_permission("tarea.asignar"):
            # Antes se descartaba en silencio y el flash decia "Actividad
            # creada.": la tarea aparecia en el planner de quien la escribio y
            # nadie entendia por que no le habia llegado a la otra persona.
            flash(i18n.t("No puedes asignar actividades a otras personas."), "error")
            return redirect(url_for("planner.dia"))

        # Que exista Y este activa. Un id inexistente reventaba con un 500 por
        # la clave foranea, y uno desactivado mandaba la tarea a un agujero
        # negro: a un buzon al que nadie puede entrar.
        destinatario = repo_users.get_by_id(assigned_to)
        if destinatario is None or not destinatario["is_active"]:
            flash(i18n.t("Esa cuenta no existe o esta desactivada."), "error")
            return redirect(url_for("planner.dia"))

        owner_id = assigned_to
        assigned_by = user_id

    repo_tasks.create(datos, owner_id, assigned_by)
    if assigned_by:
        flash("Actividad asignada a %s." % destinatario["username"], "ok")
    else:
        flash(i18n.t("Actividad creada."), "ok")
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
            flash(i18n.t(e), "error")
        return redirect(url_for("planner.dia"))

    repo_tasks.update_owned(task_id, user_id, datos)
    flash(i18n.t("Actividad actualizada."), "ok")
    return redirect(url_for("planner.dia"))


@planner.route("/v2/tasks/<int:task_id>/delete", methods=["POST"])
@security.requires("planner.eliminar")
def eliminar_tarea(task_id):
    user_id = security.current_user_id()
    if not repo_tasks.delete_owned(task_id, user_id):
        abort(404)
    flash(i18n.t("Actividad eliminada."), "ok")
    return redirect(url_for("planner.dia"))


# --------------------------------------------------------------------------
# US3/US9 - Mover columna Kanban
# --------------------------------------------------------------------------

@planner.route("/v2/tasks/<int:task_id>/column", methods=["POST"])
@security.requires("kanban.mover")
def mover_columna(task_id):
    user_id = security.current_user_id()
    # `request.json` lanza 415 si el Content-Type no es JSON, asi que una
    # peticion sin el campo `column` daba un 415 crudo en vez del 400 con
    # mensaje que documenta el modulo. `silent=True` devuelve None en vez de
    # reventar.
    cuerpo = request.get_json(silent=True) or {}
    column = (request.form.get("column") or cuerpo.get("column") or "").strip()

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
@security.requires("planner.ver")
def score_breakdown(task_id):
    """
    El desglose de UNA tarea, y solo si es tuya.

    Aqui habia un respaldo que leia de la tabla `tasks` de la v1 cuando
    get_owned() no encontraba nada:

        tarea = repo_tasks.get_owned(task_id, user_id)
        if tarea is None:
            tarea = database.get_task_by_id(task_id)   # <-- sin user_id

    Como `tasks` de la v1 no tiene columna `user_id`, ese respaldo devolvia
    CUALQUIER tarea de CUALQUIER cuenta con HTTP 200. Comprobado: una cuenta
    leia el puntaje completo de una tarea ajena. Es TC-08 -- permiso no es
    propiedad -- y es uno de los tres casos que bloquean el release.

    La prueba de TC 4.2 no lo veia porque su base de prueba deja la tabla v1
    vacia: el respaldo devolvia None y salia el 404 por casualidad.

    Se retira el respaldo. Las tareas de la v1 no son de nadie y por eso no se
    pueden mostrar a nadie; las que importan viven en `tasks_v2`, que si lleva
    `user_id`.

    404 y no 403: un 403 confirmaria que ese id existe y es de otra persona.
    """
    user_id = security.current_user_id()
    available = request.args.get("available", 120, type=int)

    tarea = repo_tasks.get_owned(task_id, user_id)
    if tarea is None:
        return jsonify({"error": "not found"}), 404

    total, breakdown = scoring.calculate_score(tarea, available)
    return jsonify({"id": task_id, "total": total, "breakdown": breakdown})
