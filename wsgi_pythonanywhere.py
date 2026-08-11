# Contenido de referencia para el archivo WSGI de PythonAnywhere.
# NO se usa en local. Se copia y pega en el editor WSGI de PythonAnywhere.
# Reemplazar TUUSUARIO por el usuario de PythonAnywhere (no el de GitHub).

import sys

path = '/home/TUUSUARIO/vibe-planner'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application   # noqa: E402
