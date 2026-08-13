# Contenido de referencia para el archivo WSGI de PythonAnywhere.
# NO se usa en local. Se copia y pega en el editor WSGI de PythonAnywhere
# (Web -> "WSGI configuration file"), reemplazando TODO lo que venga por defecto.
#
# Reemplazar TUUSUARIO por el usuario de PythonAnywhere (no el de GitHub).
#
# Requisitos del lado de PythonAnywhere:
#   - Web app creada con "Manual configuration" (NO el asistente de Flask).
#   - Virtualenv apuntando a /home/TUUSUARIO/.virtualenvs/vibeplanner
#   - Source code y Working directory en /home/TUUSUARIO/vibe-planner
#
# `database.init_db()` corre al importar app.py, así que vibe_planner.db se
# crea solo la primera vez. No hay que subir la base de datos al repo.

import os
import sys

path = '/home/TUUSUARIO/vibe-planner'
if path not in sys.path:
    sys.path.insert(0, path)

# Opcional pero recomendado: clave de sesión propia en producción.
# Sin esto, app.py usa la clave por defecto del repositorio.
os.environ.setdefault('VIBEPLANNER_SECRET', 'cambia-esto-por-una-cadena-larga')

from app import app as application   # noqa: E402
