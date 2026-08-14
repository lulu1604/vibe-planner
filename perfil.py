"""
VibePlanner v2 - Perfil propio (perfil.py)
-------------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

    Ruta              Metodo  Permiso
    ----------------  ------  --------------
    /perfil           GET     perfil.ver
    /perfil           POST    perfil.editar
    /perfil/password  POST    perfil.editar

Es la contraparte de usuario del restablecimiento del administrador: sin esta
pantalla, la unica forma de cambiar tu propia contrasena seria pedirsela a un
administrador, que ademas tendria que elegirla por ti.

AQUI NO SE TOCAN LOS ROLES. Ni siquiera para verlos como campo editable: si
una cuenta pudiera cambiarse sus propios roles, cualquiera se haria
administrador y toda la tabla de permisos sobraria. Los roles solo se cambian
desde admin.py, con el permiso `rol.asignar`.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

import repo_users
import security
import validators

perfil = Blueprint("perfil", __name__, url_prefix="/perfil")


def _pintar(datos=None, errores=None, codigo=200):
    usuario = security.current_user()
    base = {"full_name": usuario["full_name"], "email": usuario["email"]}
    base.update(datos or {})

    return render_template(
        "perfil/perfil.html",
        usuario=usuario,
        roles=security.current_roles(),
        permisos=sorted(security.effective_permissions()),
        datos=base,
        errores=errores or {},
        seccion_activa="perfil",
        REGLAS=validators.REGLAS,
    ), codigo


@perfil.route("")
@security.requires("perfil.ver")
def ver():
    return _pintar()


@perfil.route("", methods=["POST"])
@security.requires("perfil.editar")
def guardar():
    """
    Solo nombre y correo. El nombre de usuario no se cambia: es la identidad
    con la que entras y con la que te ven los demas, y renombrarla dejaria
    huerfano cualquier sitio donde ya se hubiera mostrado.
    """
    user_id = security.current_user_id()

    datos = {
        "full_name": validators.normalizar_nombre(request.form.get("full_name")),
        "email": validators.normalizar_email(request.form.get("email")),
    }

    errores = {}
    for campo, error in (
        ("full_name", validators.validar_nombre_completo(datos["full_name"])),
        ("email", validators.validar_email(datos["email"])),
    ):
        if error:
            errores[campo] = error

    # `excluir_id` es lo que evita que tu propio correo choque contigo mismo
    # al guardar sin haberlo cambiado.
    if not errores and repo_users.exists_email(datos["email"], excluir_id=user_id):
        errores["email"] = "Ese correo ya esta registrado en otra cuenta."

    if errores:
        return _pintar(datos=datos, errores=errores, codigo=400)

    repo_users.update_profile(user_id, datos["full_name"], datos["email"])
    flash("Tus datos quedaron actualizados.", "ok")
    return redirect(url_for("perfil.ver"))


@perfil.route("/password", methods=["POST"])
@security.requires("perfil.editar")
def cambiar_password():
    usuario = security.current_user()
    actual = request.form.get("password_actual") or ""
    nueva = request.form.get("password") or ""

    # Pedir la contrasena actual protege el caso real: alguien se levanta y
    # deja la sesion abierta. Sin esta comprobacion, quien pase por delante
    # se queda con la cuenta cambiandole la clave en dos clics.
    if not repo_users.verify_password(usuario, actual):
        return _pintar(errores={"password_actual": "Tu contrasena actual no es correcta."},
                       codigo=400)

    error = validators.validar_password(nueva, usuario["username"], usuario["email"])
    if error:
        return _pintar(errores={"password": error}, codigo=400)

    if actual == nueva:
        return _pintar(errores={"password": "La contrasena nueva tiene que ser distinta de la actual."},
                       codigo=400)

    repo_users.set_password(usuario["id"], nueva)
    flash("Tu contrasena quedo actualizada.", "ok")
    return redirect(url_for("perfil.ver"))
