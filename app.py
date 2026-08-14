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
from calendar_bp import calendar_bp
from habits import habitos as habitos_bp
from home import home as home_bp, register_menu
from perfil import perfil as perfil_bp

app = Flask(__name__)          # <-- NO TOCAR ESTA LÍNEA

app.secret_key = config.SECRET_KEY

app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE

database.init_db()

# --------------------------------------------------------------------------
# v2 - NÚCLEO Y MÓDULOS
# --------------------------------------------------------------------------
security.init_app(app)      # CSRF global + helpers de plantilla
register_menu(app)          # menú filtrado por permisos

app.register_blueprint(auth_bp)        # /register /login /logout
app.register_blueprint(home_bp)        # /inicio
app.register_blueprint(admin_bp)       # /admin/usuarios
app.register_blueprint(perfil_bp)      # /perfil
app.register_blueprint(calendar_bp)    # /calendario /eventos /invitacion
app.register_blueprint(habitos_bp)     # /habitos /metricas /admin/metricas


@app.errorhandler(400)
def _error_400(e):
    return render_template("errors/400.html", descripcion=getattr(e, "description", None)), 400


@app.errorhandler(403)
def _error_403(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def _error_404(e):
    return render_template("errors/404.html"), 404


DEFAULT_AVAILABLE_MINUTES = 120

MAX_TITLE_LEN = 120
MAX_MINUTES = 1440              # 24 h: más que eso no cabe en un día
VALID_PRIORITIES = (1, 2, 3)


@app.teardown_appcontext
def _close_db(exception=None):
    database.close_db(exception)


def _leer_minutos_disponibles():
    valor = request.args.get("available", DEFAULT_AVAILABLE_MINUTES, type=int)
    if valor is None:
        return DEFAULT_AVAILABLE_MINUTES
    return max(0, min(valor, MAX_MINUTES))


def _validar_formulario_tarea(form):
    errores = []

    titulo = (form.get("title") or "").strip()
    if not titulo:
        errores.append("El título no puede estar vacío. Escribe qué actividad quieres registrar.")
    elif len(titulo) > MAX_TITLE_LEN:
        errores.append(f"El título es muy largo. Usa {MAX_TITLE_LEN} caracteres o menos.")

    fecha_txt = (form.get("due_date") or "").strip()
    if not fecha_txt:
        errores.append("Falta la fecha límite. Indícala en formato AAAA-MM-DD.")
    else:
        try:
            datetime.strptime(fecha_txt, "%Y-%m-%d")
        except ValueError:
            errores.append(f"La fecha «{fecha_txt}» no es válida. Usa el formato AAAA-MM-DD, por ejemplo 2026-08-20.")

    minutos_txt = (form.get("estimated_minutes") or "").strip()
    minutos = form.get("estimated_minutes", type=int)
    if not minutos_txt:
        minutos = 30
    elif minutos is None:
        errores.append(f"La duración «{minutos_txt}» no es un número. Escribe los minutos, por ejemplo 45.")
    elif minutos <= 0:
        errores.append("La duración debe ser mayor a 0 minutos.")
    elif minutos > MAX_MINUTES:
        errores.append(f"La duración no puede pasar de {MAX_MINUTES} minutos (24 horas).")

    prioridad = form.get("priority_level", 2, type=int)
    if prioridad is None:
        prioridad = 2
    if prioridad not in VALID_PRIORITIES:
        errores.append("La prioridad debe ser Alta, Media o Baja.")

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


# ======================================================================
# RUTAS v1 RETIRADAS  (auditoria de integracion, 2026-08-14)
# ----------------------------------------------------------------------
# Aqui vivian las cinco rutas heredadas de la v1:
#
#     GET  /                                 -> index.html con TODAS las tareas
#     POST /tasks                            -> crear
#     POST /tasks/<id>/delete                -> eliminar
#     POST /tasks/<id>/status                -> cambiar estado
#     GET  /api/task/<id>/score-breakdown    -> desglose del puntaje
#
# Se retiran por DOS razones, no una:
#
# 1. SEGURIDAD. Ninguna llevaba @login_required ni @requires. Cualquiera sin
#    sesion podia leer las tareas de todo el mundo en `GET /`, crear tareas y
#    BORRARLAS (verificado: HTTP 302 y la fila desaparecio). Ademas
#    `database.get_daily_progress()` cuenta las tareas de TODA la base, asi que
#    la barra de progreso mezclaba el trabajo de desconocidos. Con `tasks` sin
#    columna `user_id`, esto no se puede arreglar poniendo un decorador: no hay
#    forma de saber de quien es cada fila. Rompia TC-08 y TC-11, los dos casos
#    criticos que bloquean el release.
#
# 2. COLISION CON EL MODULO B. `/tasks` y `/api/task/<id>/score-breakdown` son
#    exactamente los endpoints que trae el blueprint de Lucero. Al registrarse,
#    Flask conserva la primera regla que coincide y la suya quedaria muerta sin
#    un solo error en consola: un dia entero de depuracion.
#
# `templates/index.html`, `static/js/main.js` y las funciones v1 de
# `database.py` (get_tasks, add_task, update_status, delete_task,
# get_daily_progress) quedan sin usar. NO se borran todavia: son la referencia
# de la que parte Lucero. Se retiran cuando el Modulo B entre a main.


@app.route("/")
def index_route():
    """La portada es el home del Modulo A, que si comprueba la sesion."""
    return redirect(url_for("home.index"))


def _correr_pruebas():
    """
    Los 11 asserts de Ana, reorientados tras retirar las rutas v1.

    Antes atacaban `POST /tasks` y `/api/task/<id>/score-breakdown`. Al retirar
    esas cinco rutas (ver el bloque de arriba) la suite quedo apuntando a
    endpoints que ya no existen y fallaba entera desde el primer assert.

    Se reorientan a la capa que SI sobrevive y que es justo la que hereda
    Lucero en el Modulo B: `_validar_formulario_tarea()`, las funciones v1 de
    `database.py` y la forma del desglose de `scoring.py`. Cada assert sigue
    comprobando exactamente la misma regla de negocio que comprobaba; lo unico
    que cambia es que se verifica un nivel mas abajo, sin pasar por HTTP.

    Cuando el Modulo B publique su blueprint con `/planner` y su propio
    endpoint de desglose, estos asserts deberian volver a subir a nivel HTTP
    contra las rutas nuevas.
    """
    import tempfile

    from werkzeug.datastructures import MultiDict

    fd, ruta_tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.DB_PATH = ruta_tmp
    database.init_db()

    app.config["TESTING"] = True

    base = {"title": "Tarea valida", "due_date": "2026-08-20",
            "category": "Estudio", "priority_level": "1", "estimated_minutes": "45"}

    def validar(**cambios):
        """
        Devuelve (datos, errores) tal cual los devolvia la ruta.

        MultiDict y no un dict normal: `_validar_formulario_tarea` usa
        `form.get("...", type=int)`, que es de Werkzeug. Con un dict pelado
        revienta con TypeError y estariamos probando otra cosa.
        """
        datos = dict(base)
        datos.update(cambios)
        return _validar_formulario_tarea(MultiDict(datos))

    def total_tareas():
        with app.app_context():
            return len(database.get_tasks())

    # --- 1. La tarea valida pasa la validacion Y llega a la base ---------
    datos, errores = validar()
    assert not errores, f"Assert 1 Falló: una tarea válida fue rechazada -> {errores}"
    antes = total_tareas()
    with app.app_context():
        database.add_task(datos)
    assert total_tareas() == antes + 1, "Assert 1 Falló: la tarea válida no se insertó"

    # --- 2-8. Cada entrada invalida se rechaza CON MENSAJE ---------------
    # Se comprueba tambien que el mensaje exista: un rechazo silencioso deja al
    # usuario sin saber que arreglar, que es el defecto que Ana venia a cerrar.
    casos = [
        (2, {"title": "   "},             "sin título"),
        (3, {"due_date": "2026-02-31"},   "el 31 de febrero"),
        (4, {"due_date": "20-08-2026"},   "una fecha DD-MM-AAAA"),
        (5, {"estimated_minutes": "0"},   "una duración de 0 minutos"),
        (6, {"estimated_minutes": "-30"}, "una duración negativa"),
        (7, {"estimated_minutes": "abc"}, "una duración no numérica"),
        (8, {"priority_level": "99"},     "una prioridad inválida"),
    ]
    for numero, cambio, descripcion in casos:
        antes = total_tareas()
        datos, errores = validar(**cambio)
        assert errores, f"Assert {numero} Falló: se aceptó {descripcion}"
        assert datos is None, f"Assert {numero} Falló: devolvió datos pese al error"
        assert total_tareas() == antes, \
            f"Assert {numero} Falló: se insertó una tarea con {descripcion}"

    # --- 9. La FORMA del desglose no cambia -----------------------------
    # Es el contrato que consume main.js y que el Modulo B tiene que respetar:
    # tres componentes, cada uno con `puntos` y `razon`.
    with app.app_context():
        primera = database.get_tasks()[0]
    total, desglose = scoring.calculate_score(dict(primera), 120)
    assert isinstance(total, int), "Assert 9 Falló: el puntaje total no es un entero"
    assert set(desglose.keys()) == {"prioridad", "urgencia", "tiempo"}, \
        f"Assert 9 Falló: el desglose cambió de forma y rompe main.js -> {list(desglose.keys())}"
    for clave, parte in desglose.items():
        assert set(parte.keys()) == {"puntos", "razon"}, \
            f"Assert 9 Falló: el componente «{clave}» cambió de forma -> {list(parte.keys())}"
    assert total == sum(p["puntos"] for p in desglose.values()), \
        "Assert 9 Falló: la suma del desglose no coincide con el total (TC-15)"

    # --- 10. Un id inexistente no existe --------------------------------
    with app.app_context():
        assert database.get_task_by_id(999999) is None, \
            "Assert 10 Falló: un id inexistente devolvió una tarea"

    # --- 11. Un `available` basura no revienta, se acota ------------------
    with app.test_request_context("/?available=abc"):
        assert _leer_minutos_disponibles() == DEFAULT_AVAILABLE_MINUTES, \
            "Assert 11 Falló: un parámetro available inválido no cayó al valor por defecto"
    with app.test_request_context("/?available=999999"):
        assert _leer_minutos_disponibles() == MAX_MINUTES, \
            "Assert 11 Falló: un available enorme no se acotó a 24 h"

    os.remove(ruta_tmp)
    print("SUCCESS: Todas las 11 pruebas de assert para app.py pasaron exitosamente!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        _correr_pruebas()
    else:
        app.run(debug=True)
