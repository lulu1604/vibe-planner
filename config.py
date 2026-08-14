"""
VibePlanner v2 - Configuracion (config.py)
------------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

Constantes del servidor. Nada de esto sale de un formulario: si un valor se
puede cambiar desde el navegador, no es configuracion, es entrada de usuario.
"""

import os

# --------------------------------------------------------------------------
# Sesion y secretos
# --------------------------------------------------------------------------
# El SECRET_KEY real se configura SOLO como variable de entorno en el panel de
# PythonAnywhere. Lo que entra al historial de Git es publico para siempre,
# aunque despues se borre (riesgo R10 de Inception).
SECRET_KEY = os.environ.get("VIBEPLANNER_SECRET", "dev-only-no-usar-en-produccion")

SESSION_COOKIE_HTTPONLY = True   # JavaScript no puede leer la cookie de sesion
SESSION_COOKIE_SAMESITE = "Lax"  # el navegador no la manda en peticiones de otro sitio

# La cookie de sesion NO viaja por http. Es una credencial completa: quien la
# copia entra al panel de administracion sin contrasena.
#
# Condicionado a VIBEPLANNER_SECRET y no fijado a True porque True a secas
# rompe en SILENCIO todo el desarrollo local: sobre http://127.0.0.1:5000 el
# navegador aceptaria la cookie pero no la devolveria, asi que nadie podria
# iniciar sesion y el sintoma seria "el login no hace nada".
#
# La variable solo existe en produccion (panel de PythonAnywhere), asi que la
# proteccion se enciende exactamente donde hay HTTPS. Va de la mano con activar
# "Force HTTPS" en el panel: sin las dos, la primera peticion sale en claro.
SESSION_COOKIE_SECURE = bool(os.environ.get("VIBEPLANNER_SECRET"))

# --------------------------------------------------------------------------
# Contrasenas
# --------------------------------------------------------------------------
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Werkzeug 3.x usa scrypt por defecto: ~32 MiB de RAM por hash. PythonAnywhere
# free tier va justo de memoria y la suite de pruebas hace decenas de hashes.
# pbkdf2 con 600.000 iteraciones sigue siendo la recomendacion de OWASP 2023.
PASSWORD_HASH_METHOD = "pbkdf2:sha256:600000"

# --------------------------------------------------------------------------
# Roles y paginacion
# --------------------------------------------------------------------------
# Alcance v2.1: solo dos roles. El rol `lider` esta en BACKLOG_v3.md.
# Anadirlo manana es una entrada mas en seed.py, no un refactor.
ROL_POR_DEFECTO = "usuario"
ROLES_ASIGNABLES = ("usuario", "admin")

# H2 de REVISION_BD_ESCALABILIDAD.md: ninguna consulta sin acotar.
USUARIOS_POR_PAGINA = 50

# --------------------------------------------------------------------------
# Heredado de la v1 (no tocar: lo usa app.py)
# --------------------------------------------------------------------------
DEFAULT_AVAILABLE_MINUTES = 120
