"""
VibePlanner v2 - Autenticacion (auth.py)
-----------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

Blueprint del registro publico, el login y el logout.

    Situacion                              Respuesta                   Codigo
    -------------------------------------  --------------------------  ------
    Registro valido                        crea, abre sesion, al home     302
    Datos invalidos                        vuelve al form con errores     400
    Usuario o correo duplicado             mensaje comun                  409
    Login correcto                         a `next` si existe, si no home 302
    Usuario o contrasena incorrectos       MISMO mensaje en ambos casos   401
    Cuenta desactivada                     mensaje explicito              403
    Ya autenticado abre /login o /register al home                        302
    /logout por GET                        no existe esa combinacion      405
"""

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

import repo_users
import security
import validators

auth = Blueprint("auth", __name__)

# =========================================================================
# REGLA DE ORO DEL REGISTRO PUBLICO
#
# Esta constante vive en el SERVIDOR. El formulario no decide roles: no tiene
# campo de roles, y si alguien lo anade con DevTools o manda el POST con curl,
# aqui no se lee. Un `role=admin` enviado a mano no otorga absolutamente nada.
#
# Es TC-03, uno de los tres casos que bloquean el release.
#
# Es exactamente lo contrario que en admin.py, donde los roles SI se leen del
# formulario -- porque quien llega a esa linea ya demostro tener el permiso.
# =========================================================================
PUBLIC_REGISTRATION_ROLES = ["usuario"]

MENSAJE_CREDENCIALES = "Usuario o contrasena incorrectos."


def _iniciar_sesion(user_id):
    """
    Sesion nueva y limpia.

    `session.clear()` antes de escribir el id evita la fijacion de sesion: si
    alguien logro plantar un identificador de sesion conocido en el navegador
    de la victima, al entrar se descarta y se genera otro.
    """
    destino = session.pop(security.SESSION_NEXT_KEY, None)
    session.clear()
    session[security.SESSION_USER_KEY] = user_id
    return destino


def _destino_seguro(destino):
    """
    Solo se admiten rutas internas.

    Sin esta comprobacion, /login?next=https://sitio-malo.example convierte
    nuestro login en un trampolin de phishing con nuestro dominio delante.
    """
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("home.index")


# --------------------------------------------------------------------------
# Registro
# --------------------------------------------------------------------------
@auth.route("/register", methods=["GET", "POST"])
def register():
    if security.current_user():
        return redirect(url_for("home.index"))

    if request.method == "GET":
        return render_template("auth/register.html", datos={}, errores={},
                               REGLAS=validators.REGLAS)

    datos, errores = validators.validar_datos_cuenta(request.form)

    if errores:
        # 400 y de vuelta al formulario CON lo que ya habia escrito (menos la
        # contrasena). Devolver el formulario en blanco castiga al usuario por
        # un error de un solo campo.
        return render_template("auth/register.html",
                               datos=validators.datos_para_repintar(datos),
                               errores=errores,
                               REGLAS=validators.REGLAS), 400

    user_id = repo_users.create_user(datos, PUBLIC_REGISTRATION_ROLES)

    if user_id is None:
        # 409. El mensaje NO dice cual de los dos esta tomado: decirlo
        # convertiria el registro en un comprobador de cuentas existentes.
        errores = {"username": "Ese usuario o correo ya esta registrado."}
        return render_template("auth/register.html",
                               datos=validators.datos_para_repintar(datos),
                               errores=errores,
                               REGLAS=validators.REGLAS,
                               ofrecer_login=True), 409

    _iniciar_sesion(user_id)
    flash(f"Cuenta creada. Bienvenido a VibePlanner, {datos['username']}.", "ok")
    return redirect(url_for("home.index"))


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():
    if security.current_user():
        return redirect(url_for("home.index"))

    if request.method == "GET":
        return render_template("auth/login.html", datos={}, error=None)

    username = validators.normalizar_username(request.form.get("username"))
    password = request.form.get("password") or ""

    usuario = repo_users.get_by_username(username)

    # verify_password gasta el mismo tiempo aunque `usuario` sea None: si no,
    # se pueden enumerar las cuentas validas cronometrando la respuesta.
    if not repo_users.verify_password(usuario, password):
        return render_template("auth/login.html",
                               datos={"username": username},
                               error=MENSAJE_CREDENCIALES), 401

    if not usuario["is_active"]:
        # Aqui SI se distingue, y a proposito: quien llega hasta este punto ya
        # demostro saber la contrasena, asi que no hay nada que enumerar, y
        # necesita saber por que no entra.
        return render_template("auth/login.html",
                               datos={"username": username},
                               error="Tu cuenta esta desactivada. Contacta al administrador."), 403

    destino = _iniciar_sesion(usuario["id"])
    return redirect(_destino_seguro(destino))


# --------------------------------------------------------------------------
# Logout
# --------------------------------------------------------------------------
@auth.route("/logout", methods=["POST"])
def logout():
    """
    Solo POST. Un logout por GET lo dispara cualquier <img src="/logout"> de
    otra pagina, y ademas los navegadores precargan enlaces: se cerraria la
    sesion sola. Por eso el menu usa un formulario, no un enlace.
    """
    session.clear()
    flash("Cerraste sesion.", "ok")
    return redirect(url_for("auth.login"))
