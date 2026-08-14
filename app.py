"""
VibePlanner - Controlador Flask
--------------------------------------------------
DUEÑO DE ESTE ARCHIVO: Ana Cusi (rutas y despliegue)

REGLA CRÍTICA: la instancia de Flask se llama EXACTAMENTE `app` y está definida
a nivel de módulo. PythonAnywhere hace `from app import app`. No usar
application factory, no renombrar a `application`.

CONTRATO CONGELADO CON EL FRONTEND (Piero) - no cambiar sin avisar al grupo:
    GET  /                                      -> index.html con tasks, available_minutes, progress
    POST /tasks                                 -> crea actividad
    POST /tasks/<id>/delete                     -> elimina actividad
    POST /tasks/<id>/status                     -> cambia estado
    GET  /api/task/<id>/score-breakdown?available=N
         -> {"id": int, "total": int, "breakdown": ...}
         -> 404 {"error": "not found"}
"""

import os
from datetime import datetime

from flask import Flask, flash, get_flashed_messages, jsonify, redirect, render_template, request, url_for

import config
import database
import scoring
import security
from admin import admin as admin_bp
from auth import auth as auth_bp
from home import home as home_bp, register_menu
from perfil import perfil as perfil_bp

app = Flask(__name__)          # <-- NO TOCAR ESTA LÍNEA

# Necesaria para flash(): así los errores de validación llegan al usuario.
# En PythonAnywhere se puede definir VIBEPLANNER_SECRET como variable de entorno.
app.secret_key = config.SECRET_KEY

# v2: endurecido de la cookie de sesión. HTTPONLY impide que un XSS la lea;
# SAMESITE=Lax hace que el navegador no la envíe en peticiones de otro sitio.
app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE

# Inicializar esquema SQLite automáticamente al cargar el módulo WSGI
# (v2: init_db() crea además las 5 tablas de identidad de schema_v2.sql)
database.init_db()

# --------------------------------------------------------------------------
# v2 - NÚCLEO (Piero, Módulo A). Nada de esto altera las rutas de la v1.
# --------------------------------------------------------------------------
security.init_app(app)      # CSRF global + helpers de plantilla
register_menu(app)          # menú filtrado por permisos, para base.html

app.register_blueprint(auth_bp)      # /register /login /logout
app.register_blueprint(home_bp)      # /inicio
app.register_blueprint(admin_bp)     # /admin/usuarios
app.register_blueprint(perfil_bp)    # /perfil


@app.errorhandler(400)
def _error_400(e):
    # Casi siempre es el token CSRF caducado. `e.description` trae el texto
    # concreto que puso quien llamó a abort().
    return render_template("errors/400.html", descripcion=getattr(e, "description", None)), 400


@app.errorhandler(403)
def _error_403(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def _error_404(e):
    return render_template("errors/404.html"), 404

# Tiempo disponible por defecto (minutos). US2/US4 lo usan para el bono de tiempo.
DEFAULT_AVAILABLE_MINUTES = 120

# Límites de validación
MAX_TITLE_LEN = 120
MAX_MINUTES = 1440              # 24 h: más que eso no cabe en un día
VALID_PRIORITIES = (1, 2, 3)


@app.teardown_appcontext
def _close_db(exception=None):
    database.close_db(exception)


# --------------------------------------------------------------------------
# Helpers de validación (servidor). No confiar en el HTML: el navegador se
# puede saltar `required` y `min` con DevTools o con un POST hecho a mano.
# --------------------------------------------------------------------------

def _leer_minutos_disponibles():
    """Lee `available` del querystring y lo acota a un rango sensato."""
    valor = request.args.get("available", DEFAULT_AVAILABLE_MINUTES, type=int)
    if valor is None:
        return DEFAULT_AVAILABLE_MINUTES
    return max(0, min(valor, MAX_MINUTES))


def _validar_formulario_tarea(form):
    """
    Valida el formulario de creación de actividad.

    Devuelve (datos, errores):
      - datos:   dict listo para database.add_task(), o None si hubo errores
      - errores: lista de mensajes en español que dicen qué pasó y cómo arreglarlo
    """
    errores = []

    # --- Título: obligatorio y acotado ---
    titulo = (form.get("title") or "").strip()
    if not titulo:
        errores.append("El título no puede estar vacío. Escribe qué actividad quieres registrar.")
    elif len(titulo) > MAX_TITLE_LEN:
        errores.append(f"El título es muy largo. Usa {MAX_TITLE_LEN} caracteres o menos.")

    # --- Fecha límite: obligatoria y en formato YYYY-MM-DD real ---
    # No basta con revisar el patrón: "2026-02-31" tiene el formato correcto
    # pero no existe. strptime lo rechaza, una expresión regular no.
    fecha_txt = (form.get("due_date") or "").strip()
    if not fecha_txt:
        errores.append("Falta la fecha límite. Indícala en formato AAAA-MM-DD.")
    else:
        try:
            datetime.strptime(fecha_txt, "%Y-%m-%d")
        except ValueError:
            errores.append(f"La fecha «{fecha_txt}» no es válida. Usa el formato AAAA-MM-DD, por ejemplo 2026-08-20.")

    # --- Duración estimada: entero mayor que 0 ---
    # request.form.get(type=int) devuelve None si el texto no es un entero,
    # así distinguimos "no es número" de "es un número inválido".
    minutos_txt = (form.get("estimated_minutes") or "").strip()
    minutos = form.get("estimated_minutes", type=int)
    if not minutos_txt:
        minutos = 30                                  # valor por defecto razonable
    elif minutos is None:
        errores.append(f"La duración «{minutos_txt}» no es un número. Escribe los minutos, por ejemplo 45.")
    elif minutos <= 0:
        errores.append("La duración debe ser mayor a 0 minutos.")
    elif minutos > MAX_MINUTES:
        errores.append(f"La duración no puede pasar de {MAX_MINUTES} minutos (24 horas).")

    # --- Prioridad: solo 1, 2 o 3 ---
    prioridad = form.get("priority_level", 2, type=int)
    if prioridad is None:
        prioridad = 2
    if prioridad not in VALID_PRIORITIES:
        errores.append("La prioridad debe ser Alta, Media o Baja.")

    # --- Categoría: libre pero acotada ---
    categoria = (form.get("category") or "General").strip() or "General"
    categoria = categoria[:40]

    if errores:
        return None, errores

    return {
        "title": titulo,
        "category": categoria,
        "priority_level": prioridad,
        "due_date": fecha_txt,
        "estimated_minutes": minutos,
    }, []


def _volver_al_inicio():
    """Redirige al dashboard conservando el tiempo disponible que el usuario tenía."""
    disponible = request.form.get("available", type=int)
    if disponible is None:
        return redirect(url_for("index_route"))
    return redirect(url_for("index_route", available=max(0, min(disponible, MAX_MINUTES))))


# --------------------------------------------------------------------------
# US2 - Ver el plan del día ordenado
# --------------------------------------------------------------------------
@app.route("/")
def index_route():
    available = _leer_minutos_disponibles()
    tasks = database.get_tasks()
    ranked = scoring.rank_tasks(tasks, available)
    progress = database.get_daily_progress()
    return render_template(
        "index.html",
        tasks=ranked,
        available_minutes=available,
        progress=progress,
    )


# --------------------------------------------------------------------------
# US1 - Crear / editar / eliminar actividades
# --------------------------------------------------------------------------
@app.route("/tasks", methods=["POST"])
def add_task_route():
    datos, errores = _validar_formulario_tarea(request.form)

    if errores:
        # No se inserta nada. Los mensajes viajan por flash() y los pinta el
        # frontend con get_flashed_messages().
        for mensaje in errores:
            flash(mensaje, "error")
        return _volver_al_inicio()

    database.add_task(datos)
    flash("Actividad agregada.", "ok")
    return _volver_al_inicio()


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])   # POST, nunca GET
def delete_task_route(task_id):
    if database.delete_task(task_id):
        flash("Actividad eliminada.", "ok")
    else:
        flash("Esa actividad ya no existe. Actualiza la página.", "error")
    return _volver_al_inicio()


# --------------------------------------------------------------------------
# US3 - Cambiar estado y ver progreso
# --------------------------------------------------------------------------
@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_status_route(task_id):
    new_status = request.form.get("status", "pending")
    # database.update_status() ya rechaza estados fuera de la lista blanca y
    # devuelve False; acá solo traducimos ese False a un mensaje para el usuario.
    if not database.update_status(task_id, new_status):
        flash("No se pudo cambiar el estado. Vuelve a intentarlo.", "error")
    return _volver_al_inicio()


# --------------------------------------------------------------------------
# US4 - Explicabilidad: desglose del puntaje
# --------------------------------------------------------------------------
@app.route("/api/task/<int:task_id>/score-breakdown")
def score_breakdown_route(task_id):
    available = _leer_minutos_disponibles()
    task = database.get_task_by_id(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404
    total, breakdown = scoring.calculate_score(task, available)
    return jsonify({"id": task_id, "total": total, "breakdown": breakdown})


# --------------------------------------------------------------------------
# PRUEBAS DE RUTAS Y VALIDACIÓN (EVIDENCIA DE TESTING DE ANA)
#
#   python app.py test   -> corre los asserts sobre una base temporal
#   python app.py        -> levanta el servidor de desarrollo
# --------------------------------------------------------------------------
def _correr_pruebas():
    import tempfile

    # Base temporal: las pruebas nunca tocan vibe_planner.db real.
    fd, ruta_tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.DB_PATH = ruta_tmp
    database.init_db()

    app.config["TESTING"] = True
    cliente = app.test_client()

    # v2: ahora TODO POST lleva token CSRF. Se planta en la sesión del cliente
    # de pruebas y se añade al formulario base — exactamente lo que hace el
    # navegador con el <input type="hidden" name="_csrf"> que traen las
    # plantillas. Los 11 asserts siguen probando lo mismo que probaban.
    CSRF = "token-de-prueba"
    with cliente.session_transaction() as sesion:
        sesion["_csrf"] = CSRF

    def total_tareas():
        with app.app_context():
            return len(database.get_tasks())

    base = {"title": "Tarea valida", "due_date": "2026-08-20",
            "category": "Estudio", "priority_level": "1", "estimated_minutes": "45",
            "_csrf": CSRF}

    def enviar(**cambios):
        datos = dict(base)
        datos.update(cambios)
        return cliente.post("/tasks", data=datos)

    # Assert 1: una tarea válida sí se inserta y redirige
    antes = total_tareas()
    r = enviar()
    assert r.status_code == 302, "Assert 1 Falló: la tarea válida no redirigió"
    assert total_tareas() == antes + 1, "Assert 1 Falló: la tarea válida no se insertó"

    # Assert 2: título vacío se rechaza
    antes = total_tareas()
    enviar(title="   ")
    assert total_tareas() == antes, "Assert 2 Falló: se insertó una tarea sin título"

    # Assert 3: fecha con formato correcto pero inexistente (31 de febrero)
    antes = total_tareas()
    enviar(due_date="2026-02-31")
    assert total_tareas() == antes, "Assert 3 Falló: se aceptó el 31 de febrero"

    # Assert 4: fecha en formato equivocado
    antes = total_tareas()
    enviar(due_date="20-08-2026")
    assert total_tareas() == antes, "Assert 4 Falló: se aceptó una fecha DD-MM-AAAA"

    # Assert 5: duración de 0 minutos se rechaza
    antes = total_tareas()
    enviar(estimated_minutes="0")
    assert total_tareas() == antes, "Assert 5 Falló: se aceptó una duración de 0 minutos"

    # Assert 6: duración negativa se rechaza
    antes = total_tareas()
    enviar(estimated_minutes="-30")
    assert total_tareas() == antes, "Assert 6 Falló: se aceptó una duración negativa"

    # Assert 7: duración no numérica se rechaza
    antes = total_tareas()
    enviar(estimated_minutes="abc")
    assert total_tareas() == antes, "Assert 7 Falló: se aceptó una duración no numérica"

    # Assert 8: prioridad fuera de 1-3 se rechaza
    antes = total_tareas()
    enviar(priority_level="99")
    assert total_tareas() == antes, "Assert 8 Falló: se aceptó una prioridad inválida"

    # Assert 9: el contrato JSON que consume el frontend de Ana sigue intacto
    with app.app_context():
        primera = database.get_tasks()[0]
    r = cliente.get(f"/api/task/{primera['id']}/score-breakdown?available=120")
    assert r.status_code == 200, "Assert 9 Falló: el endpoint de desglose no respondió 200"
    payload = r.get_json()
    assert set(payload.keys()) == {"id", "total", "breakdown"}, \
        f"Assert 9 Falló: el JSON cambió de forma y rompe main.js -> {list(payload.keys())}"

    # Assert 10: id inexistente devuelve 404 y no revienta
    r = cliente.get("/api/task/999999/score-breakdown")
    assert r.status_code == 404, "Assert 10 Falló: un id inexistente no devolvió 404"

    # Assert 11: un `available` basura no tumba la página
    assert cliente.get("/?available=abc").status_code == 200, \
        "Assert 11 Falló: un parámetro available inválido rompió el dashboard"

    os.remove(ruta_tmp)
    print("SUCCESS: Todas las 11 pruebas de assert para app.py pasaron exitosamente!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        _correr_pruebas()
    else:
        app.run(debug=True)
