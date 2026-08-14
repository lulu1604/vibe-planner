# Contenido de referencia para el archivo WSGI de PythonAnywhere.
# NO se usa en local, y PythonAnywhere TAMPOCO lee este archivo. Se copia y se
# pega en el editor WSGI del panel (Web -> "WSGI configuration file"),
# reemplazando TODO lo que venga por defecto. El que manda es el del servidor:
#   /var/www/TUUSUARIO_pythonanywhere_com_wsgi.py
#
# Reemplazar TUUSUARIO por el usuario de PythonAnywhere (no el de GitHub).
#
# --------------------------------------------------------------------------
# Requisitos del lado de PythonAnywhere
# --------------------------------------------------------------------------
#   - Web app creada con "Manual configuration" (NO el asistente de Flask, que
#     genera su propio app.py y sobrescribe el nuestro).
#   - Virtualenv en /home/TUUSUARIO/.virtualenvs/vibeplanner
#   - Source code y Working directory en /home/TUUSUARIO/vibe-planner
#
# --------------------------------------------------------------------------
# Variables de entorno - se configuran en el panel Web -> Environment variables
# NUNCA en este archivo: lo que entra al historial de Git es publico para
# siempre, aunque despues se borre.
# --------------------------------------------------------------------------
#   VIBEPLANNER_SECRET        firma las cookies de sesion. Con el valor por
#                             defecto, cualquiera puede falsificar una sesion.
#                             Generarla con:
#                               python3 -c "import secrets; print(secrets.token_urlsafe(48))"
#   VIBEPLANNER_ADMIN_USER    usuario del administrador inicial
#   VIBEPLANNER_ADMIN_EMAIL   correo del administrador inicial
#   VIBEPLANNER_ADMIN_PASS    su contrasena. Si se queda la de por defecto,
#                             la aplicacion queda abierta.
#
# --------------------------------------------------------------------------
# Antes del primer arranque: SEMBRAR
# --------------------------------------------------------------------------
# `database.init_db()` corre al importar app.py, asi que el ESQUEMA se crea
# solo. Los permisos, los roles y el administrador NO: eso lo hace `seed.py`,
# y hay que ejecutarlo A MANO una vez desde una consola Bash:
#
#     cd ~/vibe-planner
#     source ~/.virtualenvs/vibeplanner/bin/activate
#     export VIBEPLANNER_ADMIN_USER='admin'      # el panel Web no exporta a
#     export VIBEPLANNER_ADMIN_EMAIL='...'       # la consola: hay que repetirlo
#     export VIBEPLANNER_ADMIN_PASS='...'
#     python seed.py
#
# Sin ese paso la base queda vacia de permisos y TODAS las paginas responden
# 403, incluso al administrador. Parece un fallo de permisos y es un paso de
# despliegue que falta.
#
# `seed.py` es idempotente, pero NUNCA se llama al importar: sembrar es un acto
# manual y consciente, no algo que ocurra en cada reinicio del servidor.
#
# Guia completa paso a paso: docs/despliegue.md

import sys

path = '/home/TUUSUARIO/vibe-planner'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application   # noqa: E402
