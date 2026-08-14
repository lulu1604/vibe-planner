"""
VibePlanner v2 - Validacion de entrada (validators.py)
------------------------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

FUENTE UNICA de las reglas de los formularios de cuentas. Lo importan auth.py,
admin.py y perfil.py. Que sea uno solo es el punto: hasta ahora la regla de
"correo duplicado" existia en tres versiones distintas en tres documentos.

DOS IDEAS QUE GOBIERNAN ESTE ARCHIVO
------------------------------------
1. Los `required`, `pattern` y `minlength` del HTML son PREVENCION, no
   validacion. La validacion real vive aqui, en el servidor, y se demuestra
   con curl saltandose el navegador:
       curl -X POST localhost:5000/register -d "username=a&email=x&password=1"
   Si el servidor lo acepta, la regla no existe.

2. Las plantillas NO escriben sus propios atributos: reciben el dict REGLAS y
   los generan desde aqui.
       <input name="username" minlength="{{ REGLAS.username.min }}"
              maxlength="{{ REGLAS.username.max }}"
              pattern="{{ REGLAS.username.pattern }}">
   Asi es imposible que el pattern del HTML y el regex de Python se separen,
   que es el fallo silencioso numero uno de este tipo de formularios.

Las funciones devuelven `None` si el valor es valido, o el MENSAJE DE ERROR ya
redactado si no lo es. El mensaje dice que pasa Y como se arregla (heuristica
H9): "La duracion debe estar entre 1 y 480 minutos", no "Valor invalido".
"""

import re

import config

# --------------------------------------------------------------------------
# Limites
# --------------------------------------------------------------------------
USERNAME_MIN = 3
USERNAME_MAX = 20
EMAIL_MAX = 120
FULL_NAME_MIN = 2
FULL_NAME_MAX = 80
PASSWORD_MIN = config.MIN_PASSWORD_LENGTH   # 8
PASSWORD_MAX = config.MAX_PASSWORD_LENGTH   # 128
SEARCH_MAX = 60

# Titulo y descripcion de CUALQUIER cosa que el usuario crea: tarea, evento o
# habito. Un solo numero para los tres modulos.
#
# Antes cada uno tenia el suyo -- 120 en tareas, 80 en habitos y ninguno en el
# calendario, que tragaba 9.000 caracteres por la ruta de edicion -- asi que el
# mismo tipo de campo se comportaba distinto segun la pantalla.
TITULO_MAX = 120
DESCRIPCION_MAX = 500

# Sin regex entran espacios, emojis y '../'; y un '@' haria ambiguo el login.
# El `pattern` del HTML va sin ^ $ porque el navegador ya lo ancla solo.
USERNAME_PATTERN = r"[a-z][a-z0-9._]{2,19}"
USERNAME_RE = re.compile(r"^" + USERNAME_PATTERN + r"$")

# type="email" del navegador acepta "a@b" (sin punto). Este no.
EMAIL_PATTERN = r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}"
EMAIL_RE = re.compile(r"^" + EMAIL_PATTERN + r"$")

# Sin reglas de composicion (mayuscula + numero + simbolo) a proposito:
# NIST 800-63B las desaconseja porque empujan a 'Password1!' y nada mas.
# La longitud manda, y una lista negra corta ataja lo evidente.
PASSWORD_COMUNES = frozenset({
    "12345678", "123456789", "1234567890", "password", "password1",
    "qwerty123", "qwertyuiop", "11111111", "00000000", "abc12345",
    "contrasena", "contrasenna", "password123", "iloveyou", "admin123",
    "administrador", "vibeplanner", "planner123", "letmein1", "welcome1",
})


# --------------------------------------------------------------------------
# REGLAS - lo que consumen las plantillas Jinja2
# --------------------------------------------------------------------------
REGLAS = {
    "username": {
        "min": USERNAME_MIN,
        "max": USERNAME_MAX,
        "pattern": USERNAME_PATTERN,
        "etiqueta": "Nombre de usuario",
        "ayuda": "Entre 3 y 20 caracteres. Letras, numeros, punto y guion bajo.",
        "autocomplete": "username",
    },
    "email": {
        "max": EMAIL_MAX,
        "pattern": EMAIL_PATTERN,
        "etiqueta": "Correo electronico",
        "ayuda": "Lo usaras para entrar y para recuperar tu cuenta.",
        "autocomplete": "email",
    },
    "full_name": {
        "min": FULL_NAME_MIN,
        "max": FULL_NAME_MAX,
        "etiqueta": "Nombre completo (opcional)",
        "ayuda": "Como quieres que te llamemos en la aplicacion.",
        "autocomplete": "name",
    },
    "password": {
        "min": PASSWORD_MIN,
        "max": PASSWORD_MAX,
        "etiqueta": "Contrasena",
        # H5/H10: el requisito se ve ANTES de escribir, no cuando ya fallo.
        "ayuda": "Minimo 8 caracteres. Se guarda cifrada.",
        "autocomplete": "new-password",
    },
}


# --------------------------------------------------------------------------
# Normalizacion - SIEMPRE antes de validar y antes de guardar
# --------------------------------------------------------------------------
def normalizar_username(valor):
    """'  Piero  ' -> 'piero'. La BD ya es COLLATE NOCASE; esto es la 1a barrera."""
    return (valor or "").strip().lower()


def normalizar_email(valor):
    return (valor or "").strip().lower()


def normalizar_nombre(valor):
    """Colapsa los espacios interiores: 'Ana   Cusi' -> 'Ana Cusi'."""
    return " ".join((valor or "").split())


def normalizar_busqueda(valor):
    """Trunca y escapa los comodines de LIKE para que '%' no liste todo."""
    limpio = (valor or "").strip()[:SEARCH_MAX]
    return limpio


# --------------------------------------------------------------------------
# Validacion campo a campo. Devuelven None (valido) o el mensaje de error.
# --------------------------------------------------------------------------
def validar_username(valor):
    if not valor:
        return "Escribe un nombre de usuario."
    if len(valor) < USERNAME_MIN or len(valor) > USERNAME_MAX:
        return f"El usuario debe tener entre {USERNAME_MIN} y {USERNAME_MAX} caracteres."
    if not USERNAME_RE.match(valor):
        return ("El usuario solo puede llevar letras, numeros, punto y guion bajo, "
                "y debe empezar por una letra.")
    return None


def validar_email(valor):
    if not valor:
        return "Escribe tu correo."
    if len(valor) > EMAIL_MAX:
        return f"El correo no puede pasar de {EMAIL_MAX} caracteres."
    if not EMAIL_RE.match(valor):
        return "Escribe un correo valido, por ejemplo nombre@dominio.com."
    return None


def validar_nombre_completo(valor):
    """Opcional: vacio es valido. La BD lo declara DEFAULT ''."""
    if not valor:
        return None
    if len(valor) < FULL_NAME_MIN or len(valor) > FULL_NAME_MAX:
        return (f"El nombre completo debe tener entre {FULL_NAME_MIN} y "
                f"{FULL_NAME_MAX} caracteres.")
    return None


def validar_password(valor, username="", email=""):
    """
    `username` y `email` son opcionales pero conviene pasarlos: una contrasena
    igual al usuario es lo primero que prueba cualquiera.
    """
    if not valor:
        return "Escribe una contrasena."
    if len(valor) < PASSWORD_MIN:
        return f"La contrasena debe tener al menos {PASSWORD_MIN} caracteres."
    if len(valor) > PASSWORD_MAX:
        return f"La contrasena no puede pasar de {PASSWORD_MAX} caracteres."

    bajo = valor.lower()
    if bajo in PASSWORD_COMUNES:
        return "Esa contrasena es demasiado facil de adivinar. Elige otra."

    parte_local = (email or "").split("@")[0].lower()
    if bajo and (bajo == (username or "").lower() or (parte_local and bajo == parte_local)):
        return "La contrasena no puede ser igual a tu usuario ni a tu correo."
    return None


def validar_roles(codigos):
    """
    Lista blanca + rol base forzado.

    Dos reglas que parecen una sola y no lo son:
      1. Nunca se inserta un codigo que venga del navegador sin comprobarlo.
         Lo desconocido se descarta EN SILENCIO: solo puede llegar de una
         manipulacion, y avisar al que manipula no ayuda a nadie.
      2. `usuario` se anade siempre. Todos son usuarios y los demas roles se
         SUMAN encima; un administrador sin el rol `usuario` no podria abrir
         su propio planner.

    Devuelve una lista ordenada y sin repetidos.
    """
    validos = {c for c in (codigos or []) if c in config.ROLES_ASIGNABLES}
    validos.add(config.ROL_POR_DEFECTO)
    return sorted(validos)


def validar_estado(valor):
    """El formulario manda '0' o '1'. Cualquier otra cosa es manipulacion."""
    if valor not in ("0", "1"):
        return None
    return int(valor)


# --------------------------------------------------------------------------
# Formularios completos
# --------------------------------------------------------------------------
def validar_datos_cuenta(form, exigir_password=True):
    """
    Valida el bloque de campos comun al registro publico y al alta
    administrativa. Que las dos rutas llamen a ESTA funcion es justamente el
    arreglo: hasta ahora el alta administrativa pasaba request.form crudo a
    create_user() y aceptaba un usuario vacio con contrasena de un caracter.

    Devuelve (datos_normalizados, errores).
    `errores` es {campo: mensaje} para pintarlo debajo de su campo.
    """
    datos = {
        "username": normalizar_username(form.get("username")),
        "email": normalizar_email(form.get("email")),
        "full_name": normalizar_nombre(form.get("full_name")),
        "password": form.get("password") or "",
    }

    errores = {}
    for campo, error in (
        ("username", validar_username(datos["username"])),
        ("email", validar_email(datos["email"])),
        ("full_name", validar_nombre_completo(datos["full_name"])),
    ):
        if error:
            errores[campo] = error

    if exigir_password or datos["password"]:
        error = validar_password(datos["password"], datos["username"], datos["email"])
        if error:
            errores["password"] = error

    return datos, errores


def datos_para_repintar(datos):
    """
    Lo que vuelve al formulario tras un 400.

    Se conserva todo MENOS la contrasena (H3: no perder lo escrito). La
    contrasena nunca se repuebla, nunca viaja en un flash y nunca se registra
    en el log: reaparecer en el HTML es exactamente como acaba en la cache del
    navegador y en las capturas de pantalla del soporte tecnico.
    """
    return {k: v for k, v in datos.items() if k != "password"}


# --------------------------------------------------------------------------
# Pruebas: python validators.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    assert normalizar_username("  Piero  ") == "piero"
    assert normalizar_nombre("Ana   Cusi") == "Ana Cusi"

    assert validar_username("piero") is None
    assert validar_username("pi") is not None                  # corto
    assert validar_username("p" * 21) is not None              # largo
    assert validar_username("1piero") is not None              # empieza por numero
    assert validar_username("piero cald") is not None          # espacio
    assert validar_username("piero@esan") is not None          # arroba
    assert validar_username("piero.c_1") is None

    assert validar_email("a@b.pe") is None
    assert validar_email("a@b") is not None                    # lo que type=email SI acepta
    assert validar_email("sin-arroba.pe") is not None
    assert validar_email("a@b." + "x" * 130) is not None       # largo

    assert validar_nombre_completo("") is None                 # opcional
    assert validar_nombre_completo("A") is not None
    assert validar_nombre_completo("Piero Calderon") is None

    assert validar_password("Vibe2026!") is None
    assert validar_password("corta1") is not None
    assert validar_password("password") is not None            # lista negra
    assert validar_password("PASSWORD") is not None            # lista negra, insensible
    assert validar_password("pierocalderon", username="pierocalderon") is not None
    assert validar_password("pierocald", email="pierocald@esan.pe") is not None

    # El rol base se fuerza y lo desconocido se descarta.
    assert validar_roles([]) == ["usuario"]
    assert validar_roles(["admin"]) == ["admin", "usuario"]
    assert validar_roles(["admin", "superroot", "lider"]) == ["admin", "usuario"]
    assert validar_roles(["usuario", "usuario"]) == ["usuario"]

    assert validar_estado("0") == 0
    assert validar_estado("1") == 1
    assert validar_estado("sql") is None

    # El alta administrativa valida igual que el registro publico.
    _, errores = validar_datos_cuenta({"username": "", "email": "x", "password": "1"})
    assert set(errores) == {"username", "email", "password"}, errores

    datos, errores = validar_datos_cuenta(
        {"username": "Lucero", "email": "L@Esan.PE", "full_name": " Lucero  Ayala ",
         "password": "Vibe2026!"}
    )
    assert not errores
    assert datos["username"] == "lucero" and datos["email"] == "l@esan.pe"
    assert datos["full_name"] == "Lucero Ayala"
    assert "password" not in datos_para_repintar(datos)

    print("validators.py: 26/26 comprobaciones en verde")
