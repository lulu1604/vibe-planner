"""
VibePlanner v2 - Pruebas de regresion de la auditoria de integracion
======================================================================
    python test_auditoria.py

Un caso por defecto encontrado el 14/08/2026 al unir los Modulos A, C y D.
Ninguno lo cubria test_v2.py, test_module_c.py ni test_module_d.py: los tres
prueban su modulo por dentro, y estos seis fallos solo aparecen al cruzar dos
modulos o al atacar una ruta desde fuera del navegador.

Si alguno de estos vuelve a fallar, el defecto ha vuelto.
"""

import os
import re
import sqlite3
import tempfile

os.environ.setdefault("VIBEPLANNER_SECRET", "test-auditoria")

import database

_fd, _RUTA = tempfile.mkstemp(suffix=".db")
os.close(_fd)
database.DB_PATH = _RUTA

import seed
seed.main()

from app import app
import repo_users

app.config["TESTING"] = True

CSRF = "token-de-prueba"
OK, FALLOS = [], []


def check(cid, nombre, condicion, detalle=""):
    (OK if condicion else FALLOS).append(cid)
    print(("  OK    " if condicion else "  FALLA") + " %-7s %s" % (cid, nombre))
    if not condicion and detalle:
        print("            -> " + detalle)


def cliente(user_id=None):
    c = app.test_client()
    with c.session_transaction() as s:
        if user_id:
            s["user_id"] = user_id
        s["_csrf"] = CSRF
    return c


def post(c, url, datos=None, **kw):
    d = dict(datos or {})
    d["_csrf"] = CSRF
    return c.post(url, data=d, **kw)


def fila(sql, args=()):
    with app.app_context():
        return database.raw_connection().execute(sql, args).fetchone()


with app.app_context():
    for u in ("ana", "jose"):
        if not repo_users.get_by_username(u):
            repo_users.create_user(
                {"username": u, "email": u + "@auditoria.local", "password": "Vibe2026!"},
                ["usuario"])
    ANA = repo_users.get_by_username("ana")["id"]
    JOSE = repo_users.get_by_username("jose")["id"]

ca, cj = cliente(ANA), cliente(JOSE)
anon = cliente()

EVENTO = {"title": "Evento de auditoria", "start_date": "2026-09-10",
          "start_time": "09:00", "end_date": "2026-09-10", "end_time": "10:00",
          "color": "#567C8D"}


print("\n--- A-01  Las rutas v1 no exponen datos sin sesion ---")
# Antes: GET / listaba las tareas de TODO el mundo sin pedir sesion, y
# POST /tasks/<id>/delete borraba filas para cualquier anonimo.
r = anon.get("/")
check("A-01a", "GET / sin sesion NO devuelve una pagina con datos",
      r.status_code in (301, 302), "devolvio %s" % r.status_code)
for ruta in ("/tasks", "/tasks/1/delete", "/tasks/1/status"):
    r = post(anon, ruta, {"title": "x", "due_date": "2026-09-10"})
    check("A-01b", "POST %-18s sin sesion no escribe" % ruta,
          r.status_code in (400, 401, 403, 404, 405) or "/login" in r.headers.get("Location", ""),
          "devolvio %s" % r.status_code)
r = anon.get("/api/task/1/score-breakdown")
check("A-01c", "el desglose del puntaje no es publico",
      r.status_code in (301, 302, 401, 403, 404), "devolvio %s" % r.status_code)

libres = []
for regla in app.url_map.iter_rules():
    if str(regla).startswith("/static"):
        continue
    if getattr(app.view_functions[regla.endpoint], "__wrapped__", None) is None:
        libres.append(str(regla))
check("A-01d", "solo /, /login, /register y /logout viven sin decorador",
      set(libres) <= {"/", "/login", "/register", "/logout"},
      "tambien sueltas: %s" % sorted(set(libres) - {"/", "/login", "/register", "/logout"}))


print("\n--- A-02  /eventos/<id>/editar valida `status` (era un HTTP 500) ---")
post(cj, "/eventos/nuevo", EVENTO)
EID = fila("SELECT id FROM events WHERE title=?", (EVENTO["title"],))["id"]
try:
    datos = dict(EVENTO)
    datos["status"] = "INVENTADO"
    r = post(cj, "/eventos/%d/editar" % EID, datos)
    estado = fila("SELECT status FROM events WHERE id=?", (EID,))["status"]
    check("A-02", "un `status` fuera de la lista blanca no revienta",
          r.status_code < 500 and estado in ("tentativo", "confirmado", "cancelado"),
          "HTTP %s, status guardado=%r" % (r.status_code, estado))
except sqlite3.IntegrityError as e:
    check("A-02", "un `status` fuera de la lista blanca no revienta", False,
          "IntegrityError sin capturar = 500: %s" % e)


print("\n--- A-03  /eventos/<id>/editar valida el titulo igual que /nuevo ---")
vacio = dict(EVENTO)
vacio["title"] = ""
post(cj, "/eventos/%d/editar" % EID, vacio)
titulo = fila("SELECT title FROM events WHERE id=?", (EID,))["title"]
check("A-03", "un titulo vacio se rechaza al editar", bool(titulo),
      "el evento quedo con title=%r y desaparece de la cuadricula" % titulo)


print("\n--- A-04  El calendario usa la hora de Lima, no la del servidor ---")
fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar_bp.py"),
              encoding="utf-8").read()
check("A-04a", "calendar_bp no llama a datetime.now() sin zona",
      "datetime.now()" not in fuente,
      "%d llamadas sin zona: despues de las 19:00 de Lima el servidor ya esta en manana"
      % fuente.count("datetime.now()"))
import fechas
import calendar_bp as _cbp
check("A-04b", "_current_local_year_month() coincide con la hora de Lima",
      _cbp._current_local_year_month() == fechas.anio_mes_local())


print("\n--- A-05  Eliminar un evento ajeno responde 404, como editar e invitar ---")
r = post(ca, "/eventos/%d/eliminar" % EID)
vive = fila("SELECT COUNT(*) c FROM events WHERE id=?", (EID,))["c"]
check("A-05a", "ana eliminando el evento de jose -> 404", r.status_code == 404,
      "devolvio %s: un 302 con flash distingue lo ajeno de lo inexistente" % r.status_code)
check("A-05b", "y el evento de jose sigue existiendo", bool(vive))


print("\n--- A-06  El registro diario de un habito valida su rango ---")
post(ca, "/habitos", {"name": "Habito de auditoria", "habit_type": "ejercicio",
                      "target_value": "30", "unit": "minutos"})
HID = fila("SELECT id FROM habits WHERE name='Habito de auditoria'")["id"]
for valor in ("-5", "999999"):
    post(ca, "/habitos/%d/registro" % HID, {"done": "1", "value": valor})
    reg = fila("SELECT value FROM habit_logs WHERE habit_id=?", (HID,))
    check("A-06", "value=%-8r no llega a la base" % valor, reg is None,
          "se guardo %s y el usuario no puede corregirlo desde ninguna pantalla"
          % (reg["value"] if reg else None))
post(ca, "/habitos/%d/registro" % HID, {"done": "1", "value": "30"})
reg = fila("SELECT value FROM habit_logs WHERE habit_id=?", (HID,))
check("A-06b", "un valor valido si se guarda", reg is not None and reg["value"] == 30.0)


print("\n--- A-07  Aislamiento entre cuentas (control, no debe romperse) ---")
post(ca, "/habitos", {"name": "ZZSOLODEANA", "habit_type": "dieta",
                      "target_value": "3", "unit": "vasos"})
html = cj.get("/habitos").data.decode("utf8", "ignore")
check("A-07a", "jose no ve el habito de ana", "ZZSOLODEANA" not in html)
r = post(cj, "/habitos/%d/registro" % HID, {"done": "1", "value": "10"})
check("A-07b", "jose registrando el habito de ana -> 404", r.status_code == 404,
      "devolvio %s" % r.status_code)


print("\n" + "=" * 66)
print("%d OK - %d FALLAS" % (len(OK), len(FALLOS)))
if FALLOS:
    print("Han vuelto: " + ", ".join(sorted(set(FALLOS))))
else:
    print("SUCCESS: los seis defectos de la auditoria siguen corregidos.")

with app.app_context():
    database.close_db()
for sufijo in ("", "-wal", "-shm"):
    try:
        os.unlink(_RUTA + sufijo)
    except OSError:
        pass

raise SystemExit(1 if FALLOS else 0)
