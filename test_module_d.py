"""
VibePlanner v2 - Pruebas del Modulo D (test_module_d.py)
------------------------------------------------------------------------
DUENA DE ESTE ARCHIVO: Ana Cusi (Modulo D)

Cubre TC-33 .. TC-42, los casos automatizables del plan de pruebas.
TC-43, TC-44 y TC-45 son visuales y van en docs/VUP_V2/evidencia_modulo_d.md.

    python test_module_d.py

Sin pytest y sin dependencias nuevas, igual que test_v2.py y test_module_c.py.
Corre SIEMPRE sobre una base temporal: nunca toca vibe_planner.db.
"""

import os
import sys
import tempfile

CSRF_PRUEBA = "token-de-prueba"
ADMIN_PASS = "CambiarEsto2026!"

# Marcadores que se siembran como contenido de usuario. TC-41 comprueba que
# NINGUNO aparece en el panel de metricas del sistema.
MARCADOR_TAREA = "MARCADOR_SECRETO_TAREA"
MARCADOR_EVENTO = "MARCADOR_SECRETO_EVENTO"
MARCADOR_CORREO = "marcador_secreto@test.local"


def _reiniciar_base():
    """Base temporal recien sembrada, con database.DB_PATH ya redirigido."""
    fd, ruta = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    import database
    database.DB_PATH = ruta
    database.init_db()

    import seed
    db = database.raw_connection()
    seed.sembrar_permisos(db)
    seed.sembrar_roles(db)
    db.commit()
    admin_id, _ = seed.sembrar_admin(db)
    db.close()

    return ruta, admin_id


def _cliente(app):
    app.config["TESTING"] = True
    return app.test_client()


def _post(cliente, url, **datos):
    """
    POST con token CSRF valido.

    El token se replanta ANTES de cada peticion, y no una sola vez al crear el
    cliente, porque al iniciar sesion auth.py hace session.clear() y el token
    cambia. Sin esto, TODOS los POST de este archivo devolverian 400.
    """
    with cliente.session_transaction() as sesion:
        sesion["_csrf"] = CSRF_PRUEBA
    datos.setdefault("_csrf", CSRF_PRUEBA)
    return cliente.post(url, data=datos)


def _entrar(cliente, username, password):
    return _post(cliente, "/login", username=username, password=password)


def main():
    ruta, admin_id = _reiniciar_base()

    import app as app_modulo
    import database
    import metrics
    import repo_habits
    import repo_users

    app = app_modulo.app
    cliente = _cliente(app)

    resultados = []      # (codigo, "OK" | "FALLA" | "OMITIDO")
    fallos = []

    def comprobar(codigo, nombre, condicion, detalle=""):
        if condicion:
            print("  OK       %s  %s" % (codigo, nombre))
            resultados.append((codigo, "OK"))
        else:
            print("  FALLA    %s  %s  %s" % (codigo, nombre, detalle))
            resultados.append((codigo, "FALLA"))
            fallos.append(codigo)

    def omitir(codigo, motivo):
        print("  OMITIDO  %s  %s" % (codigo, motivo))
        resultados.append((codigo, "OMITIDO"))

    # ---------------------------------------------------------------- setup
    _entrar(cliente, "admin", ADMIN_PASS)

    # Un segundo usuario SIN el permiso metrica.sistema.ver, para TC-42, y con
    # un correo marcador para TC-41.
    with app.app_context():
        repo_users.create_user(
            {"username": "lucero", "email": MARCADOR_CORREO,
             "password": "Vibe2026Segura!", "full_name": "Lucero"},
            ["usuario"], granted_by=admin_id,
        )

    print("\n--- Habitos (US13) ---")

    # ---------------------------------------------------------------- TC-33
    tipos = [
        ("Dormir 8 horas", "sueno", "8", "horas"),
        ("Correr 30 minutos", "ejercicio", "30", "minutos"),
        ("Tomar 8 vasos de agua", "dieta", "8", "vasos"),
        ("Meditar 10 minutos", "relajacion", "10", "minutos"),
    ]
    for nombre, tipo, meta, unidad in tipos:
        _post(cliente, "/habitos", name=nombre, habit_type=tipo,
              target_value=meta, unit=unidad)

    pagina = cliente.get("/habitos")
    creados_ok = pagina.status_code == 200 and all(
        nombre.encode() in pagina.data for nombre, _, _, _ in tipos
    )
    metas_ok = ("8 horas".encode() in pagina.data
                and "30 minutos".encode() in pagina.data
                and "8 vasos".encode() in pagina.data)
    comprobar("TC-33", "los cuatro tipos de habito se crean con meta y unidad",
              creados_ok and metas_ok,
              "status=%s" % pagina.status_code)

    # ---------------------------------------------------------------- TC-34
    conexion = database.raw_connection()
    habito_id = conexion.execute(
        "SELECT id FROM habits WHERE name = ?", ("Dormir 8 horas",)
    ).fetchone()["id"]
    conexion.close()

    with app.app_context():
        hoy = metrics.hoy_iso()

    _post(cliente, "/habitos/%d/registro" % habito_id, value="7", done="1")
    _post(cliente, "/habitos/%d/registro" % habito_id, value="8", done="1")

    conexion = database.raw_connection()
    filas, valor = conexion.execute(
        "SELECT COUNT(*), MAX(value) FROM habit_logs WHERE habit_id = ? AND log_date = ?",
        (habito_id, hoy),
    ).fetchone()
    conexion.close()
    comprobar("TC-34", "corregir el registro de hoy NO duplica la fila",
              filas == 1 and valor == 8.0,
              "filas=%s valor=%s" % (filas, valor))

    # ------------------------------------------------------------ TC-35/36
    # Fechas FIJAS, nunca date.today(): una prueba de rachas que depende del
    # dia en que se ejecuta falla sola en la madrugada del cambio de mes.
    with app.app_context():
        racha_id = repo_habits.create(
            {"name": "Racha 3-4", "habit_type": "general"}, user_id=admin_id)
        for dia in ("2026-08-17", "2026-08-18", "2026-08-19"):
            repo_habits.upsert_log(racha_id, dia, 1, True)

        antes = metrics.habit_streak(racha_id, "2026-08-20")
        repo_habits.upsert_log(racha_id, "2026-08-20", 1, True)
        despues = metrics.habit_streak(racha_id, "2026-08-20")

        hueco_id = repo_habits.create(
            {"name": "Racha con hueco", "habit_type": "general"}, user_id=admin_id)
        repo_habits.upsert_log(hueco_id, "2026-08-17", 1, True)
        repo_habits.upsert_log(hueco_id, "2026-08-19", 1, True)
        con_hueco = metrics.habit_streak(hueco_id, "2026-08-19")

    comprobar("TC-35", "la racha da 3 con hoy sin marcar y 4 al marcarlo",
              antes == 3 and despues == 4,
              "antes=%s despues=%s" % (antes, despues))
    comprobar("TC-36", "un dia sin cumplir rompe la racha (17 y 19, sin el 18)",
              con_hueco == 1, "racha=%s" % con_hueco)

    print("\n--- Metricas propias (US14) ---")

    # ---------------------------------------------------------------- TC-37
    with app.app_context():
        columnas = metrics._columnas(metrics.TABLA_TAREAS)
        tiene_user_id = "user_id" in columnas

    if tiene_user_id:
        with app.app_context():
            db = database.get_db()
            reparto = [("Trabajo", 4, 3), ("Personal", 2, 1), ("Actividades", 2, 2)]
            for categoria, total, hechas in reparto:
                for indice in range(total):
                    db.execute(
                        """INSERT INTO tasks (user_id, title, category, due_date,
                                              estimated_minutes, status)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (admin_id, MARCADOR_TAREA, categoria, hoy, 30,
                         "completed" if indice < hechas else "pending"),
                    )
            db.commit()
            resumen = metrics.daily_summary(admin_id, hoy)

        comprobar("TC-37", "6 de 8 actividades dan 75 % agrupadas en tres secciones",
                  resumen["tareas"]["porcentaje"] == 75.0
                  and sum(s["total"] for s in resumen["secciones"].values()) == 8
                  and list(resumen["secciones"].keys())[:3] == ["Trabajo", "Personal", "Actividades"],
                  "porcentaje=%s" % resumen["tareas"]["porcentaje"])
    else:
        omitir("TC-37", "el Modulo B aun no ha anadido user_id a `tasks`")
        with app.app_context():
            resumen = metrics.daily_summary(admin_id, hoy)

    # ---------------------------------------------------------------- TC-38
    # Cuenta recien creada: cero de todo. Es lo primero que ve un usuario nuevo.
    cliente_nuevo = _cliente(app)
    _entrar(cliente_nuevo, "lucero", "Vibe2026Segura!")
    vacia = cliente_nuevo.get("/metricas")
    comprobar("TC-38", "una cuenta vacia abre /metricas sin error 500",
              vacia.status_code == 200 and b"0" in vacia.data,
              "status=%s" % vacia.status_code)

    # ---------------------------------------------------------------- TC-39
    # Los habitos se reportan APARTE: ni suman ni restan al % de actividades.
    sin_clave = "porcentaje" not in resumen["habitos"]
    claves_ok = set(resumen["habitos"].keys()) == {"marcados", "total"}
    if tiene_user_id:
        no_contamina = resumen["tareas"]["porcentaje"] == 75.0
    else:
        # Sin tareas conectadas, el % debe seguir en 0 pese a haber habitos
        # marcados: si los habitos se colaran, aqui saldria distinto de 0.
        no_contamina = resumen["tareas"]["porcentaje"] == 0.0
    comprobar("TC-39", "los habitos van aparte del porcentaje de actividades",
              sin_clave and claves_ok and no_contamina,
              "habitos=%s tareas=%s" % (resumen["habitos"], resumen["tareas"]))

    print("\n--- Metricas del sistema (US15) ---")

    # ---------------------------------------------------------------- TC-40
    with app.app_context():
        db = database.get_db()
        db.execute(
            """INSERT INTO events (owner_id, title, start_at, end_at)
               VALUES (?, ?, ?, ?)""",
            (admin_id, MARCADOR_EVENTO, "2026-08-20 09:00", "2026-08-20 10:00"),
        )
        db.commit()

        agregados = metrics.system_metrics()
        reales = {
            "usuarios_total": db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"],
            "usuarios_activos": db.execute(
                "SELECT COUNT(*) AS n FROM users WHERE is_active = 1").fetchone()["n"],
            "eventos_total": db.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"],
        }

    coinciden = all(agregados[clave] == valor for clave, valor in reales.items())
    solo_numeros = all(
        isinstance(v, (int, float)) and not isinstance(v, bool)
        for v in agregados.values()
    )
    comprobar("TC-40", "las cifras del panel coinciden con SELECT COUNT(*)",
              coinciden and solo_numeros,
              "panel=%s reales=%s" % (agregados, reales))

    # ---------------------------------------------------------------- TC-41
    panel = cliente.get("/admin/metricas")
    filtrado = (
        panel.status_code == 200
        and MARCADOR_TAREA.encode() not in panel.data
        and MARCADOR_EVENTO.encode() not in panel.data
        and MARCADOR_CORREO.encode() not in panel.data
        and b"lucero" not in panel.data
    )
    comprobar("TC-41", "el panel no expone contenido de nadie, ni en el HTML",
              filtrado, "status=%s" % panel.status_code)

    # ---------------------------------------------------------------- TC-42
    sin_permiso = cliente_nuevo.get("/admin/metricas")
    comprobar("TC-42", "sin el permiso metrica.sistema.ver responde 403",
              sin_permiso.status_code == 403,
              "status=%s" % sin_permiso.status_code)

    # ------------------------------------------------------------- limpieza
    for sufijo in ("", "-wal", "-shm"):
        try:
            os.unlink(ruta + sufijo)
        except OSError:
            pass

    # -------------------------------------------------------------- resumen
    print("\n" + " · ".join(
        "%s %s" % (codigo, estado if estado != "OMITIDO" else "OMITIDO (Modulo B)")
        for codigo, estado in resultados
    ))

    pasados = sum(1 for _, e in resultados if e == "OK")
    omitidos = sum(1 for _, e in resultados if e == "OMITIDO")
    total = len(resultados)

    if fallos:
        print("\nFALLARON %d de %d casos del Modulo D: %s"
              % (len(fallos), total, ", ".join(fallos)))
        return 1

    if omitidos:
        print("\nSUCCESS: %d de %d casos automatizados del Modulo D pasaron (%d omitido%s)."
              % (pasados, total, omitidos, "s" if omitidos != 1 else ""))
    else:
        print("\nSUCCESS: los %d casos automatizados del Modulo D pasaron." % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
