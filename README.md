# VibePlanner

Planificador de actividades con priorizacion transparente y explicable.
Proyecto final - Fundamentals of Vibe Coding, ESAN Global Week 2026.

**Equipo:** Lucero Ayala - Jose Cabrera - Piero Calderon - Ana Cusi

🔗 **App desplegada:** https://ana1604.pythonanywhere.com
📦 **Repositorio:** https://github.com/lulu1604/vibe-planner

> **v2 — multiusuario.** La v1 era un planificador de un solo usuario, sin
> cuentas, cuyo diferenciador era el puntaje explicable. La v2 conserva ese motor
> **intacto** y lo convierte en una plataforma con cuentas y **roles agregativos**.
>
> La decision que gobierna toda la arquitectura: **el rol no es una categoria a la
> que perteneces, es una bolsa de permisos que cargas.** Un usuario puede llevar
> varios roles a la vez y sus permisos son la **union** de todos ellos. Por eso el
> administrador es tambien un usuario normal: planifica su dia y administra el
> sistema con la misma cuenta.
>
> Documentacion completa del update en [`docs/VUP_V2/`](docs/VUP_V2/) —
> empieza por [`00_INDICE.md`](docs/VUP_V2/00_INDICE.md).

---

## Estado del proyecto

| Modulo | Responsable | Estado |
|---|---|---|
| **A — Nucleo**: cuentas, roles y permisos | Piero | ✅ US5, US6, US7 cerradas |
| **B — Planner y Kanban** | Lucero | 🚧 v1 funcionando, v2 en progreso |
| **C — Calendario e invitaciones** | Jose | 🚧 Pendiente |
| **D — Habitos, metricas y design system** | Ana | 🚧 En progreso |
| Despliegue en PythonAnywhere | Ana | ✅ En linea |

Suites de pruebas — **las cuatro deben pasar antes de desplegar**:

```bash
python app.py test    # 11 asserts  rutas y validacion del planner
python database.py    #  4 asserts  contrato de persistencia
python validators.py  # 26 asserts  reglas de los formularios de cuentas
python test_v2.py     # 33 asserts  nucleo: cuentas, roles y permisos
python scoring.py     #  6 asserts  motor de puntuacion
```

---

## Como levantar el proyecto en tu maquina

```bash
git clone https://github.com/lulu1604/vibe-planner.git
cd vibe-planner

# 1. Crear TU entorno virtual (no se sube al repo)
python -m venv venv

# 2. Activarlo
#    Windows:
venv\Scripts\activate
#    macOS / Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Sembrar permisos, roles y el administrador   <-- NO te lo saltes
python seed.py

# 5. Correr
python app.py
```

Abre http://127.0.0.1:5000/login y entra con el administrador que acaba de crear
`seed.py` (por defecto `admin` / `CambiarEsto2026!`, y te avisa por consola de que
deberias cambiarla).

> 🔴 **Si te saltas `python seed.py`**, la base queda sin permisos, sin roles y sin
> administrador: no puedes entrar a nada y *todas* las paginas responden 403.
> Parece un fallo de permisos y es un paso de instalacion que falta.
>
> `seed.py` es idempotente: cada vez que alguien anade un permiso nuevo, se vuelve
> a ejecutar y queda sembrado sin duplicar nada.

### Variables de entorno

Ninguna hace falta en local — todas tienen un valor por defecto. **En produccion
las cuatro son obligatorias** y se configuran en el panel de PythonAnywhere, nunca
en el repositorio:

| Variable | Por defecto | Para que |
|---|---|---|
| `VIBEPLANNER_SECRET` | clave de desarrollo | Firma las cookies de sesion |
| `VIBEPLANNER_ADMIN_USER` | `admin` | Usuario del administrador inicial |
| `VIBEPLANNER_ADMIN_EMAIL` | `admin@vibeplanner.local` | Su correo |
| `VIBEPLANNER_ADMIN_PASS` | `CambiarEsto2026!` | Su contrasena |

---

## Reglas que NO se rompen

1. La instancia de Flask se llama **exactamente `app`** a nivel de modulo en
   `app.py`. PythonAnywhere hace `from app import app`. Sin application factory.
2. **Toda** consulta que devuelva datos de un usuario lleva `user_id` **dentro del
   `WHERE`**. Filtrar en Python despues no cuenta.
3. Los decoradores comprueban **permisos**, nunca nombres de rol. Nada de
   `@admin_required`: eso vuelve a meter el rol dentro del codigo y anula la tabla.
4. El `user_id` sale **siempre** de la sesion, jamas del formulario.
5. Los permisos se cachean en `flask.g` (dura una peticion), **jamas en la sesion**.
   Si vivieran en la cookie, quitarle un rol a alguien no tendria efecto hasta que
   cerrara sesion.
6. `PRAGMA foreign_keys = ON` en **cada** conexion. No es persistente, y sin el
   SQLite ignora las claves foraneas en silencio.
7. Todo POST lleva token CSRF. La lista de exenciones de `security.py` esta vacia y
   asi debe quedarse.
8. El `SECRET_KEY` de produccion **no entra al repositorio**, solo a las variables
   de entorno del servidor.
9. Todo permiso nuevo se declara en `seed.py`. Un permiso usado en un decorador
   pero no sembrado es un 403 permanente que nadie sabra explicar.
10. `vibe_planner.db` **nunca** se sube al repo (ya esta en `.gitignore`).
11. Sin APIs externas, sin CDN, sin gunicorn. Solo Flask y libreria estandar:
    `requirements.txt` tiene una sola linea.
12. Toda la logica de puntuacion vive **solo** en `scoring.py`.
13. La ruta de la base de datos es **absoluta**, calculada desde `__file__`.

---

## Contratos congelados

Si necesitas cambiar una de estas firmas, avisa al grupo **antes** de hacerlo.

### Nucleo — `security.py` (hito H2)

Lo que importan los modulos B, C y D:

```python
current_user()              -> dict | None
current_user_id()           -> int  | None
current_roles()             -> list[dict]     # solo para PINTAR, no para decidir
effective_permissions()     -> set[str]
has_permission("codigo")    -> bool
csrf_token()                -> str            # para las plantillas
@login_required
@requires("permiso.codigo")
```

Uso en una ruta — hacen falta **las dos llaves**:

```python
@planner.route("/mis-cosas")
@requires("planner.ver")          # llave 1: el permiso
def mis_cosas():
    user_id = current_user_id()   # llave 2: el filtro que va DENTRO del WHERE
```

Y en las plantillas, `{% if has_permission('usuario.listar') %}` es **cortesia
visual**: oculta el boton, no protege la ruta. La ruta la protege `@requires`.

### v1 — `scoring.py` y `database.py`

```python
# scoring.py
calculate_score(task: dict, available_minutes: int) -> tuple[int, dict]
rank_tasks(tasks: list[dict], available_minutes: int) -> list[dict]

# database.py
get_tasks(filter_status=None) -> list[dict]
get_task_by_id(task_id) -> dict | None
add_task(task_data: dict) -> bool
update_status(task_id, new_status) -> bool
delete_task(task_id) -> bool
get_daily_progress() -> dict  # claves: total, completed, percent
```

Forma exacta del `breakdown`:

```json
{
  "prioridad": {"puntos": 50, "razon": "Prioridad Alta"},
  "urgencia":  {"puntos": 40, "razon": "Vence hoy"},
  "tiempo":    {"puntos": 15, "razon": "Entra en tus 120 min disponibles"}
}
```

---

## Reparto por modulo (v2)

| Integrante | Modulo | Archivos |
|---|---|---|
| **Piero** | **A — Nucleo**: cuentas, roles, permisos | `security.py`, `auth.py`, `admin.py`, `perfil.py`, `home.py`, `repo_users.py`, `validators.py`, `seed.py`, `schema_v2.sql`, `config.py`, `app.py` |
| **Lucero** | **B — Planner y Kanban** | `scoring.py`, `repo_tasks.py`, `planner.py` |
| **Jose** | **C — Calendario** *(+ dueno unico del esquema SQL)* | `database.py`, `repo_events.py`, `calendar_bp.py` |
| **Ana** | **D — Habitos, metricas y design system** | `repo_habits.py`, `metrics.py`, `habits.py`, `static/css/`, `templates/components/`, despliegue |

> El reparto de la v1 decia "Piero → rutas, Ana → frontend". En la v2 se invirtio a
> peticion de ambos: **Piero = backend/nucleo, Ana = design system y despliegue**.
> Ver `docs/VUP_V2/00_INDICE.md`.

---

## Estructura

Raiz plana a proposito: PythonAnywhere hace `from app import app`, y un paquete
`src/` obligaria a un shim y a que los cuatro cambien sus imports.

```
app.py            crea `app`, registra blueprints, manejadores 400/403/404
config.py         SECRET_KEY y constantes
security.py       la guardia: @requires, current_user, CSRF   <- contrato H2
validators.py     reglas y mensajes de los formularios (fuente unica)
repo_users.py     unico modulo que toca users/roles/permissions
auth.py           /register /login /logout
admin.py          /admin/usuarios  (listado, alta, detalle, roles, estado, clave)
perfil.py         /perfil
home.py           /inicio  con el menu filtrado por permisos
seed.py           24 permisos, 2 roles y el administrador inicial
schema_v2.sql     esquema de identidad (5 tablas)
database.py       conexion por peticion + PRAGMAs
scoring.py        motor de puntuacion (sin cambios desde la v1)

templates/  base.html (shell) - auth/ - admin/ - perfil/ - errors/ - components/
static/     css/ (tokens -> base -> components) - js/ - fonts/
docs/       VUP_V2/ (el update) - vup_deliverables/ (la v1 entregada) - prompts/
```

---

## Flujo Git

```bash
git switch -c feature/tu-modulo
# ... trabajas ...
python app.py test && python database.py && python validators.py && python test_v2.py
git add .
git commit -m "descripcion clara"
git push -u origin feature/tu-modulo
# luego Pull Request en GitHub
```

**Merge a `main` todos los dias**, aunque tu parte este incompleta.
Cuatro ramas que viven una semana = conflictos imposibles el ultimo dia.

> Antes de mergear, comprueba que un **clon limpio arranca**. Que funcione en tu
> carpeta no basta: ya paso una vez que se subieron las plantillas sin el `app.py`
> que las registra, y `main` respondia 500 para todo el mundo menos para quien lo
> subio.

---

## Despliegue

La aplicacion corre en PythonAnywhere: **https://ana1604.pythonanywhere.com**

Guia completa, variables de entorno y tabla de errores comunes en
[`docs/despliegue.md`](docs/despliegue.md).

Para publicar cambios, en la consola Bash de PythonAnywhere:

```bash
cd ~/vibe-planner && git pull origin main
source ~/.virtualenvs/vibeplanner/bin/activate
pip install -r requirements.txt
python seed.py            # <-- siembra los permisos nuevos. NO te lo saltes
```

Luego boton **Reload** en la pestana Web. `vibe_planner.db` esta en `.gitignore`,
asi que los datos de produccion sobreviven a cada actualizacion.

---

## Evidencia para la rubrica

Cada prompt que uses va en `docs/prompts/` **el mismo dia**, con: el prompt
literal, lo que devolvio la IA, que aceptaste o rechazaste **y por que**, y al
menos un ejemplo real de codigo mal generado y su correccion.
