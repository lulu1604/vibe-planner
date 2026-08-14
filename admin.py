"""
VibePlanner v2 - Panel de administracion (admin.py)
----------------------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)
Cierra la historia US7: gestion de usuarios.

    Ruta                              Metodo  Permiso
    --------------------------------  ------  ------------------
    /admin/usuarios                   GET     usuario.listar
    /admin/usuarios                   POST    usuario.crear
    /admin/usuarios/<id>/roles        POST    rol.asignar
    /admin/usuarios/<id>/estado       POST    usuario.desactivar
    /admin/usuarios/<id>/password     POST    usuario.editar
    /admin/usuarios/disponible        GET     usuario.crear

UN PERMISO DISTINTO POR ACCION. Listar no implica crear, y crear no implica
asignar roles. Si todo colgara de un unico `admin.todo`, el dia que exista un
rol de soporte que solo deba VER las cuentas no habria forma de expresarlo.

LO QUE NO EXISTE AQUI, Y NO ES UN OLVIDO:
  - No hay ninguna ruta de BORRADO de usuarios. Solo se desactiva. Las tareas
    y los eventos de una cuenta desactivada siguen existiendo (TC-05).
  - No hay ninguna forma de VER una contrasena. Solo de asignar una nueva.
"""

from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, url_for)

import config
import repo_users
import security
import validators
from repo_users import SinAdministradores

admin = Blueprint("admin", __name__, url_prefix="/admin")

MENSAJE_SIN_ADMINS = ("No puedes dejar el sistema sin administradores. "
                      "Asigna el rol Administrador a otra cuenta activa antes "
                      "de quitarte el tuyo.")


def _usuario_o_404(user_id):
    """
    Sin esto, assign_roles() y set_active() sobre un id inexistente no fallan:
    hacen un UPDATE de cero filas y la pantalla dice alegremente "Guardado".
    """
    usuario = repo_users.get_by_id(user_id)
    if usuario is None:
        abort(404)
    return usuario


def _nombres_de_roles(codigos, catalogo):
    """['admin','usuario'] -> 'Administrador y Usuario' (idioma de persona)."""
    por_codigo = {r["code"]: r["name"] for r in catalogo}
    nombres = [por_codigo.get(c, c) for c in codigos]
    if len(nombres) <= 1:
        return nombres[0] if nombres else "ninguno"
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _pintar_listado(datos=None, errores=None, form_abierto=False, codigo=200):
    """
    Dibuja la pantalla de usuarios.

    Se saca a una funcion porque la pinta tanto el GET como el POST fallido:
    duplicar la consulta es como los dos caminos acaban mostrando cosas
    distintas.
    """
    busqueda = validators.normalizar_busqueda(request.args.get("q"))
    pagina = request.args.get("page", 1, type=int) or 1

    total = repo_users.count_users(search=busqueda or None)
    por_pagina = config.USUARIOS_POR_PAGINA
    total_paginas = max(1, -(-total // por_pagina))   # division techo

    # La pagina se acota en vez de rechazarse: un `?page=99` no lo escribio el
    # usuario, lo genero un enlace viejo. Un 400 ahi seria castigarle por algo
    # que no hizo.
    pagina = min(max(pagina, 1), total_paginas)

    usuarios = repo_users.list_users(
        search=busqueda or None,
        limit=por_pagina,
        offset=(pagina - 1) * por_pagina,
    )

    return render_template(
        "admin/usuarios.html",
        usuarios=usuarios,
        catalogo_roles=repo_users.list_roles(),
        yo=security.current_user_id(),
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        busqueda=busqueda,
        datos=datos or {},
        errores=errores or {},
        form_abierto=form_abierto,
        seccion_activa="admin",
        REGLAS=validators.REGLAS,
    ), codigo


# --------------------------------------------------------------------------
# Listado
# --------------------------------------------------------------------------
@admin.route("/usuarios")
@security.requires("usuario.listar")
def usuarios():
    return _pintar_listado()


# --------------------------------------------------------------------------
# Alta de cuenta
# --------------------------------------------------------------------------
@admin.route("/usuarios", methods=["POST"])
@security.requires("usuario.crear")
def crear_usuario():
    # MISMAS reglas que el registro publico, misma funcion. Antes el alta
    # administrativa pasaba request.form crudo al repositorio y aceptaba un
    # usuario vacio con una contrasena de un caracter.
    datos, errores = validators.validar_datos_cuenta(request.form)

    # AQUI SI se leen los roles del formulario -- es exactamente lo contrario
    # del registro publico. La diferencia no es el formulario, es quien lo
    # envia: para llegar a esta linea hay que tener `usuario.crear`, y eso ya
    # se comprobo arriba. Aun asi pasan por la lista blanca: nunca se inserta
    # un codigo que venga del navegador sin comprobarlo.
    roles = validators.validar_roles(request.form.getlist("roles"))

    if errores:
        return _pintar_listado(
            datos=validators.datos_para_repintar(datos),
            errores=errores,
            form_abierto=True,
            codigo=400,
        )

    user_id = repo_users.create_user(datos, roles, granted_by=security.current_user_id())

    if user_id is None:
        # En el panel SI se dice cual choca: aqui no hay riesgo de enumeracion
        # (quien mira ya puede listar todas las cuentas) y el administrador
        # necesita saber cual de los dos campos corregir.
        errores = {}
        if repo_users.exists_username(datos["username"]):
            errores["username"] = "Ese nombre de usuario ya esta en uso."
        if repo_users.exists_email(datos["email"]):
            errores["email"] = "Ese correo ya esta registrado en otra cuenta."
        return _pintar_listado(
            datos=validators.datos_para_repintar(datos),
            errores=errores or {"username": "No se pudo crear la cuenta."},
            form_abierto=True,
            codigo=409,
        )

    nombres = _nombres_de_roles(roles, repo_users.list_roles())
    flash(f"Cuenta {datos['username']} creada con los roles {nombres}.", "ok")
    return redirect(url_for("admin.usuarios"))


# --------------------------------------------------------------------------
# Cambio de roles
# --------------------------------------------------------------------------
@admin.route("/usuarios/<int:user_id>/roles", methods=["POST"])
@security.requires("rol.asignar")
def cambiar_roles(user_id):
    usuario = _usuario_o_404(user_id)
    roles = validators.validar_roles(request.form.getlist("roles"))

    try:
        repo_users.assign_roles(user_id, roles, granted_by=security.current_user_id())
    except SinAdministradores:
        # La regla no se comprueba aqui: se comprueba DENTRO de la transaccion
        # del repositorio, mirando el resultado real. Comprobarla aqui antes de
        # escribir dejaria una carrera entre dos administradores simultaneos.
        flash(MENSAJE_SIN_ADMINS, "error")
        return redirect(url_for("admin.usuarios"))

    nombres = _nombres_de_roles(roles, repo_users.list_roles())
    # H1: el mensaje dice QUE quedo, no "Guardado". Quien acaba de tocar los
    # roles de otra persona necesita ver el resultado, no una palmadita.
    flash(f"Roles de {usuario['username']} actualizados: {nombres}.", "ok")
    return redirect(url_for("admin.usuarios"))


# --------------------------------------------------------------------------
# Activar / desactivar
# --------------------------------------------------------------------------
@admin.route("/usuarios/<int:user_id>/estado", methods=["POST"])
@security.requires("usuario.desactivar")
def cambiar_estado(user_id):
    usuario = _usuario_o_404(user_id)
    nuevo = validators.validar_estado(request.form.get("is_active"))

    if nuevo is None:
        flash("No se pudo cambiar el estado. Vuelve a intentarlo.", "error")
        return redirect(url_for("admin.usuarios"))

    # Prevencion antes que explicacion: aunque la regla del ultimo admin ya lo
    # atraparia en la mayoria de los casos, desactivarse a uno mismo nunca es
    # lo que se queria hacer -- deja a la persona fuera de su propia sesion.
    if user_id == security.current_user_id() and nuevo == 0:
        flash("No puedes desactivar tu propia cuenta. Pideselo a otro administrador.", "error")
        return redirect(url_for("admin.usuarios"))

    try:
        repo_users.set_active(user_id, nuevo)
    except SinAdministradores:
        flash(MENSAJE_SIN_ADMINS, "error")
        return redirect(url_for("admin.usuarios"))

    if nuevo == 0:
        flash(f"Cuenta de {usuario['username']} desactivada. Sus datos se conservan.", "ok")
    else:
        flash(f"Cuenta de {usuario['username']} reactivada.", "ok")
    return redirect(url_for("admin.usuarios"))


# --------------------------------------------------------------------------
# Restablecer contrasena
# --------------------------------------------------------------------------
@admin.route("/usuarios/<int:user_id>/password", methods=["POST"])
@security.requires("usuario.editar")
def restablecer_password(user_id):
    """
    RESTABLECER, no recuperar. La contrasena anterior no se puede leer: lo que
    hay guardado es un hash, y ese es justamente el punto. El administrador
    asigna una nueva y se la comunica por fuera.
    """
    usuario = _usuario_o_404(user_id)
    nueva = request.form.get("password") or ""

    error = validators.validar_password(nueva, usuario["username"], usuario["email"])
    if error:
        flash(error, "error")
        return redirect(url_for("admin.usuarios"))

    repo_users.set_password(user_id, nueva)
    flash(f"Contrasena de {usuario['username']} restablecida.", "ok")
    return redirect(url_for("admin.usuarios"))


# --------------------------------------------------------------------------
# Comprobacion de disponibilidad (la usa ui.js al salir del campo)
# --------------------------------------------------------------------------
@admin.route("/usuarios/disponible")
@security.requires("usuario.crear")
def usuario_disponible():
    """
    Evita rellenar el formulario entero para descubrir al enviarlo que el
    nombre ya existia.

    Exige `usuario.crear` a proposito: sin el permiso, este endpoint seria un
    comprobador publico de que cuentas existen en el sistema.
    """
    username = validators.normalizar_username(request.args.get("username"))
    if validators.validar_username(username):
        return jsonify({"disponible": False, "motivo": "formato"})
    return jsonify({"disponible": not repo_users.exists_username(username)})
