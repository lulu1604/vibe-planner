"""
VibePlanner v2 - Pruebas del nucleo (test_v2.py)
-------------------------------------------------
    python test_v2.py

Cubre las tres historias del Modulo A (US5, US6, US7) y, en particular, los
casos que BLOQUEAN el release. Corre sobre una base temporal: nunca toca
vibe_planner.db.

Las pruebas de la v1 siguen en su sitio y hay que ejecutarlas tambien:
    python app.py test      (11 asserts, Ana)
    python database.py      (4 asserts, Jose)
    python validators.py    (26 comprobaciones)
"""

import os
import re
import sys
import tempfile

CSRF_PRUEBA = "token-de-prueba"


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
    cambia. Eso es deliberado -- endurece contra la fijacion de sesion -- y un
    navegador real ni se entera, porque cada pagina que carga trae ya el token
    nuevo en su <input type="hidden">. Aqui hay que imitarlo a mano.
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
    import repo_users
    import security
    from repo_users import SinAdministradores

    app = app_modulo.app
    cliente = _cliente(app)
    fallos = []

    def comprobar(nombre, condicion, detalle=""):
        if condicion:
            print(f"  OK   {nombre}")
        else:
            print(f"  FALLA {nombre}  {detalle}")
            fallos.append(nombre)

    print("\n--- US5: registro, login y logout ---")

    r = _post(cliente, "/register", username="piero", email="piero@esan.pe",
              password="Vibe2026!", full_name="Piero Calderon")
    comprobar("TC 5.1  registro valido redirige (302)", r.status_code == 302, r.status_code)

    with app.app_context():
        db = database.raw_connection()
        piero = repo_users.get_by_username("piero", conn=db)
        comprobar("TC-01   la contrasena se guarda cifrada",
                  piero and "Vibe2026!" not in piero["password_hash"]
                  and piero["password_hash"].startswith("pbkdf2:"))
        db.close()

    cliente.get("/logout")   # por GET no deberia hacer nada
    r = cliente.get("/logout")
    comprobar("        /logout por GET responde 405", r.status_code == 405, r.status_code)

    r = _post(cliente, "/logout")
    comprobar("        /logout por POST cierra sesion (302)", r.status_code == 302, r.status_code)

    # --- Validacion de servidor, saltandose el HTML -----------------------
    cliente2 = _cliente(app)
    r = _post(cliente2, "/register", username="a", email="x", password="1")
    comprobar("TC 5.3  datos invalidos -> 400 (no 500)", r.status_code == 400, r.status_code)

    r = _post(cliente2, "/register", username="piero", email="otro@esan.pe",
              password="Vibe2026!")
    comprobar("TC 5.2  usuario duplicado -> 409", r.status_code == 409, r.status_code)

    # --- Mensaje de login identico en ambos casos (enumeracion) ----------
    r_inexistente = _entrar(cliente2, "no.existe", "loquesea123")
    r_mala_clave = _entrar(cliente2, "piero", "clave-incorrecta")
    comprobar("TC 5.4  credenciales malas -> 401",
              r_inexistente.status_code == 401 and r_mala_clave.status_code == 401)

    def _mensaje(respuesta):
        html = respuesta.get_data(as_text=True)
        encontrado = re.search(r"Usuario o contrasena incorrectos\.", html)
        return encontrado.group(0) if encontrado else None

    comprobar("TC-04   el mensaje es IDENTICO exista o no la cuenta",
              _mensaje(r_inexistente) is not None
              and _mensaje(r_inexistente) == _mensaje(r_mala_clave))

    print("\n--- US6: permisos agregativos ---")

    with app.app_context():
        db = database.raw_connection()
        p_admin = repo_users.get_permissions(admin_id, conn=db)
        p_piero = repo_users.get_permissions(piero["id"], conn=db)
        db.close()

    # 17 y 24: el Modulo B anadio `tarea.asignar` (US10), acotada al rol admin
    # porque US10 sigue diferida al backlog v3. El usuario normal no la tiene.
    comprobar("TC 6.1  un rol -> 17 permisos", len(p_piero) == 17, len(p_piero))
    comprobar("TC 6.2  dos roles -> 24 permisos (la union)", len(p_admin) == 24, len(p_admin))
    comprobar("        un usuario normal NO puede asignar tareas a otros (US10 diferida)",
              "tarea.asignar" not in p_piero and "tarea.asignar" in p_admin)
    comprobar("        el admin conserva los permisos de usuario",
              p_piero.issubset(p_admin))

    # --- TC-03: EL CASO QUE BLOQUEA EL RELEASE ---------------------------
    cliente3 = _cliente(app)
    _post(cliente3, "/register", username="atacante", email="mal@esan.pe",
          password="Hack2026!", role="admin", roles="admin")

    with app.app_context():
        db = database.raw_connection()
        atacante = repo_users.get_by_username("atacante", conn=db)
        roles_atacante = [r["code"] for r in repo_users.get_roles(atacante["id"], conn=db)]
        db.close()

    comprobar("TC-03   role=admin en el registro NO otorga nada  <-- BLOQUEANTE",
              roles_atacante == ["usuario"], roles_atacante)

    print("\n--- US7: gestion de usuarios ---")

    admin_cli = _cliente(app)
    _entrar(admin_cli, "admin", "CambiarEsto2026!")

    r = admin_cli.get("/admin/usuarios")
    comprobar("TC 7.1  el admin abre /admin/usuarios (200)", r.status_code == 200, r.status_code)

    r = admin_cli.get("/inicio")
    comprobar("TC-06   ...y /inicio en la MISMA sesion (es usuario y admin)",
              r.status_code == 200, r.status_code)

    piero_cli = _cliente(app)
    _entrar(piero_cli, "piero", "Vibe2026!")
    r = piero_cli.get("/admin/usuarios")
    comprobar("TC-07   una cuenta sin permiso recibe 403 REAL del servidor",
              r.status_code == 403, r.status_code)

    # --- TC-09: quitar un rol surte efecto sin cerrar sesion -------------
    r = _post(admin_cli, "/admin/usuarios", username="lucero", email="lucero@esan.pe",
              password="Vibe2026!", roles=["usuario", "admin"])
    comprobar("        alta administrativa con dos roles (302)", r.status_code == 302, r.status_code)

    with app.app_context():
        db = database.raw_connection()
        lucero = repo_users.get_by_username("lucero", conn=db)
        db.close()

    lucero_cli = _cliente(app)
    _entrar(lucero_cli, "lucero", "Vibe2026!")
    comprobar("        lucero entra y ve la administracion",
              lucero_cli.get("/admin/usuarios").status_code == 200)

    _post(admin_cli, f"/admin/usuarios/{lucero['id']}/roles", roles="usuario")

    comprobar("TC-09   quitarle el rol surte efecto SIN cerrar sesion",
              lucero_cli.get("/admin/usuarios").status_code == 403)

    # --- TC-10: nunca sin administradores --------------------------------
    with app.app_context():
        db = database.raw_connection()
        try:
            repo_users.assign_roles(admin_id, ["usuario"], conn=db)
            sin_admins = False
        except SinAdministradores:
            sin_admins = True
        roles_admin = [r["code"] for r in repo_users.get_roles(admin_id, conn=db)]
        db.close()

    comprobar("TC-10   quitarse admin siendo el ultimo se rechaza  <-- BLOQUEANTE",
              sin_admins and "admin" in roles_admin, roles_admin)

    with app.app_context():
        db = database.raw_connection()
        try:
            repo_users.set_active(admin_id, 0, conn=db)
            desactivo = True
        except SinAdministradores:
            desactivo = False
        sigue_activo = repo_users.get_by_id(admin_id, conn=db)["is_active"]
        db.close()

    comprobar("TC-10   desactivar al ultimo admin se rechaza",
              not desactivo and sigue_activo == 1)

    # --- TC-05: desactivar no borra --------------------------------------
    with app.app_context():
        db = database.raw_connection()
        db.execute(
            "INSERT INTO tasks (title, due_date, estimated_minutes) VALUES (?, ?, ?)",
            ("Tarea de lucero", "2026-08-20", 30),
        )
        db.commit()
        antes = db.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
        db.close()

    _post(admin_cli, f"/admin/usuarios/{lucero['id']}/estado", is_active="0")
    r = _entrar(_cliente(app), "lucero", "Vibe2026!")
    comprobar("TC-05   una cuenta desactivada no puede entrar (403)",
              r.status_code == 403, r.status_code)

    with app.app_context():
        db = database.raw_connection()
        despues = db.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
        db.close()
    comprobar("TC-05   ...y sus datos NO se borran", antes == despues)

    # --- No existe ninguna ruta de borrado -------------------------------
    rutas = [str(regla) for regla in app.url_map.iter_rules()]
    comprobar("        no existe ninguna ruta de borrado de usuarios",
              not any("delete" in r or "borrar" in r for r in rutas if "usuario" in r))

    # --- 404, no 403, para un id inexistente -----------------------------
    r = _post(admin_cli, "/admin/usuarios/999999/estado", is_active="0")
    comprobar("        id de usuario inexistente -> 404", r.status_code == 404, r.status_code)

    r = admin_cli.get("/admin/usuarios/999999")
    comprobar("        detalle de un id inexistente -> 404", r.status_code == 404, r.status_code)

    # --- Pantalla de mantenimiento ---------------------------------------
    r = admin_cli.get(f"/admin/usuarios/{piero['id']}")
    comprobar("        el detalle de una cuenta abre (200)", r.status_code == 200, r.status_code)

    r = _post(admin_cli, f"/admin/usuarios/{piero['id']}/datos",
              full_name="Piero Calderon Ramos", email="piero.nuevo@esan.pe")
    with app.app_context():
        db = database.raw_connection()
        actualizado = repo_users.get_by_id(piero["id"], conn=db)
        db.close()
    comprobar("        editar nombre y correo de otra cuenta funciona",
              r.status_code == 302 and actualizado["email"] == "piero.nuevo@esan.pe"
              and actualizado["full_name"] == "Piero Calderon Ramos", r.status_code)

    # El correo de `admin` ya existe: debe rebotar con 400, NO con un 500 por
    # el UNIQUE de la base.
    r = _post(admin_cli, f"/admin/usuarios/{piero['id']}/datos",
              full_name="Piero", email="admin@vibeplanner.local")
    with app.app_context():
        db = database.raw_connection()
        sin_cambios = repo_users.get_by_id(piero["id"], conn=db)
        db.close()
    comprobar("        correo duplicado al editar -> 400 y no cambia nada",
              r.status_code == 400 and sin_cambios["email"] == "piero.nuevo@esan.pe",
              r.status_code)

    r = _post(admin_cli, f"/admin/usuarios/{piero['id']}/datos",
              full_name="Piero", email="esto-no-es-un-correo")
    comprobar("        correo invalido al editar -> 400", r.status_code == 400, r.status_code)

    # --- El menu de cuenta se filtra por permisos ------------------------
    html_admin = admin_cli.get("/inicio").get_data(as_text=True)
    html_piero = piero_cli.get("/inicio").get_data(as_text=True)
    comprobar("        el menu ofrece Gestion de usuarios solo a quien puede",
              "Gestion de usuarios" in html_admin
              and "Gestion de usuarios" not in html_piero)

    print("\n--- BLOQUE C: calendario e invitaciones (US11, US12) ---")

    # Dos cuentas limpias y activas para este bloque. `lucero` quedo
    # desactivada en TC-05 y `piero` con el correo ya cambiado, asi que se
    # crean aparte para que los asserts de aqui no dependan de los de arriba.
    with app.app_context():
        db = database.raw_connection()
        cal_jose = repo_users.create_user(
            {"username": "josec", "email": "josec@esan.pe", "password": "Vibe2026!",
             "full_name": "Jose Cabrera"}, ["usuario"], conn=db)
        cal_ana = repo_users.create_user(
            {"username": "anac", "email": "anac@esan.pe", "password": "Vibe2026!",
             "full_name": "Ana Cusi"}, ["usuario"], conn=db)
        db.close()

    jose_cli = _cliente(app); _entrar(jose_cli, "josec", "Vibe2026!")
    ana_cli = _cliente(app); _entrar(ana_cli, "anac", "Vibe2026!")

    # --- TC-25: el evento cae en su dia ----------------------------------
    r = _post(jose_cli, "/eventos/nuevo", title="Examen de IoT",
              description="Aula 302",
              start_date="2026-08-27", start_time="09:00",
              end_date="2026-08-27", end_time="11:00", color="#567C8D")
    comprobar("TC-25   crear un evento redirige (302)", r.status_code == 302, r.status_code)

    html = jose_cli.get("/calendario/2026/8").get_data(as_text=True)
    comprobar("TC-25   aparece en la cuadricula con su titulo", "Examen de IoT" in html)
    comprobar("TC-25   ...con su hora de inicio", "09:00" in html)
    comprobar("TC-25   ...y con su color", "#567C8D" in html)

    # --- TC-26: navegacion entre meses Y entre anos ----------------------
    html = jose_cli.get("/calendario/2026/12").get_data(as_text=True)
    comprobar("TC-26   diciembre enlaza a enero del ano siguiente",
              "/calendario/2027/1" in html)
    html = jose_cli.get("/calendario/2026/1").get_data(as_text=True)
    comprobar("TC-26   enero enlaza a diciembre del anterior",
              "/calendario/2025/12" in html)
    comprobar("TC-26   un mes de 28 dias renderiza",
              jose_cli.get("/calendario/2026/2").status_code == 200)
    html = jose_cli.get("/calendario/2026/9").get_data(as_text=True)
    comprobar("TC-26   el evento de agosto NO se cuela en septiembre",
              "Examen de IoT" not in html)

    # --- TC-27: horario incoherente --------------------------------------
    def _contar(titulo):
        with app.app_context():
            db = database.raw_connection()
            n = db.execute("SELECT COUNT(*) c FROM events WHERE title = ?",
                           (titulo,)).fetchone()["c"]
            db.close()
        return n

    r = _post(jose_cli, "/eventos/nuevo", title="Fin antes del inicio",
              start_date="2026-08-20", start_time="15:00",
              end_date="2026-08-20", end_time="14:00", color="#567C8D")
    cuerpo = r.get_data(as_text=True)
    comprobar("TC-27   fin < inicio no revienta con 500", r.status_code != 500, r.status_code)
    comprobar("TC-27   ...lo explica en pantalla", "posterior a la de inicio" in cuerpo)
    comprobar("TC-27   ...y no inserta nada", _contar("Fin antes del inicio") == 0)

    r = _post(jose_cli, "/eventos/nuevo", title="Fin igual al inicio",
              start_date="2026-08-20", start_time="15:00",
              end_date="2026-08-20", end_time="15:00", color="#567C8D")
    comprobar("TC-27   fin == inicio tambien se rechaza",
              r.status_code != 500 and _contar("Fin igual al inicio") == 0)

    # --- TC-28: el calendario de otro no se ve nunca ---------------------
    html = ana_cli.get("/calendario/2026/8").get_data(as_text=True)
    comprobar("TC-28   ana no ve ningun evento de jose", "Examen de IoT" not in html)

    # --- Propiedad != permiso: ana tiene evento.editar, pero no es suyo --
    with app.app_context():
        db = database.raw_connection()
        ev_id = db.execute("SELECT id FROM events WHERE title='Examen de IoT'").fetchone()["id"]
        db.close()

    comprobar("TC-08   editar un evento ajeno responde 404, no 403",
              ana_cli.get(f"/eventos/{ev_id}/editar").status_code == 404)
    _post(ana_cli, f"/eventos/{ev_id}/eliminar")
    comprobar("TC-08   ...y borrarlo no lo borra", _contar("Examen de IoT") == 1)
    r = _post(ana_cli, f"/eventos/{ev_id}/invitar")
    comprobar("TC-08   ...ni puede generar un link de invitacion (404)",
              r.status_code == 404, r.status_code)

    # --- TC-29: invitar y aceptar ----------------------------------------
    r = _post(jose_cli, f"/eventos/{ev_id}/invitar")
    token = r.get_json()["token"] if r.status_code == 200 else None
    comprobar("TC-29   el anfitrion genera un token", token is not None and len(token) > 20)
    comprobar("        el token no es un id incremental",
              token is not None and not token.isdigit())

    r = _post(ana_cli, f"/invitacion/{token}/aceptar")
    comprobar("TC-29   ana acepta (302)", r.status_code == 302, r.status_code)
    html = ana_cli.get("/calendario/2026/8").get_data(as_text=True)
    comprobar("TC-29   el evento aparece en el calendario de ana", "Examen de IoT" in html)
    comprobar("TC-29   ...marcado como invitada por el anfitrion", "josec" in html)

    html = ana_cli.get(f"/invitacion/{token}").get_data(as_text=True)
    comprobar("TC-29   el contador muestra 1 invitado, sin contar al anfitrion",
              "1 invitado" in html, "el anfitrion se estaba sumando a si mismo")

    # --- TC-30: token invalido no filtra nada ----------------------------
    html = ana_cli.get("/invitacion/token-inventado-123").get_data(as_text=True)
    comprobar("TC-30   token invalido no revela el titulo", "Examen de IoT" not in html)
    comprobar("TC-30   ...ni el anfitrion", "josec" not in html)
    comprobar("TC-30   ...ni la fecha", "2026-08-27" not in html)
    comprobar("TC-30   ...y lo dice con un mensaje util", "cancelada" in html)

    # --- TC-32: aceptar dos veces es idempotente -------------------------
    def _aceptadas():
        with app.app_context():
            db = database.raw_connection()
            n = db.execute(
                "SELECT COUNT(*) c FROM event_invitations "
                "WHERE event_id = ? AND status = 'accepted'", (ev_id,)).fetchone()["c"]
            db.close()
        return n

    antes = _aceptadas()
    _post(ana_cli, f"/invitacion/{token}/aceptar")
    comprobar("TC-32   aceptar dos veces no crea otra fila", _aceptadas() == antes,
              f"{antes} -> {_aceptadas()}")
    html = ana_cli.get(f"/invitacion/{token}").get_data(as_text=True)
    comprobar("TC-32   ...y el contador sigue en 1", "1 invitado" in html)

    # --- TC-31: la invitacion exige sesion y devuelve al destino ---------
    anon = _cliente(app)
    r = anon.get(f"/invitacion/{token}")
    comprobar("TC-31   sin sesion redirige al login (302)", r.status_code == 302, r.status_code)
    r = _post(anon, "/login", username="anac", password="Vibe2026!")
    destino = r.headers.get("Location") or ""
    comprobar("TC-31   ...y tras entrar VUELVE SOLO a la invitacion",
              token in destino, f"fue a {destino}")

    # --- TC-07 aplicado al calendario: el permiso manda ------------------
    #
    # ESTE ES EL ASSERT QUE FALTABA. El modulo se entrego con @login_required
    # en las 8 rutas, asi que los 5 permisos de calendario estaban sembrados y
    # no los comprobaba nadie: un administrador podia quitarlos y no pasaba
    # nada. Sin esta comprobacion, la regresion vuelve en silencio.
    def _permiso_del_rol(codigo, poner):
        with app.app_context():
            db = database.raw_connection()
            if poner:
                db.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT (SELECT id FROM roles WHERE code='usuario'), "
                    "       (SELECT id FROM permissions WHERE code=?) "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING", (codigo,))
            else:
                db.execute(
                    "DELETE FROM role_permissions "
                    "WHERE role_id = (SELECT id FROM roles WHERE code='usuario') "
                    "  AND permission_id = (SELECT id FROM permissions WHERE code=?)",
                    (codigo,))
            db.commit()
            db.close()

    _permiso_del_rol("calendario.ver", poner=False)
    comprobar("TC-07   sin `calendario.ver` el calendario da 403",
              jose_cli.get("/calendario/2026/8").status_code == 403,
              jose_cli.get("/calendario/2026/8").status_code)
    _permiso_del_rol("calendario.ver", poner=True)

    _permiso_del_rol("evento.crear", poner=False)
    r = _post(jose_cli, "/eventos/nuevo", title="No deberia entrar",
              start_date="2026-08-29", start_time="10:00",
              end_date="2026-08-29", end_time="11:00", color="#567C8D")
    comprobar("TC-07   sin `evento.crear` no se puede crear un evento (403)",
              r.status_code == 403 and _contar("No deberia entrar") == 0, r.status_code)
    _permiso_del_rol("evento.crear", poner=True)

    _permiso_del_rol("invitacion.responder", poner=False)
    comprobar("TC-07   sin `invitacion.responder` no se ve la invitacion (403)",
              ana_cli.get(f"/invitacion/{token}").status_code == 403)
    _permiso_del_rol("invitacion.responder", poner=True)

    # --- Transversales del modulo ----------------------------------------
    sin_csrf = _cliente(app); _entrar(sin_csrf, "josec", "Vibe2026!")
    r = sin_csrf.post("/eventos/nuevo", data={"title": "sin csrf",
                                              "start_date": "2026-08-30"})
    comprobar("        POST de evento sin token CSRF -> 400", r.status_code == 400,
              r.status_code)

    _post(jose_cli, "/eventos/nuevo", title="Color inyectado",
          start_date="2026-08-31", start_time="10:00",
          end_date="2026-08-31", end_time="11:00",
          color="red; background:url(javascript:alert(1))")
    with app.app_context():
        db = database.raw_connection()
        fila = db.execute("SELECT color FROM events WHERE title='Color inyectado'").fetchone()
        db.close()
    comprobar("        un color fuera de la paleta no entra a la base",
              fila is not None and fila["color"] in (
                  "#2F4156", "#567C8D", "#C8D9E6", "#D7707F", "#9DA3A4", "#4C4D53"),
              fila["color"] if fila else "no se creo el evento")

    html = jose_cli.get("/inicio").get_data(as_text=True)
    comprobar("        el menu enlaza el calendario de verdad",
              "/calendario" in html,
              "home.py apunta a un endpoint que no existe y sale 'Proximamente'")

    print("\n--- BLOQUE B: planner y kanban (US1-US4, US8-US9) ---")

    # --- TC-08: el desglose del puntaje NO cruza cuentas -----------------
    #
    # Aqui vivia un respaldo que leia de la tabla `tasks` de la v1 cuando la
    # tarea no era tuya. Como esa tabla no tiene `user_id`, devolvia CUALQUIER
    # tarea de CUALQUIER cuenta con HTTP 200.
    #
    # La prueba del Modulo B no lo veia porque su base deja la tabla v1 vacia:
    # el respaldo devolvia None y el 404 salia por casualidad. Por eso este
    # assert SIEMBRA una fila en la tabla v1 antes de preguntar: sin ese dato,
    # la comprobacion pasa sin comprobar nada.
    with app.app_context():
        db = database.raw_connection()
        db.execute("INSERT INTO tasks (title, due_date, estimated_minutes, priority_level) "
                   "VALUES ('Tarea heredada de la v1', '2026-08-20', 45, 1)")
        db.commit()
        tarea_v1 = db.execute(
            "SELECT id FROM tasks WHERE title='Tarea heredada de la v1'").fetchone()["id"]
        db.close()

    r = jose_cli.get(f"/v2/api/task/{tarea_v1}/score-breakdown?available=120")
    comprobar("TC-08   el desglose de una tarea ajena responde 404  <-- BLOQUEANTE",
              r.status_code == 404,
              f"devolvio {r.status_code}: se esta filtrando el puntaje de otra cuenta")

    # --- Aislamiento del planner ----------------------------------------
    r = _post(jose_cli, "/v2/tasks", title="Tarea de josec", due_date="2026-08-25",
              estimated_minutes="30", priority_level="1", category="Estudio")
    comprobar("        crear una tarea en el planner (302)", r.status_code == 302, r.status_code)

    html = ana_cli.get("/planner").get_data(as_text=True)
    comprobar("TC-11   ana no ve las tareas de josec en su planner",
              "Tarea de josec" not in html)
    html = ana_cli.get("/kanban").get_data(as_text=True)
    comprobar("TC-11   ...ni en su kanban", "Tarea de josec" not in html)

    with app.app_context():
        db = database.raw_connection()
        t_id = db.execute(
            "SELECT id FROM tasks_v2 WHERE title='Tarea de josec'").fetchone()["id"]
        db.close()

    r = _post(ana_cli, f"/v2/tasks/{t_id}/delete")
    with app.app_context():
        db = database.raw_connection()
        sigue = db.execute("SELECT COUNT(*) c FROM tasks_v2 WHERE id=?",
                           (t_id,)).fetchone()["c"]
        db.close()
    comprobar("TC-08   ana no puede borrar la tarea de josec", sigue == 1)

    r = ana_cli.get(f"/v2/api/task/{t_id}/score-breakdown")
    comprobar("TC-08   ...ni ver su desglose (404)", r.status_code == 404, r.status_code)

    print("\n--- Transversales ---")

    # --- CSRF -------------------------------------------------------------
    sin_token = app.test_client()
    r = sin_token.post("/login", data={"username": "admin", "password": "x"})
    comprobar("        POST sin token CSRF -> 400", r.status_code == 400, r.status_code)

    # --- R9: todo permiso usado en @requires existe en la tabla ----------
    #
    # Un permiso escrito en un decorador pero no sembrado es un 403 permanente
    # que nadie sabe explicar. Esta comprobacion cubre toda esa clase de fallo
    # de una vez, sin tener que acordarse de cada ruta.
    usados = set()
    for archivo in os.listdir(os.path.dirname(os.path.abspath(__file__))):
        if archivo.endswith(".py"):
            with open(archivo, "r", encoding="utf-8") as f:
                usados |= set(re.findall(r'@security\.requires\(\s*"([^"]+)"', f.read()))

    with app.app_context():
        db = database.raw_connection()
        sembrados = {f["code"] for f in db.execute("SELECT code FROM permissions").fetchall()}
        db.close()

    huerfanos = usados - sembrados
    comprobar(f"        los {len(usados)} permisos de @requires estan sembrados",
              not huerfanos, huerfanos)

    # --- Todo url_for() de toda plantilla apunta a un endpoint real ------
    #
    # Un url_for a un endpoint inexistente NO falla al arrancar: falla con
    # BuildError el dia que alguien abre esa pantalla, y el mensaje no dice de
    # que plantilla vino. Ya paso dos veces en este proyecto: home.py apuntaba
    # a `calendario.mes` (el menu salia "Proximamente") y templates/index.html
    # quedo llamando a `add_task_route` despues de retirar las rutas v1.
    endpoints_reales = set(app.view_functions)
    rotos = []
    raiz_plantillas = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    for carpeta, _, archivos in os.walk(raiz_plantillas):
        for archivo in archivos:
            if not archivo.endswith(".html"):
                continue
            ruta_plantilla = os.path.join(carpeta, archivo)
            with open(ruta_plantilla, "r", encoding="utf-8") as f:
                for endpoint in re.findall(r"url_for\(\s*['\"]([^'\"]+)['\"]", f.read()):
                    if endpoint not in endpoints_reales and endpoint != "static":
                        rotos.append(f"{archivo} -> {endpoint}")

    comprobar("        todo url_for() de las plantillas apunta a un endpoint real",
              not rotos, rotos)

    # --- Las FK se respetan de verdad ------------------------------------
    with app.app_context():
        db = database.raw_connection()
        try:
            db.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, 99999)",
                       (admin_id,))
            fk_activas = False
        except Exception:
            fk_activas = True
        db.close()
    comprobar("        PRAGMA foreign_keys activo en cada conexion", fk_activas)

    os.remove(ruta)

    print()
    if fallos:
        print(f"FALLARON {len(fallos)} comprobaciones:")
        for f in fallos:
            print(f"   - {f}")
        return 1

    print("SUCCESS: el nucleo del Modulo A esta en verde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
