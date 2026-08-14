"""
VibePlanner v2 - La guardia (security.py)
------------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

*** CONTRATO CONGELADO - HITO H2 ***
Esto es lo que importan los modulos B, C y D. Cambiar una firma de aqui obliga
a avisar al grupo ANTES, porque rompe codigo de otras tres personas.

    current_user()                  -> dict | None
    current_user_id()               -> int  | None
    effective_permissions()         -> set[str]
    has_permission("codigo")        -> bool
    @login_required
    @requires("codigo", ...)
    current_roles()                 -> list[dict]   (solo para PINTAR)
    csrf_token()                    -> str          (para las plantillas)
    validate_csrf()                 -> bool
    init_app(app)                   (lo llama app.py una vez)

COMO SE USA EN UNA RUTA
    @calendar_bp.route("/calendario")
    @requires("calendario.ver")         # llave 1: el permiso
    def mes():
        user_id = current_user_id()     # llave 2: el filtro DENTRO del WHERE
        ...

Las dos llaves son necesarias. El decorador dice "puedes ver calendarios"; el
user_id dentro del WHERE dice "el tuyo". Con solo la primera, cualquiera con
`calendario.ver` lee los datos de todos.

@requires comprueba PERMISOS, nunca nombres de rol, y nunca se sustituye por
@login_required "porque total, todos lo tienen": un permiso que no se comprueba
en ningun sitio es un permiso que el administrador cree que puede quitar y no
puede. Si manana existe un rol `soporte` con `usuario.listar`, con @requires
entra solo; con @login_required no hay forma de expresarlo.

Y en las plantillas:
    {% if has_permission('usuario.listar') %} ... {% endif %}
Eso es CORTESIA VISUAL, no seguridad: oculta el boton, no protege la ruta. La
ruta la protege @requires en el servidor, y sigue protegida aunque alguien
escriba la URL a mano.
"""

import functools
import hmac
import secrets

from flask import abort, g, redirect, request, session, url_for

import repo_users

SESSION_USER_KEY = "user_id"
SESSION_NEXT_KEY = "next"
SESSION_CSRF_KEY = "_csrf"
CSRF_FIELD = "_csrf"

METODOS_SEGUROS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# Exenciones de CSRF. ESTA VACIA, Y ASI DEBE QUEDARSE.
#
# Existio brevemente para las 3 rutas de tareas de la v1, cuyos formularios no
# tenian token. Al actualizar esa pantalla a la v2 se les anadio y la lista se
# quedo sin nada dentro, que es donde tiene que estar.
#
# Un merge posterior la reintrodujo y `POST /tasks` volvio a aceptarse sin
# token: las plantillas YA mandan el token, asi que la exencion no aportaba
# nada y solo reabria el agujero. Si manana un formulario "necesita" entrar
# aqui, lo que hay que arreglar es el formulario.
CSRF_EXENTAS = frozenset()


# --------------------------------------------------------------------------
# Quien es el que pregunta
# --------------------------------------------------------------------------
def current_user():
    """
    La cuenta de la sesion, o None.

    Se cachea en `g`, que dura UNA peticion. Si la cuenta se desactivo o se
    borro entre dos clics, la sesion se cierra aqui mismo: la cookie sigue
    siendo valida criptograficamente, pero la cuenta ya no.
    """
    if "usuario" not in g:
        g.usuario = None
        user_id = session.get(SESSION_USER_KEY)
        if user_id is not None:
            usuario = repo_users.get_by_id(user_id)
            if usuario is None or not usuario["is_active"]:
                session.clear()
            else:
                g.usuario = usuario
    return g.usuario


def current_user_id():
    usuario = current_user()
    return usuario["id"] if usuario else None


def effective_permissions():
    """
    La union de los permisos de todos los roles de la cuenta.

    SE CACHEAN EN `g`, JAMAS EN LA SESION. Es la decision de seguridad mas
    importante de este archivo: si vivieran en la cookie, quitarle el rol
    `admin` a alguien no tendria ningun efecto hasta que cerrara sesion, y
    mientras tanto seguiria administrando el sistema con una cookie caducada
    en la practica. `g` dura una peticion, asi que el cambio se nota en la
    siguiente recarga (TC-09).
    """
    if "permisos" not in g:
        usuario = current_user()
        g.permisos = repo_users.get_permissions(usuario["id"]) if usuario else set()
    return g.permisos


def has_permission(codigo):
    return codigo in effective_permissions()


def current_roles():
    """
    Los roles de la cuenta, para PINTARLOS ("Usuario", "Administrador").

    Solo para mostrar. Ninguna decision de acceso mira esta lista: para eso
    esta has_permission(). Si alguien empieza a escribir
    `if 'admin' in current_roles()`, la tabla de permisos deja de servir para
    nada y volvemos a tener el rol incrustado en el codigo.
    """
    if "roles" not in g:
        usuario = current_user()
        g.roles = repo_users.get_roles(usuario["id"]) if usuario else []
    return g.roles


# --------------------------------------------------------------------------
# Decoradores
# --------------------------------------------------------------------------
def login_required(vista):
    @functools.wraps(vista)
    def envoltura(*args, **kwargs):
        if current_user() is None:
            session[SESSION_NEXT_KEY] = request.full_path
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)
    return envoltura


def requires(*codigos):
    def decorador(vista):
        @functools.wraps(vista)
        @login_required
        def envoltura(*args, **kwargs):
            faltantes = [c for c in codigos if not has_permission(c)]
            if faltantes:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


# --------------------------------------------------------------------------
# CSRF
# --------------------------------------------------------------------------
def csrf_token():
    if SESSION_CSRF_KEY not in session:
        session[SESSION_CSRF_KEY] = secrets.token_urlsafe(32)
    return session[SESSION_CSRF_KEY]


def validate_csrf():
    """
    `compare_digest` en vez de `==` para no filtrar por tiempo cuantos
    caracteres iniciales acerto quien lo esta adivinando.
    """
    esperado = session.get(SESSION_CSRF_KEY) or ""
    enviado = request.form.get(CSRF_FIELD) or request.headers.get("X-CSRF-Token") or ""
    if not esperado or not enviado:
        return False
    return hmac.compare_digest(esperado, enviado)


# --------------------------------------------------------------------------
# Enganche con la aplicacion
# --------------------------------------------------------------------------
def register_template_helpers(app):
    app.context_processor(lambda: {
        "current_user": current_user,
        "current_roles": current_roles,
        "has_permission": has_permission,
        "csrf_token": csrf_token,
    })


def init_app(app):
    @app.before_request
    def _validar_csrf():
        if request.method in METODOS_SEGUROS:
            return None
        if request.endpoint in CSRF_EXENTAS:
            return None
        if not validate_csrf():
            abort(400, description=(
                "Tu sesion caduco o el formulario estuvo abierto demasiado tiempo. "
                "Vuelve a intentarlo."
            ))
        return None

    register_template_helpers(app)
    return app
