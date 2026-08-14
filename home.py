"""
VibePlanner v2 - Inicio y menu (home.py)
-----------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

El menu de la aplicacion. Se construye a partir de los PERMISOS de la cuenta,
no de sus roles: asi, cuando manana exista un rol `soporte` con
`usuario.listar`, la entrada de Administracion le aparece sola sin tocar una
linea de aqui.

Ocultar una entrada del menu es CORTESIA VISUAL, no seguridad. La ruta sigue
protegida por @requires en el servidor y responde 403 aunque se escriba la URL
a mano (TC-07).
"""

from flask import Blueprint, render_template, url_for
from werkzeug.routing import BuildError

import repo_users
import security

home = Blueprint("home", __name__)


# --------------------------------------------------------------------------
# Los modulos de la aplicacion.
#
# `endpoint` apunta a blueprints que todavia no existen (los de Lucero, Jose y
# Ana). No es un error: mientras no esten registrados, la entrada se muestra
# apagada con "Proximamente" en vez de romper la pagina con un BuildError.
# En cuanto alguien registre su blueprint, su entrada se enciende sola.
# --------------------------------------------------------------------------
MODULOS = [
    {
        "clave": "planner",
        "etiqueta": "Planner",
        "descripcion": "Tu plan del dia, ordenado por puntaje.",
        "permiso": "planner.ver",
        "endpoint": "planner.dia",
        "icono": "M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01",
    },
    {
        "clave": "kanban",
        "etiqueta": "Tablero",
        "descripcion": "Arrastra tus actividades entre columnas.",
        "permiso": "kanban.ver",
        "endpoint": "planner.kanban",
        "icono": "M3.75 4.5h4.5v15h-4.5zM9.75 4.5h4.5v10.5h-4.5zM15.75 4.5h4.5v7.5h-4.5z",
    },
    {
        "clave": "calendario",
        "etiqueta": "Calendario",
        "descripcion": "Tus eventos del mes y tus invitaciones.",
        "permiso": "calendario.ver",
        "endpoint": "calendario.mes",
        "icono": ("M6.75 3v2.25M17.25 3v2.25M3.75 7.5h16.5M4.5 5.25h15a.75.75 0 0 1 .75.75"
                  "v13.5a.75.75 0 0 1-.75.75h-15a.75.75 0 0 1-.75-.75V6a.75.75 0 0 1 .75-.75z"),
    },
    {
        "clave": "habitos",
        "etiqueta": "Habitos",
        "descripcion": "Tus rachas de sueno, ejercicio y alimentacion.",
        "permiso": "habito.ver",
        "endpoint": "habitos.lista",
        "icono": "M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
    },
    {
        "clave": "metricas",
        "etiqueta": "Metricas",
        "descripcion": "Cuanto completaste y en que se te va el tiempo.",
        "permiso": "metrica.propia.ver",
        "endpoint": "habitos.metricas",
        "icono": "M3 20.25h18M7.5 20.25V12M12 20.25V6.75M16.5 20.25v-6",
    },
    {
        "clave": "admin",
        "etiqueta": "Administracion",
        "descripcion": "Cuentas del sistema, roles y permisos.",
        "permiso": "usuario.listar",
        "endpoint": "admin.usuarios",
        "icono": ("M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0"
                  "-7.533-2.493M15 19.128c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1"
                  " 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07"
                  "M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0zm8.25 2.25a2.625 2.625"
                  " 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0z"),
    },
    {
        "clave": "perfil",
        "etiqueta": "Mi perfil",
        "descripcion": "Tus datos y tu contrasena.",
        "permiso": "perfil.ver",
        "endpoint": "perfil.ver",
        "icono": ("M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0zM4.501 20.118a7.5 7.5 0 0 1"
                  " 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632z"),
    },
]


def _url_o_none(endpoint):
    """
    La URL del endpoint, o None si el blueprint aun no esta registrado.

    Sin este try, una sola entrada de un modulo que todavia no existe tumba el
    menu entero con un BuildError -- y con el, TODAS las pantallas, porque el
    menu vive en base.html.
    """
    try:
        return url_for(endpoint)
    except BuildError:
        return None


def menu_visible():
    """
    Las entradas que esta cuenta puede ver, ya resueltas.

    Cada una trae `url` (None si el modulo no existe todavia) y `disponible`.
    """
    entradas = []
    for modulo in MODULOS:
        if not security.has_permission(modulo["permiso"]):
            continue
        url = _url_o_none(modulo["endpoint"])
        entrada = dict(modulo)
        entrada["url"] = url
        entrada["disponible"] = url is not None
        entradas.append(entrada)
    return entradas


def register_menu(app):
    """Expone el menu a todas las plantillas: base.html lo necesita siempre."""
    app.context_processor(lambda: {"menu_visible": menu_visible})


@home.route("/inicio")
@security.login_required
def index():
    usuario = security.current_user()
    entradas = menu_visible()

    return render_template(
        "home.html",
        usuario=usuario,
        entradas=[e for e in entradas if e["clave"] != "perfil"],
        roles=repo_users.get_roles(usuario["id"]),
    )
