"""
VibePlanner v2 - Lógica de métricas y rachas (metrics.py)
------------------------------------------------------------------------
DUEÑA DE ESTE ARCHIVO: Ana Cusi (Módulo D - Hábitos, Métricas y Design System)

CONTRATO CONGELADO - MÓDULO D:
    daily_summary(user_id, date_iso) -> dict   # por sección + %
    habit_streak(habit_id, today_iso) -> int   # días CONSECUTIVOS
    system_metrics() -> dict                   # sólo agregados

Auxiliares públicos que consumen las vistas y las pruebas:
    hoy_iso() -> str                           # hoy en America/Lima
    racha_desde_logs(fechas_cumplidas, today_iso) -> int   # racha sin volver a la base

Este archivo no tiene rutas ni HTML: son funciones que reciben datos y
devuelven diccionarios, para que las plantillas no calculen NADA y las pruebas
puedan comprobarlo sin levantar el servidor.

Cambiar cualquiera de estas firmas obliga a AVISAR AL GRUPO antes de hacerlo.
"""

from datetime import date, datetime, timedelta, timezone

import database
import repo_events
import repo_habits

# Una racha no se busca hacia atrás hasta el principio de los tiempos: sin
# ventana, la consulta crece sin límite conforme envejece la cuenta. 400 días
# cubre más de un año seguido; una racha más larga que la ventana se mostraría
# recortada a 400, que es un problema que preferimos tener.
VENTANA_RACHA = 400

# Nombres de tabla para el PRAGMA. Son constantes del módulo A PROPÓSITO: el
# PRAGMA no acepta parámetros con ?, así que el nombre se interpola, y lo único
# seguro es que nunca venga de una petición.
TABLA_TAREAS = "tasks"

# Orden fijo de las secciones. Una pantalla que reordena sus bloques en cada
# recarga se siente rota, aunque los números sean correctos.
SECCIONES_PREFERENTES = ("Trabajo", "Personal", "Actividades")


def hoy_iso():
    """
    La fecha de hoy en America/Lima, en ISO YYYY-MM-DD.

    No es `date.today()`: PythonAnywhere corre en UTC y a partir de las 19:00
    hora de Lima ya es "mañana" para el servidor. Sin esto, la racha de un
    usuario se rompería sola cada tarde.
    """
    try:
        from zoneinfo import ZoneInfo
        ahora = datetime.now(ZoneInfo("America/Lima"))
    except Exception:
        # Algunos Windows no traen la base de datos de zonas horarias. Lima no
        # aplica horario de verano, así que el offset fijo es exacto.
        ahora = datetime.now(timezone(timedelta(hours=-5)))
    return ahora.date().isoformat()


def _porcentaje(parte, total):
    """
    El porcentaje protegido contra la división entre cero.

    TODA división del módulo pasa por aquí. Una cuenta recién creada abre
    /metricas con cero de todo, y si eso da un 500 es lo primero que ve un
    usuario nuevo (TC-38).
    """
    if not total or total <= 0:
        return 0.0
    return round(parte / total * 100, 1)


def _columnas(tabla):
    """
    Las columnas que la tabla tiene AHORA MISMO.

    Preguntar en vez de suponer permite que /metricas funcione hoy y se llene
    sola en cuanto el Módulo B añada `user_id` a `tasks`, sin tocar una línea
    de aquí.
    """
    return {fila["name"] for fila in database.get_db().execute("PRAGMA table_info(%s)" % tabla)}


# --------------------------------------------------------------------------
# Rachas
# --------------------------------------------------------------------------

def racha_desde_logs(fechas_cumplidas, today_iso):
    """
    La racha a partir de un conjunto de fechas ISO ya cargado en memoria.

    Existe separada de `habit_streak` para que la pantalla de hábitos, que ya
    trae los registros de todos los hábitos en UNA consulta, pueda calcular
    todas las rachas sin volver a la base una vez por hábito (N+1).
    """
    hoy = date.fromisoformat(today_iso)
    racha = 0
    cursor = hoy
    if cursor.isoformat() not in fechas_cumplidas:
        cursor -= timedelta(days=1)
    while cursor.isoformat() in fechas_cumplidas:
        racha += 1
        cursor -= timedelta(days=1)
    return racha


def habit_streak(habit_id, today_iso):
    """
    Días CONSECUTIVOS cumplidos terminando hoy (o ayer, si hoy aún no se marcó).

    No son cumplimientos totales: con el 17 y el 19 cumplidos pero el 18 no, la
    racha del día 19 es 1, no 2 (TC-36).

    El retroceso de un día cuando hoy no está marcado es deliberado: sin él, un
    usuario que todavía no ha marcado hoy vería su racha en 0 y pensaría que la
    perdió (TC-35).
    """
    hoy = date.fromisoformat(today_iso)
    desde = (hoy - timedelta(days=VENTANA_RACHA)).isoformat()

    cumplidos = {
        fila["log_date"]
        for fila in repo_habits.logs_range(habit_id, desde, today_iso)
        if fila["done"]
    }
    return racha_desde_logs(cumplidos, today_iso)


# --------------------------------------------------------------------------
# Resumen del día
# --------------------------------------------------------------------------

def _ordenar_secciones(nombres):
    """Trabajo, Personal y Actividades primero; el resto alfabéticamente."""
    preferentes = [n for n in SECCIONES_PREFERENTES if n in nombres]
    resto = sorted(n for n in nombres if n not in SECCIONES_PREFERENTES)
    return preferentes + resto


def _resumen_tareas(user_id, date_iso):
    """
    Las tareas del día agrupadas por categoría.

    Devuelve (secciones, totales, conectadas). Si `tasks` todavía no tiene
    `user_id` -- el Módulo B aún no la ha migrado -- devuelve todo en cero con
    conectadas=False, para que la pantalla diga "no está conectado" en vez de
    enseñar un 0 % que parece un dato real.
    """
    columnas = _columnas(TABLA_TAREAS)
    if "user_id" not in columnas:
        return {}, {"completadas": 0, "total": 0, "porcentaje": 0.0}, False

    # Una tarea cuenta como completada por su estado o, si el Módulo B ya
    # añadió el Kanban, por estar en la columna final.
    if "kanban_column" in columnas:
        completada = "(status = 'completed' OR kanban_column = 'done')"
    else:
        completada = "(status = 'completed')"

    db = database.get_db()
    filas = db.execute(
        """SELECT category AS seccion,
                  COUNT(*) AS total,
                  SUM(CASE WHEN %s THEN 1 ELSE 0 END) AS completadas
           FROM   tasks
           WHERE  user_id = ? AND due_date = ?
           GROUP  BY category""" % completada,
        (user_id, date_iso),
    ).fetchall()

    crudas = {}
    for fila in filas:
        nombre = fila["seccion"] or "General"
        crudas[nombre] = {
            "completadas": fila["completadas"] or 0,
            "total": fila["total"] or 0,
        }

    secciones = {}
    for nombre in _ordenar_secciones(crudas.keys()):
        datos = crudas[nombre]
        secciones[nombre] = {
            "completadas": datos["completadas"],
            "total": datos["total"],
            "porcentaje": _porcentaje(datos["completadas"], datos["total"]),
        }

    hechas = sum(s["completadas"] for s in secciones.values())
    todas = sum(s["total"] for s in secciones.values())
    totales = {
        "completadas": hechas,
        "total": todas,
        "porcentaje": _porcentaje(hechas, todas),
    }
    return secciones, totales, True


def daily_summary(user_id, date_iso):
    """
    "¿Cómo me fue hoy?" en un diccionario.

    Los hábitos van en su propia clave y SIN porcentaje a propósito: son un
    indicador distinto del de tareas y mezclarlos hace que el número deje de
    significar nada (TC-39). Al no existir la clave, nadie la puede sumar por
    descuido.
    """
    secciones, tareas, conectadas = _resumen_tareas(user_id, date_iso)

    habitos = repo_habits.list_by_user(user_id)
    registros = repo_habits.logs_of_day_by_user(user_id, date_iso)
    marcados = sum(1 for h in habitos if registros.get(h["id"], {}).get("done"))

    return {
        "fecha": date_iso,
        "secciones": secciones,
        "tareas": tareas,
        "habitos": {"marcados": marcados, "total": len(habitos)},
        "eventos": len(repo_events.list_day(user_id, date_iso)),
        "tareas_conectadas": conectadas,
    }


# --------------------------------------------------------------------------
# Métricas del sistema
# --------------------------------------------------------------------------

def system_metrics():
    """
    Agregados de todo el sistema. SÓLO números.

    Ni títulos de tareas, ni nombres de eventos, ni correos: administrar el
    sistema no es leer la vida privada de las personas (TC-41). Si algún valor
    de este diccionario fuera una cadena escrita por alguien, estaría mal.
    """
    db = database.get_db()
    hoy = hoy_iso()

    usuarios_total = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    usuarios_activos = db.execute(
        "SELECT COUNT(*) AS n FROM users WHERE is_active = 1"
    ).fetchone()["n"]
    eventos_total = db.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
    habitos_total = db.execute(
        "SELECT COUNT(*) AS n FROM habits WHERE is_active = 1"
    ).fetchone()["n"]

    # Excepción justificada a "todo habit_logs pasa por repo_habits": esto es un
    # agregado de TODO el sistema, no la lectura de los hábitos de un usuario, y
    # el repositorio -- que filtra siempre por user_id -- no es el sitio para
    # una consulta que deliberadamente cruza a todos los usuarios.
    activos = {
        fila["user_id"]
        for fila in db.execute(
            """SELECT DISTINCT h.user_id AS user_id
               FROM   habit_logs l
               JOIN   habits h ON h.id = l.habit_id
               WHERE  l.log_date = ?""",
            (hoy,),
        )
    }

    if "user_id" in _columnas(TABLA_TAREAS):
        activos |= {
            fila["user_id"]
            for fila in db.execute(
                "SELECT DISTINCT user_id FROM tasks WHERE due_date = ?", (hoy,)
            )
        }

    return {
        "usuarios_total": usuarios_total,
        "usuarios_activos": usuarios_activos,
        "eventos_total": eventos_total,
        "habitos_total": habitos_total,
        "usaron_hoy": len(activos),
    }


# --------------------------------------------------------------------------
# PRUEBAS DE ASSERT DE LAS MÉTRICAS (EVIDENCIA DE TESTING DE ANA)
#   python metrics.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import tempfile

    from flask import Flask

    descriptor, ruta_temporal = tempfile.mkstemp(suffix=".db")
    os.close(descriptor)
    database.DB_PATH = ruta_temporal
    database.init_db()

    conexion = database.raw_connection()
    conexion.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (1, 'ana', 'ana@test.local', 'x')"
    )
    conexion.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (2, 'nueva', 'nueva@test.local', 'x')"
    )
    conexion.commit()
    conexion.close()

    aplicacion = Flask(__name__)

    with aplicacion.app_context():
        habito = repo_habits.create(
            {"name": "Dormir 8 horas", "habit_type": "sueno",
             "target_value": 8, "unit": "horas"},
            user_id=1,
        )

        # Assert 1: racha 3 -> 4 al marcar hoy (TC-35).
        # Cumplidos el 17, 18 y 19; hoy es el 20 y aún no se ha marcado.
        for dia in ("2026-08-17", "2026-08-18", "2026-08-19"):
            repo_habits.upsert_log(habito, dia, 8, True)
        assert habit_streak(habito, "2026-08-20") == 3, \
            "Assert 1 Falló: la racha con hoy sin marcar debería ser 3 (TC-35)"
        repo_habits.upsert_log(habito, "2026-08-20", 8, True)
        assert habit_streak(habito, "2026-08-20") == 4, \
            "Assert 1 Falló: al marcar hoy la racha debería subir a 4 (TC-35)"

        # Assert 2: racha 1 con el hueco del día 18 (TC-36)
        hueco = repo_habits.create({"name": "Correr", "habit_type": "ejercicio"}, user_id=1)
        repo_habits.upsert_log(hueco, "2026-08-17", 1, True)
        repo_habits.upsert_log(hueco, "2026-08-19", 1, True)
        assert habit_streak(hueco, "2026-08-19") == 1, \
            "Assert 2 Falló: con el 18 sin cumplir la racha del 19 es 1, no 2 (TC-36)"

        # Assert 3: sin registros, racha 0 y sin excepción
        vacio = repo_habits.create({"name": "Meditar", "habit_type": "relajacion"}, user_id=1)
        assert habit_streak(vacio, "2026-08-20") == 0, \
            "Assert 3 Falló: un hábito sin registros debe dar racha 0"

        # Assert 4: cuenta recién creada, 0.0 y sin reventar (TC-38)
        resumen_vacio = daily_summary(2, "2026-08-20")
        assert resumen_vacio["tareas"]["porcentaje"] == 0.0, \
            "Assert 4 Falló: una cuenta vacía debe dar 0.0, no lanzar (TC-38)"
        assert resumen_vacio["habitos"] == {"marcados": 0, "total": 0}, \
            "Assert 4 Falló: una cuenta vacía no tiene hábitos"
        assert "porcentaje" not in resumen_vacio["habitos"], \
            "Assert 4 Falló: 'habitos' no debe llevar porcentaje (TC-39)"

        # Assert 5: 6 de 8 tareas -> 75.0 y las secciones suman el total (TC-37)
        if "user_id" in _columnas(TABLA_TAREAS):
            db = database.get_db()
            reparto = [("Trabajo", 4, 3), ("Personal", 2, 1), ("Actividades", 2, 2)]
            for categoria, total, hechas in reparto:
                for indice in range(total):
                    estado = "completed" if indice < hechas else "pending"
                    db.execute(
                        """INSERT INTO tasks (user_id, title, category, due_date,
                                              estimated_minutes, status)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (1, "T%d" % indice, categoria, "2026-08-20", 30, estado),
                    )
            db.commit()
            resumen = daily_summary(1, "2026-08-20")
            assert resumen["tareas"]["porcentaje"] == 75.0, \
                "Assert 5 Falló: 6 de 8 tareas deben dar 75.0 (TC-37)"
            assert sum(s["total"] for s in resumen["secciones"].values()) == 8, \
                "Assert 5 Falló: las secciones no suman el total de tareas (TC-37)"
            assert list(resumen["secciones"].keys())[:3] == ["Trabajo", "Personal", "Actividades"], \
                "Assert 5 Falló: las secciones no salen en el orden preferente"
            tc37_corrido = True
        else:
            tc37_corrido = False
            print("  Assert 5 OMITIDO: el Modulo B aun no ha anadido user_id a `tasks` (TC-37)")

        # Assert 6: system_metrics() devuelve SOLO números (TC-41)
        agregados = system_metrics()
        for clave, valor in agregados.items():
            assert isinstance(valor, (int, float)) and not isinstance(valor, bool), \
                "Assert 6 Falló: system_metrics()['%s'] no es un número (TC-41)" % clave
        assert agregados["usuarios_total"] == 2, \
            "Assert 6 Falló: usuarios_total no coincide con COUNT(*) FROM users"

        database.close_db()

    for sufijo in ("", "-wal", "-shm"):
        try:
            os.unlink(ruta_temporal + sufijo)
        except OSError:
            pass

    if tc37_corrido:
        print("SUCCESS: Todas las 6 pruebas de assert para metrics.py pasaron exitosamente!")
    else:
        print("SUCCESS: 5 de 6 pruebas de assert para metrics.py pasaron "
              "(1 omitida: TC-37 espera a que el Modulo B migre `tasks`).")
