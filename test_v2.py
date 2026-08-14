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

    comprobar("TC 6.1  un rol -> 17 permisos", len(p_piero) == 17, len(p_piero))
    comprobar("TC 6.2  dos roles -> 23 permisos (la union)", len(p_admin) == 23, len(p_admin))
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
