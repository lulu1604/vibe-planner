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
import i18n
import scoring
import security
from admin import admin as admin_bp
from auth import auth as auth_bp
from calendar_bp import calendar_bp
from habits import habitos as habitos_bp
from home import home as home_bp, register_menu
from perfil import perfil as perfil_bp
from planner import planner as planner_bp

app = Flask(__name__)          # <-- NO TOCAR ESTA LÍNEA

app.secret_key = config.SECRET_KEY

app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE

database.init_db()

# --------------------------------------------------------------------------
# v2 - NÚCLEO Y MÓDULOS
# --------------------------------------------------------------------------
security.init_app(app)      # CSRF global + helpers de plantilla
i18n.init_app(app)          # expone t() e IDIOMAS a TODAS las plantillas
register_menu(app)          # menú filtrado por permisos

app.register_blueprint(auth_bp)        # /register /login /logout
app.register_blueprint(home_bp)        # /inicio
app.register_blueprint(admin_bp)       # /admin/usuarios
app.register_blueprint(perfil_bp)      # /perfil
app.register_blueprint(calendar_bp)    # /calendario /eventos /invitacion
app.register_blueprint(habitos_bp)     # /habitos /metricas /admin/metricas
app.register_blueprint(planner_bp)     # /planner /kanban /equipo/tareas


@app.errorhandler(400)
def _error_400(e):
    return render_template("errors/400.html", descripcion=getattr(e, "description", None)), 400


@app.errorhandler(403)
def _error_403(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def _error_404(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def _error_500(e):
    """
    La red de seguridad. Sin esto, cualquier excepcion no prevista sale como la
    pagina cruda de Werkzeug -- con la traza de Python entera si `debug` esta
    activo -- en mitad de la demo. El detalle va al log; el usuario ve una
    pantalla que le dice que hacer.
    """
    app.logger.exception("Error no controlado")
    return render_template("errors/500.html"), 500


@app.teardown_appcontext
def _close_db(exception=None):
    database.close_db(exception)


# ======================================================================
# VALIDACION DE TAREAS: RETIRADA DE AQUI  (auditoria de preentrega)
# ----------------------------------------------------------------------
# Aqui vivian `_validar_formulario_tarea()`, `_leer_minutos_disponibles()` y
# sus constantes. Se retiran porque eran una SEGUNDA copia de la validacion de
# tareas, y la copia viva es `planner._validar_tarea()` del Modulo B.
#
# No era teorico: las dos ya habian divergido. `MAX_MINUTES` valia 1440 aqui y
# 480 alla, asi que la MISMA entrada (600 minutos) se aceptaba o se rechazaba
# segun a quien preguntaras. Y lo peor: los unicos asserts de validacion del
# proyecto apuntaban a esta copia, la muerta. La auditoria lo demostro
# saboteando `planner.MAX_MINUTES` a mil millones -- las suites siguieron en
# verde.
#
# Los 11 asserts de Ana pasan a probar `planner._validar_tarea`, que es la que
# de verdad decide si una actividad entra a la base.
# ======================================================================

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

    Y ahora apuntan a `planner._validar_tarea`, que es la validacion VIVA: la
    que decide de verdad si una actividad entra a la base. Antes probaban una
    copia muerta que vivia en este archivo, con limites distintos (1440 min
    frente a los 480 reales). Es decir: los unicos asserts de validacion del
    proyecto estaban comprobando codigo que no ejecutaba nadie.

    Cada assert sigue comprobando la misma regla de negocio de siempre; lo que
    cambia es que ahora la comprueba donde importa.
    """
    import tempfile

    from werkzeug.datastructures import MultiDict

    import planner
    import repo_tasks

    fd, ruta_tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.DB_PATH = ruta_tmp
    database.init_db()

    app.config["TESTING"] = True

    base = {"title": "Tarea valida", "due_date": "2026-08-20",
            "category": "Estudio", "priority_level": "1", "estimated_minutes": "45"}

    def validar(**cambios):
        """
        Devuelve (datos, errores) de la validacion viva del planner.

        MultiDict y no un dict normal: `_validar_tarea` usa
        `form.get("...", type=int)`, que es de Werkzeug. Con un dict pelado
        revienta con TypeError y estariamos probando otra cosa.
        """
        datos = dict(base)
        datos.update(cambios)
        return planner._validar_tarea(MultiDict(datos))

    # Una cuenta de verdad: `tasks_v2` tiene FK contra `users`.
    import seed
    import repo_users
    conexion = database.raw_connection()
    seed.sembrar_permisos(conexion)
    seed.sembrar_roles(conexion)
    conexion.commit()
    usuario_id = repo_users.create_user(
        {"username": "prueba", "email": "prueba@esan.pe", "password": "Vibe2026!"},
        ["usuario"], conn=conexion)
    conexion.close()

    def total_tareas():
        with app.app_context():
            return len(repo_tasks.list_by_user(usuario_id))

    # --- 1. La tarea valida pasa la validacion Y llega a la base ---------
    datos, errores = validar()
    assert not errores, f"Assert 1 Falló: una tarea válida fue rechazada -> {errores}"
    antes = total_tareas()
    with app.app_context():
        repo_tasks.create(datos, usuario_id, None)
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
        # 481 ESCRITO A MANO, no `planner.MAX_MINUTES + 1`.
        #
        # Un test que lee su expectativa del codigo que prueba no puede
        # detectar un cambio en ese codigo: sigue al sabotaje y siempre pasa.
        # Lo comprobe subiendo MAX_MINUTES a mil millones con la version
        # calculada y la suite se quedo en verde. El numero va aqui clavado
        # para que sea el TEST el que fija el contrato: 8 horas por actividad.
        (8, {"estimated_minutes": "481"}, "una duración de más de 8 horas"),
        (8, {"priority_level": "alta"},   "una prioridad no numérica"),
    ]
    for numero, cambio, descripcion in casos:
        antes = total_tareas()
        datos, errores = validar(**cambio)
        assert errores, f"Assert {numero} Falló: se aceptó {descripcion}"
        assert datos is None, f"Assert {numero} Falló: devolvió datos pese al error"
        assert total_tareas() == antes, \
            f"Assert {numero} Falló: se insertó una tarea con {descripcion}"

    # --- 9. La FORMA del desglose no cambia -----------------------------
    # Es el contrato que consume puntaje.js: tres componentes, cada uno con
    # `puntos` y `razon`.
    with app.app_context():
        primera = repo_tasks.list_by_user(usuario_id)[0]
    total, desglose = scoring.calculate_score(dict(primera), 120)
    assert isinstance(total, int), "Assert 9 Falló: el puntaje total no es un entero"
    assert set(desglose.keys()) == {"prioridad", "urgencia", "tiempo"}, \
        f"Assert 9 Falló: el desglose cambió de forma y rompe main.js -> {list(desglose.keys())}"
    for clave, parte in desglose.items():
        assert set(parte.keys()) == {"puntos", "razon"}, \
            f"Assert 9 Falló: el componente «{clave}» cambió de forma -> {list(parte.keys())}"
    assert total == sum(p["puntos"] for p in desglose.values()), \
        "Assert 9 Falló: la suma del desglose no coincide con el total (TC-15)"

    # --- 10. Una tarea ajena no existe para quien pregunta ---------------
    # `get_owned` lleva el user_id DENTRO del WHERE: es la regla de las dos
    # llaves, y es lo que hace que una tarea de otro devuelva 404 y no 403.
    with app.app_context():
        assert repo_tasks.get_owned(999999, usuario_id) is None, \
            "Assert 10 Falló: un id inexistente devolvió una tarea"
        propia = repo_tasks.list_by_user(usuario_id)[0]
        assert repo_tasks.get_owned(propia["id"], usuario_id + 999) is None, \
            "Assert 10 Falló: una tarea ajena fue accesible (TC-08)"

    # --- 11. Las horas y la columna se validan, no se guardan crudas ------
    _, errores = validar(start_time="25:99")
    assert errores, "Assert 11 Falló: se aceptó una hora inexistente"
    _, errores = validar(kanban_column="inventada")
    assert errores, "Assert 11 Falló: se aceptó una columna que no existe"
    datos, errores = validar(start_time="09:00", end_time="08:00")
    assert errores, "Assert 11 Falló: se aceptó una hora de fin anterior al inicio"

    os.remove(ruta_tmp)
    print("SUCCESS: Todas las 11 pruebas de assert para app.py pasaron exitosamente!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        _correr_pruebas()
    else:
        app.run(debug=True)
