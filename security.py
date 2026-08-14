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
    csrf_token()                    -> str      (para las plantillas)
    validate_csrf()                 -> bool
    init_app(app)                   (lo llama app.py una vez)

COMO SE USA EN UNA RUTA
    @planner.route("/mis-cosas")
    @requires("planner.ver")            # llave 1: el permiso
    def mis_cosas():
        user_id = current_user_id()     # llave 2: el filtro DENTRO del WHERE
        ...

Las dos llaves son necesarias. El decorador dice "puedes ver planners"; el
user_id dentro del WHERE dice "el tuyo". Con solo la primera, cualquiera con
`planner.ver` lee los datos de todos.

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

# Rutas de la v1 exentas de CSRF durante la transicion.
# Anadido 2026-08-13: son las 3 rutas de tareas monousuario, que hoy no tienen
# sesion que falsificar y cuyos formularios son de Ana. Desaparecen cuando el
# Modulo B reescriba el planner sobre `@login_required`, y con ellas esta lista.
# NADA nuevo entra aqui: si un formulario necesita exencion, esta mal disenado.
CSRF_EXENTAS = frozenset({
    "add_task_route",
    "delete_task_route",
    "update_status_route",
})


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
    """Sin sesion -> al login, recordando a donde queria ir."""
    @functools.wraps(vista)
    def envoltura(*args, **kwargs):
        if current_user() is None:
            # H3: si abrio un enlace concreto sin sesion, despues de entrar
            # vuelve ahi, no al inicio.
            session[SESSION_NEXT_KEY] = request.full_path
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)
    return envoltura


def requires(*codigos):
    """
    Exige TODOS los permisos indicados.

    Comprueba PERMISOS, nunca nombres de rol. Un `@admin_required` volveria a
    meter el rol dentro del codigo y anularia la tabla entera: si manana se
    crea un rol `soporte` con `usuario.listar`, con @requires entra solo y con
    @admin_required se queda fuera aunque tenga el permiso.
    """
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
    """
    El token de la sesion. Se genera la primera vez que una plantilla lo pide.

    Va en todo formulario POST:
        <input type="hidden" name="_csrf" value="{{ csrf_token() }}">
    """
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
    """Expone a Jinja2 lo que las plantillas necesitan sin pasarlo ruta por ruta."""
    app.context_processor(lambda: {
        "current_user": current_user,
        "current_roles": current_roles,
        "has_permission": has_permission,
        "csrf_token": csrf_token,
    })


def init_app(app):
    """
    Lo llama app.py una sola vez.

    El `before_request` valida el CSRF de TODO metodo que escriba, en todas las
    rutas a la vez. Ponerlo formulario por formulario es como se olvida uno:
    aqui la proteccion es el valor por defecto y saltarsela exige entrar en
    CSRF_EXENTAS, que se ve en la revision de codigo.
    """
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
