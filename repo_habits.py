"""
VibePlanner v2 - Repositorio de Hábitos y Registro Diario (repo_habits.py)
------------------------------------------------------------------------
DUEÑA DE ESTE ARCHIVO: Ana Cusi (Módulo D - Hábitos, Métricas y Design System)

CONTRATO CONGELADO - MÓDULO D:
    list_by_user(user_id)                       -> list[dict]
    get_owned(habit_id, user_id)                -> dict | None
    create(data, user_id)                       -> int
    upsert_log(habit_id, date_iso, value, done) -> bool
    logs_range(habit_id, from_iso, to_iso)      -> list[dict]

Auxiliares de lectura que consume la pantalla (mismo módulo porque también
tocan `habit_logs`):
    log_of_day(habit_id, date_iso)              -> dict | None
    logs_of_day_by_user(user_id, date_iso)      -> dict   # {habit_id: fila}
    logs_range_by_user(user_id, from_iso, to_iso) -> dict # {habit_id: [filas]}

Cambiar cualquiera de estas firmas obliga a AVISAR AL GRUPO antes de hacerlo:
`metrics.py` y el blueprint `habitos` dependen de ellas.

Este archivo es el ÚNICO sitio del proyecto donde `habits` y `habit_logs`
aparecen en un SQL de escritura. La racha NO se calcula aquí: es lógica de
negocio y vive en `metrics.py`.
"""

import math

import database

TIPOS_VALIDOS = ("dieta", "ejercicio", "relajacion", "sueno", "general")
UNIDADES_VALIDAS = ("horas", "minutos", "vasos", "veces", "vez")

LARGO_MAXIMO_NOMBRE = 80
META_MAXIMA = 1000


def _dict_from_row(row):
    return dict(row) if row else None


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------

def list_by_user(user_id):
    """
    Los hábitos activos del usuario.

    Ordenados por tipo y luego por nombre para que la pantalla salga siempre en
    el mismo orden: una lista que se reordena sola entre recargas hace dudar al
    usuario de si marcó el hábito correcto.
    """
    db = database.get_db()
    rows = db.execute(
        """SELECT id, user_id, name, habit_type, target_value, unit,
                  is_active, created_at
           FROM   habits
           WHERE  user_id = ? AND is_active = 1
           ORDER  BY habit_type, name""",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_owned(habit_id, user_id):
    """
    El hábito, sólo si es de este usuario. `None` en cualquier otro caso.

    El `user_id` va DENTRO del WHERE a propósito: traer la fila y comparar
    después en Python deja la puerta abierta a que un cambio futuro se salte la
    comparación y devuelva el hábito de otra persona.
    """
    db = database.get_db()
    row = db.execute(
        """SELECT id, user_id, name, habit_type, target_value, unit,
                  is_active, created_at
           FROM   habits
           WHERE  id = ? AND user_id = ?""",
        (habit_id, user_id),
    ).fetchone()
    return _dict_from_row(row)


def logs_range(habit_id, from_iso, to_iso):
    """
    Los registros del hábito entre dos fechas ISO, ambas incluidas.

    `log_date` se guarda como TEXT en ISO YYYY-MM-DD, así que el BETWEEN de
    texto ordena y compara igual que una fecha, y además usa el índice
    ix_habit_logs_date.
    """
    db = database.get_db()
    rows = db.execute(
        """SELECT id, habit_id, log_date, value, done
           FROM   habit_logs
           WHERE  habit_id = ? AND log_date BETWEEN ? AND ?
           ORDER  BY log_date""",
        (habit_id, from_iso, to_iso),
    ).fetchall()
    return [dict(r) for r in rows]


def log_of_day(habit_id, date_iso):
    """El registro de un día concreto, o None si ese día no se marcó nada."""
    db = database.get_db()
    row = db.execute(
        """SELECT id, habit_id, log_date, value, done
           FROM   habit_logs
           WHERE  habit_id = ? AND log_date = ?""",
        (habit_id, date_iso),
    ).fetchone()
    return _dict_from_row(row)


def logs_of_day_by_user(user_id, date_iso):
    """
    Los registros de ESE día de todos los hábitos del usuario, indexados por
    `habit_id`.

    Existe para evitar el N+1: la pantalla necesita saber si cada hábito está
    marcado hoy, y preguntarlo hábito por hábito dentro del bucle son N
    consultas donde basta una. El JOIN con `habits` es también lo que garantiza
    que sólo salgan registros de hábitos suyos.
    """
    db = database.get_db()
    rows = db.execute(
        """SELECT l.id, l.habit_id, l.log_date, l.value, l.done
           FROM   habit_logs l
           JOIN   habits h ON h.id = l.habit_id
           WHERE  h.user_id = ? AND l.log_date = ?""",
        (user_id, date_iso),
    ).fetchall()
    return {fila["habit_id"]: dict(fila) for fila in rows}


def logs_range_by_user(user_id, from_iso, to_iso):
    """
    Los registros de TODOS los hábitos del usuario en una ventana de fechas,
    agrupados por `habit_id`.

    Es la versión sin N+1 de `logs_range`: la pantalla de hábitos necesita la
    racha y los últimos siete días de cada hábito, y llamar a `logs_range` por
    hábito son N consultas donde basta una.
    """
    db = database.get_db()
    rows = db.execute(
        """SELECT l.id, l.habit_id, l.log_date, l.value, l.done
           FROM   habit_logs l
           JOIN   habits h ON h.id = l.habit_id
           WHERE  h.user_id = ? AND l.log_date BETWEEN ? AND ?
           ORDER  BY l.log_date""",
        (user_id, from_iso, to_iso),
    ).fetchall()

    agrupados = {}
    for fila in rows:
        agrupados.setdefault(fila["habit_id"], []).append(dict(fila))
    return agrupados


# --------------------------------------------------------------------------
# Escritura
# --------------------------------------------------------------------------

def _validar(data):
    """
    Valida los datos de un hábito nuevo.

    Los mensajes van en español y dicen qué pasó Y cómo arreglarlo, porque se
    muestran tal cual al usuario en un flash: "Valor inválido" no le dice a
    nadie qué corregir.
    """
    nombre = (data.get("name") or "").strip()
    if not nombre:
        raise ValueError("El hábito necesita un nombre. Por ejemplo: Dormir 8 horas.")
    if len(nombre) > LARGO_MAXIMO_NOMBRE:
        raise ValueError(
            "El nombre es demasiado largo (máximo %d caracteres). "
            "Prueba con algo más corto." % LARGO_MAXIMO_NOMBRE
        )

    tipo = data.get("habit_type") or "general"
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(
            "El tipo de hábito no es válido. Elige uno de: "
            "dieta, ejercicio, relajacion, sueno o general."
        )

    try:
        meta = float(data.get("target_value", 1))
    except (TypeError, ValueError):
        raise ValueError("La meta debe ser un número. Por ejemplo: 8 horas.")
    # float() acepta 'nan' e 'inf', y NaN atraviesa las comparaciones de rango:
    # `nan <= 0` y `nan > META_MAXIMA` son las dos False, así que pasaba los dos
    # filtros y acababa guardado como NULL. En pantalla se leía "Meta: 0".
    if not math.isfinite(meta):
        raise ValueError("La meta debe ser un número. Por ejemplo: 8 horas.")
    if meta <= 0:
        raise ValueError("La meta debe ser mayor que 0. Por ejemplo: 8 horas.")
    if meta > META_MAXIMA:
        raise ValueError(
            "La meta es demasiado alta (máximo %d). "
            "Revisa la unidad: quizá querías minutos y no horas." % META_MAXIMA
        )

    unidad = data.get("unit") or "vez"
    if unidad not in UNIDADES_VALIDAS:
        raise ValueError(
            "La unidad no es válida. Elige una de: horas, minutos, vasos, veces o vez."
        )

    return nombre, tipo, meta, unidad


def create(data, user_id):
    """
    Crea un hábito y devuelve su id nuevo.

    `user_id` es un argumento aparte y NUNCA se lee de `data`: si saliera del
    diccionario del formulario, alguien acabaría creando hábitos a nombre de
    otra persona.
    """
    nombre, tipo, meta, unidad = _validar(data)

    db = database.get_db()
    cursor = db.execute(
        """INSERT INTO habits (user_id, name, habit_type, target_value, unit)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, nombre, tipo, meta, unidad),
    )
    db.commit()
    return cursor.lastrowid


def upsert_log(habit_id, date_iso, value, done):
    """
    Registra (o corrige) el cumplimiento de un día. Devuelve True.

    Es un UPSERT y no un SELECT seguido de INSERT/UPDATE por dos razones:
    la versión con SELECT tiene una condición de carrera entre la lectura y la
    escritura, y sobre todo DUPLICA la fila si el SELECT mira la fecha
    equivocada. Aquí la garantía la da el UNIQUE (habit_id, log_date) de la
    base, que no se olvida nunca (TC-34).
    """
    db = database.get_db()
    db.execute(
        """INSERT INTO habit_logs (habit_id, log_date, value, done)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(habit_id, log_date)
           DO UPDATE SET value = excluded.value, done = excluded.done""",
        (habit_id, date_iso, value, 1 if done else 0),
    )
    db.commit()
    return True


# --------------------------------------------------------------------------
# PRUEBAS DE ASSERT DEL REPOSITORIO (EVIDENCIA DE TESTING DE ANA)
#   python repo_habits.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import tempfile

    from flask import Flask

    # Base temporal: estas pruebas NUNCA deben tocar vibe_planner.db.
    descriptor, ruta_temporal = tempfile.mkstemp(suffix=".db")
    os.close(descriptor)
    database.DB_PATH = ruta_temporal
    database.init_db()

    # Dos usuarios: hacen falta dos para poder probar que un hábito ajeno no se
    # ve (assert 2).
    conexion = database.raw_connection()
    conexion.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (1, 'ana', 'ana@test.local', 'x')"
    )
    conexion.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (2, 'jose', 'jose@test.local', 'x')"
    )
    conexion.commit()
    conexion.close()

    # get_db() vive en flask.g, así que las pruebas necesitan un contexto de
    # aplicación aunque no haya ninguna petición de por medio.
    aplicacion = Flask(__name__)

    with aplicacion.app_context():
        # Assert 1: create() devuelve un id y el hábito aparece en list_by_user()
        habito_id = create(
            {"name": "Dormir 8 horas", "habit_type": "sueno",
             "target_value": 8, "unit": "horas"},
            user_id=1,
        )
        assert isinstance(habito_id, int) and habito_id > 0, \
            "Assert 1 Falló: create() no devolvió un id"
        mios = list_by_user(1)
        assert len(mios) == 1 and mios[0]["name"] == "Dormir 8 horas", \
            "Assert 1 Falló: el hábito creado no aparece en list_by_user()"

        # Assert 2: el hábito de otro usuario no se ve
        assert get_owned(habito_id, 2) is None, \
            "Assert 2 Falló: get_owned devolvió el hábito de otro usuario"
        assert get_owned(habito_id, 1) is not None, \
            "Assert 2 Falló: get_owned no devolvió el hábito propio"

        # Assert 3: corregir el registro de hoy NO duplica la fila (TC-34)
        upsert_log(habito_id, "2026-08-13", 7, True)
        upsert_log(habito_id, "2026-08-13", 8, True)
        registros = logs_range(habito_id, "2026-08-13", "2026-08-13")
        assert len(registros) == 1, \
            "Assert 3 Falló: corregir el registro duplicó la fila (TC-34)"
        assert registros[0]["value"] == 8, \
            "Assert 3 Falló: el registro no guardó el último valor"

        # Assert 4: 'sueño' con tilde es rechazado antes de llegar a la base
        try:
            create({"name": "Siesta", "habit_type": "sueño"}, user_id=1)
            raise AssertionError("Assert 4 Falló: se aceptó habit_type='sueño' con tilde")
        except ValueError:
            pass

        # Assert 5: logs_range acotado a tres días devuelve exactamente tres
        for dia in ("2026-08-14", "2026-08-15", "2026-08-16", "2026-08-17"):
            upsert_log(habito_id, dia, 8, True)
        ventana = logs_range(habito_id, "2026-08-14", "2026-08-16")
        assert len(ventana) == 3, \
            "Assert 5 Falló: logs_range devolvió %d filas en una ventana de 3 días" % len(ventana)
        assert [f["log_date"] for f in ventana] == ["2026-08-14", "2026-08-15", "2026-08-16"], \
            "Assert 5 Falló: logs_range no devolvió las fechas ordenadas"

        # Windows no borra un archivo con la conexión abierta, y el modo WAL
        # deja además dos ficheros satélite.
        database.close_db()

    for sufijo in ("", "-wal", "-shm"):
        try:
            os.unlink(ruta_temporal + sufijo)
        except OSError:
            pass

    print("SUCCESS: Todas las 5 pruebas de assert para repo_habits.py pasaron exitosamente!")
