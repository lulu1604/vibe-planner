# 🚀 Despliegue en PythonAnywhere — VibePlanner

**Responsable:** Ana Cusi (design system + despliegue)
**Curso:** Fundamentals of Vibe Coding — ESAN Global Week 2026

> **Actualizado para la v2.** La v1 ya estuvo en línea en **https://ana1604.pythonanywhere.com**.
> El usuario de PythonAnywhere es `Ana1604` (distinto del de GitHub, que es `lulu1604`).
>
> 🔴 **Lo que cambia respecto a la v1 son dos pasos, y saltarse cualquiera deja la
> aplicación inservible:**
>
> | Paso nuevo | Si te lo saltas |
> |---|---|
> | **5. Variables de entorno** | Las sesiones se firman con la clave por defecto, que está en el repositorio: cualquiera puede falsificar una sesión |
> | **6. `python seed.py`** | La base queda **sin permisos, sin roles y sin administrador**. Nadie puede entrar a nada y *todas* las páginas responden 403. Parece un fallo de permisos y es un paso de despliegue que falta |

---

## Antes de empezar

Verifica en local que las **cuatro** suites pasan:

```bat
python app.py test    -> 11 asserts   (v1: rutas y validación)
python database.py    ->  4 asserts   (contrato de persistencia)
python validators.py  -> 26 asserts   (reglas de los formularios)
python test_v2.py     -> 33 asserts   (núcleo: cuentas, roles y permisos)
```

**No despliegues si alguna falla.** El plan de Inception ya advirtió que el tier
gratuito no tiene entorno de staging: todo lo que se despliega se prueba directo
en producción.

---

## 1. Traer el código desde GitHub

En PythonAnywhere: **Consoles → Bash**

```bash
git clone https://github.com/lulu1604/vibe-planner.git
ls vibe-planner
```

Deberías ver `app.py`, `security.py`, `seed.py`, `schema_v2.sql`, `requirements.txt`,
`templates/`, `static/`.

> Para actualizar más adelante: `cd ~/vibe-planner && git pull` — pero mira antes
> la sección **Redespliegue**, que tiene un paso más.

---

## 2. Crear el entorno virtual (Linux, no el de Windows)

```bash
python3.10 -m venv ~/.virtualenvs/vibeplanner
source ~/.virtualenvs/vibeplanner/bin/activate
pip install -r ~/vibe-planner/requirements.txt
```

El `venv` de Windows **no se sube ni se copia**: PythonAnywhere necesita el suyo,
compilado para Linux.

`requirements.txt` sigue teniendo una sola línea (`Flask==3.0.3`). Werkzeug, que
es lo que cifra las contraseñas, entra solo como dependencia de Flask.

---

## 3. Crear la aplicación web

**Web → Add a new web app**

| Paso | Elegir |
|---|---|
| Dominio | `Ana1604.pythonanywhere.com` |
| Framework | **Manual configuration** ⚠️ no elijas "Flask" |
| Versión de Python | La misma del venv (3.10) |

> ⚠️ Si eliges el asistente de Flask, PythonAnywhere genera su propio `app.py` y
> **sobrescribe el nuestro**. Tiene que ser *Manual configuration*.

---

## 4. Configurar las rutas

En la página **Web**, sección **Code**:

| Campo | Valor |
|---|---|
| Source code | `/home/Ana1604/vibe-planner` |
| Working directory | `/home/Ana1604/vibe-planner` |
| Virtualenv | `/home/Ana1604/.virtualenvs/vibeplanner` |

---

## 5. Variables de entorno 🆕

En la página **Web**, sección **Environment variables**. Son **cuatro**:

| Variable | Valor | Para qué |
|---|---|---|
| `VIBEPLANNER_SECRET` | una cadena larga y aleatoria | Firma las cookies de sesión |
| `VIBEPLANNER_ADMIN_USER` | p. ej. `admin` | Usuario del administrador inicial |
| `VIBEPLANNER_ADMIN_EMAIL` | un correo real del equipo | Correo del administrador inicial |
| `VIBEPLANNER_ADMIN_PASS` | una contraseña de verdad | Contraseña del administrador inicial |

Generar el secreto (en la consola Bash):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

> 🔴 **Nunca escribas estos valores en el repositorio.** Lo que entra al historial
> de Git es público para siempre, aunque después borres el archivo. Es el riesgo
> R10 de Inception.
>
> ⚠️ **Trampa que cuesta una tarde:** las variables del panel **Web** se las lleva
> el proceso de la aplicación, **no la consola Bash**. Como el paso 6 se ejecuta
> desde la consola, hay que exportarlas también ahí:
>
> ```bash
> export VIBEPLANNER_ADMIN_USER='admin'
> export VIBEPLANNER_ADMIN_EMAIL='vibeplanner@esan.pe'
> export VIBEPLANNER_ADMIN_PASS='la-que-pusiste-en-el-panel'
> ```
>
> Sin esto, `seed.py` crea el administrador con los valores por defecto y la
> contraseña queda siendo la que está escrita en el repositorio.

---

## 6. Sembrar la base de datos 🆕

```bash
cd ~/vibe-planner
source ~/.virtualenvs/vibeplanner/bin/activate
python seed.py
```

Tiene que imprimir:

```
  23 permisos sembrados
  2 roles sembrados (usuario, admin)
  administrador 'admin' creado (id 1)
  permisos efectivos del administrador: 23 (union de sus dos roles)
```

Si sale el aviso *"se uso la contrasena por defecto del administrador"*, es que las
variables del paso 5 no llegaron a la consola. Vuelve al `export` de arriba, borra
`vibe_planner.db` y siembra otra vez.

> **`seed.py` es idempotente**: se puede ejecutar mil veces. Si el administrador ya
> existe, no lo toca.

Reglas de la base de datos:
- `vibe_planner.db` vive en la raíz del proyecto, **fuera de `/static`**. Un fichero
  SQLite servido por HTTP entrega todos los hashes de contraseña de golpe.
- Está en `.gitignore`. Nunca se sube ni se descarga.
- El esquema se crea solo al importar `app.py`; lo que **no** se crea solo son los
  permisos, los roles y el administrador. Para eso es este paso.

---

## 7. Editar el archivo WSGI

> ⚠️ **El error que nos costó más tiempo.** Hay dos archivos con nombre parecido y
> solo uno cuenta:
>
> | Archivo | Dónde vive | ¿Lo lee PythonAnywhere? |
> |---|---|---|
> | `wsgi_pythonanywhere.py` | En el repo / tu PC | ❌ **Nunca.** Es solo una referencia |
> | `/var/www/ana1604_pythonanywhere_com_wsgi.py` | En el servidor | ✅ **Este es el que manda** |
>
> Editamos el del repo y recargamos varias veces sin entender por qué seguía
> apareciendo un proyecto anterior. El servidor nunca vio ese archivo.

Clic en el enlace **WSGI configuration file** (abre el editor de PythonAnywhere).
Borra **todo** el contenido y pega esto:

```python
import sys

path = '/home/Ana1604/vibe-planner'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

Dos cosas de aquí:

- La última línea funciona porque en `app.py` la instancia se llama **exactamente
  `app`** a nivel de módulo, sin application factory. Es la regla nº 1 del proyecto.
- **Ya no se pone ningún `os.environ.setdefault('VIBEPLANNER_SECRET', ...)`.** En la
  v1 estaba, con una cadena de ejemplo, y eso era un secreto escrito en un archivo
  que se comparte. Las variables se configuran en el panel del paso 5, y solo ahí.

---

## 8. Reload y probar

Botón verde **Reload** → abrir `https://Ana1604.pythonanywhere.com`

**Primero lo que bloquea el release** — si esto falla, no se despliega:

```bash
# TC-03: escalada de privilegios en el registro
curl -X POST https://ana1604.pythonanywhere.com/register \
  -d "username=atacante&email=atacante@esan.pe&password=Hack2026!&role=admin&roles=admin"
```

Entra como administrador a **Gestión de usuarios** y comprueba que `atacante`
aparece con **una sola insignia: Usuario**. Si sale Administrador, hay un agujero
de seguridad y el release se detiene. Borra esa cuenta de prueba después.

**Checklist funcional sobre el entorno desplegado:**

- [ ] **Registro** — me registro con una cuenta nueva y entro directo
- [ ] **Login/logout** — salgo y vuelvo a entrar
- [ ] **Login fallido** — usuario inexistente y contraseña mala dan **el mismo** mensaje
- [ ] **Menú de cuenta** — arriba a la derecha, con Mi perfil y Cerrar sesión
- [ ] **Administración** — como `admin` veo "Gestión de usuarios"; como usuario normal, no
- [ ] **403 real** — un usuario normal que escriba `/admin/usuarios` a mano recibe 403
- [ ] **Alta** — creo una cuenta marcando Usuario + Administrador; salen las dos insignias
- [ ] **Mantenimiento** — "Gestionar" abre el detalle; edito nombre y correo
- [ ] **Roles** — quito el rol admin a esa cuenta; en su siguiente recarga pierde el acceso **sin cerrar sesión**
- [ ] **Sin admins** — intento quitarme el rol admin siendo el único → lo impide
- [ ] **Desactivar** — desactivo una cuenta; no entra, y al reactivarla conserva sus datos
- [ ] **US1–US4** — el planner sigue funcionando: agregar, ordenar, cambiar estado y el modal "¿Por qué este orden?"
- [ ] **Responsive** — a 360 px la tabla de usuarios se ve como tarjetas
- [ ] **Persistencia** — Reload de la web app; los datos siguen ahí

---

## 9. Publicar el enlace

Agregar al `README.md`:

```markdown
🔗 **App desplegada:** https://Ana1604.pythonanywhere.com
```

---

## Redespliegue (cada vez que se sube algo nuevo) 🆕

```bash
cd ~/vibe-planner && git pull origin main
source ~/.virtualenvs/vibeplanner/bin/activate
pip install -r requirements.txt
python seed.py            # <-- NO te lo saltes
```

Y después el botón verde **Reload**.

`python seed.py` va aquí porque **cada módulo nuevo trae permisos nuevos**. Un
permiso que se usa en el código pero no está en la tabla es un 403 permanente que
nadie sabrá explicar. Como es idempotente, ejecutarlo de más nunca hace daño.

**Después de cada cambio hay que dar Reload.** No basta con `git pull`.

---

## Si algo falla

**Web → Error log** (siempre primero). Los errores más comunes:

| Síntoma | Causa | Solución |
|---|---|---|
| **Todo responde 403, incluso al administrador** | 🆕 No se ejecutó `seed.py`: no hay permisos ni roles en la tabla | Paso 6 |
| **No puedo entrar con el administrador** | 🆕 `seed.py` se ejecutó sin las variables exportadas en la consola | Paso 5, el bloque `export`, luego borrar `vibe_planner.db` y sembrar otra vez |
| **La sesión se cierra sola al recargar** | 🆕 Falta `VIBEPLANNER_SECRET`: cada worker firma con una clave distinta | Paso 5 |
| `jinja2.exceptions.UndefinedError: 'current_user' is undefined` | 🆕 `app.py` no llegó completo: falta el `git pull` | `git pull origin main` y Reload |
| `ModuleNotFoundError: No module named 'flask'` | El virtualenv no está configurado o está vacío | Revisar el campo Virtualenv y reinstalar `requirements.txt` |
| `ModuleNotFoundError: No module named 'app'` | La ruta del WSGI está mal | Verificar que `path` apunte a la carpeta que contiene `app.py` |
| `ImportError: cannot import name 'app'` | Se renombró la instancia de Flask | En `app.py` debe existir `app = Flask(__name__)` a nivel de módulo |
| `ZoneInfoNotFoundError: 'America/Lima'` | Falta `tzdata` | `pip install tzdata` dentro del virtualenv |
| `sqlite3.OperationalError: unable to open database file` | Permisos o ruta relativa | `database.py` ya usa ruta absoluta; revisar el Working directory |
| `database is locked` | 🆕 El modo WAL sobre el almacenamiento de red de PythonAnywhere | Plan B documentado: cambiar `journal_mode = WAL` por `DELETE` en `database.py` |
| Sale la página por defecto de PythonAnywhere | No se hizo Reload | Botón verde **Reload** |

---

## Nota sobre la cuenta gratuita

- La web app **expira cada 3 meses**; se renueva con un clic desde el dashboard.
- No hay red saliente hacia dominios fuera de la lista blanca. Por eso el proyecto
  no usa CDN ni APIs externas, y las fuentes van auto-alojadas en `static/fonts/`
  — decisión ya tomada en Inception (Riesgo #1).
- **Tampoco hay SMTP.** Por eso no existe "recuperar contraseña por correo": el
  administrador la restablece desde el panel de gestión de usuarios.
- Activa **Force HTTPS** en la pestaña Web. Sin eso, la cookie de sesión viaja en
  claro — lo dejó anotado el informe de seguridad de la v1.
