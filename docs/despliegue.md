# 🚀 Despliegue en PythonAnywhere — VibePlanner

**Responsable:** Ana Cusi (rutas Flask + despliegue)
**Curso:** Fundamentals of Vibe Coding — ESAN Global Week 2026

> **Estado: desplegado.** La aplicación está en línea en **https://ana1604.pythonanywhere.com**
> Este documento registra los pasos que se siguieron, para poder repetirlos o depurarlos.
> El usuario de PythonAnywhere es `Ana1604` (distinto del usuario de GitHub, que es `lulu1604`).

---

## Antes de empezar

Verifica en local que las tres suites de asserts pasan:

```bat
python scoring.py     ->  6 asserts  (Lucero)
python database.py    ->  4 asserts  (Jose)
python app.py test    -> 11 asserts  (Ana)
```

**No despliegues si alguna falla.** El plan de Inception ya advirtió que el tier gratuito no tiene entorno de staging: todo lo que se despliega se prueba directo en producción.

---

## 1. Traer el código desde GitHub

En PythonAnywhere: **Consoles → Bash**

```bash
git clone https://github.com/lulu1604/vibe-planner.git
ls vibe-planner
```

Deberías ver `app.py`, `database.py`, `scoring.py`, `requirements.txt`, `templates/`, `static/`.

> Para actualizar más adelante: `cd ~/vibe-planner && git pull`

---

## 2. Crear el entorno virtual (Linux, no el de Windows)

```bash
python3.10 -m venv ~/.virtualenvs/vibeplanner
source ~/.virtualenvs/vibeplanner/bin/activate
pip install -r ~/vibe-planner/requirements.txt
```

El `venv` de Windows **no se sube ni se copia**: PythonAnywhere necesita el suyo, compilado para Linux.

---

## 3. Crear la aplicación web

**Web → Add a new web app**

| Paso | Elegir |
|---|---|
| Dominio | `Ana1604.pythonanywhere.com` |
| Framework | **Manual configuration** ⚠️ no elijas "Flask" |
| Versión de Python | La misma del venv (3.10) |

> ⚠️ Si eliges el asistente de Flask, PythonAnywhere genera su propio `app.py` y **sobrescribe el nuestro**. Tiene que ser *Manual configuration*.

---

## 4. Configurar las rutas

En la página **Web**, sección **Code**:

| Campo | Valor |
|---|---|
| Source code | `/home/Ana1604/vibe-planner` |
| Working directory | `/home/Ana1604/vibe-planner` |
| Virtualenv | `/home/Ana1604/.virtualenvs/vibeplanner` |

---

## 5. Editar el archivo WSGI

> ⚠️ **El error que nos costó más tiempo.** Hay dos archivos con nombre parecido y solo uno cuenta:
>
> | Archivo | Dónde vive | ¿Lo lee PythonAnywhere? |
> |---|---|---|
> | `wsgi_pythonanywhere.py` | En el repo / tu PC | ❌ **Nunca.** Es solo una referencia |
> | `/var/www/ana1604_pythonanywhere_com_wsgi.py` | En el servidor | ✅ **Este es el que manda** |
>
> Editamos el del repo y recargamos varias veces sin entender por qué seguía
> apareciendo un proyecto anterior. El servidor nunca vio ese archivo.

Clic en el enlace **WSGI configuration file** (abre el editor de PythonAnywhere, no el tuyo). Borra **todo** el contenido y pega esto:

```python
import os
import sys

path = '/home/Ana1604/vibe-planner'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('VIBEPLANNER_SECRET', 'cambia-esto-por-una-cadena-larga')

from app import app as application
```

La última línea funciona porque en `app.py` la instancia se llama **exactamente `app`** a nivel de módulo. Esa es la regla que no se rompe del `reparto.md`.

---

## 6. Reload y probar

Botón verde **Reload** → abrir `https://Ana1604.pythonanywhere.com`

Checklist de las 4 historias sobre el entorno desplegado:

- [ ] **US1** — Agregar una actividad; aparece en la lista. Eliminarla; desaparece.
- [ ] **US2** — Con 3 actividades de distinta prioridad y fecha, el orden es el esperado.
- [ ] **US3** — Cambiar estado a "Completada"; el porcentaje de avance sube.
- [ ] **US4** — Clic en "Por qué"; el modal muestra las 3 componentes y suman el total de la insignia.
- [ ] **Validación** — Intentar guardar con título vacío o 0 minutos; no se inserta y sale el mensaje de error.
- [ ] **Persistencia** — Reload de la web app; los datos siguen ahí.

---

## 7. Publicar el enlace

Agregar al `README.md`:

```markdown
🔗 **App desplegada:** https://Ana1604.pythonanywhere.com
```

---

## Si algo falla

**Web → Error log** (siempre primero). Los errores más comunes:

| Síntoma en el log | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | El virtualenv no está configurado o está vacío | Revisar el campo Virtualenv y reinstalar `requirements.txt` |
| `ModuleNotFoundError: No module named 'app'` | La ruta del WSGI está mal | Verificar que `path` apunte a la carpeta que contiene `app.py` |
| `ImportError: cannot import name 'app'` | Se renombró la instancia de Flask | En `app.py` debe existir `app = Flask(__name__)` a nivel de módulo |
| `ZoneInfoNotFoundError: 'America/Lima'` | Falta `tzdata` | `pip install tzdata` dentro del virtualenv |
| `sqlite3.OperationalError: unable to open database file` | Permisos o ruta relativa | `database.py` ya usa ruta absoluta; revisar el Working directory |
| Sale la página por defecto de PythonAnywhere | No se hizo Reload | Botón verde **Reload** |

**Después de cada cambio hay que dar Reload.** No basta con `git pull`.

---

## Nota sobre la cuenta gratuita

- La web app **expira cada 3 meses**; se renueva con un clic desde el dashboard.
- No hay red saliente hacia dominios fuera de la lista blanca. Por eso el proyecto no usa CDN ni APIs externas — decisión ya tomada en Inception (Riesgo #1).
