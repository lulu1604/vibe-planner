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

# Exenciones de CSRF
CSRF_EXENTAS = frozenset({
    "add_task_route",
    "delete_task_route",
    "update_status_route",
})


# --------------------------------------------------------------------------
# Quien es el que pregunta
# --------------------------------------------------------------------------
def current_user():
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
    if "permisos" not in g:
        usuario = current_user()
        g.permisos = repo_users.get_permissions(usuario["id"]) if usuario else set()
    return g.permisos


def has_permission(codigo):
    return codigo in effective_permissions()


def current_roles():
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
