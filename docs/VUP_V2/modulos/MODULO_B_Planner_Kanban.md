# 🗂️ MÓDULO B — Planner diario, Kanban y tareas de equipo

**Dueña propuesta:** Lucero Ayala *(ya es dueña de `scoring.py` desde v1)*
**Historias:** US1 · US2 · US3 · US4 *(heredadas)* · US8 (revisión del día) · US9 (Kanban)
**Diferido a v3:** US10 (asignación de tareas) y el rol `lider` — decisión de alcance del equipo
**Depende de:** Módulo A — arranca en cuanto `security.py` esté en `main` (hito H2)

---

## 🎯 Qué construyes

El corazón funcional del producto: la lista de actividades, el ranking explicable,
la revisión del día y el tablero Kanban. La v1 ya resolvió el motor de puntaje —
**esa fórmula no se toca**. Lo que añade la v2 es que ahora cada tarea tiene
dueño, tiene horario, vive en una columna y puede haber sido asignada por otra
persona.

---

## 📁 Archivos que te pertenecen

| Archivo | Qué contiene |
|---|---|
| `repo_tasks.py` | Único componente que toca la tabla `tasks` |
| `scoring.py` | Motor de puntaje. **La fórmula no cambia** |
| `planner.py` | Blueprint: `/planner`, `/tasks/*`, `/kanban`, `/equipo/tareas` |
| `templates/planner/dia.html` | Revisión del día (US8) |
| `templates/planner/kanban.html` | Tablero de 4 columnas (US9) |
| `templates/planner/equipo.html` | Vista de tareas asignadas (US10) |
| `static/js/kanban.js` | Arrastrar y soltar |

---

## 🔒 La regla que no puedes romper

> **Toda consulta lleva `user_id` DENTRO del `WHERE`.**
> Traer las filas y filtrarlas después en Python **no cuenta**: si la fila llegó
> a memoria, ya se filtró mal.

```python
# ✅ Correcto
def get_owned(task_id, user_id):
    row = get_db().execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
    ).fetchone()
    return dict(row) if row else None

# ❌ Incorrecto — la fila ajena ya salió de la base de datos
def get_owned(task_id, user_id):
    task = get_task(task_id)
    return task if task["user_id"] == user_id else None
```

Y en el controlador, **las dos llaves**:

```python
@planner.route("/tasks/<int:task_id>/edit", methods=["POST"])
@requires("planner.editar")                              # 🔑 permiso
def edit_task(task_id):
    task = repo_tasks.get_owned(task_id, current_user_id())   # 🔑 propiedad
    if task is None:
        abort(404)          # 404, NO 403: un 403 confirma que ese id existe
```

Esto es **TC-08** y **TC-11**, dos de los tres casos que bloquean el release.

---

## 📋 Pasos, en orden

### 1. `repo_tasks.py` — contrato congelado

```python
def get_owned(task_id, user_id)               -> dict | None
def list_by_user(user_id, column=None)        -> list[dict]
def list_by_day(user_id, date_iso)            -> list[dict]
def list_board(user_id)                       -> dict[str, list[dict]]
def list_assigned_by(leader_id)               -> list[dict]
def create(data, owner_id, assigned_by=None)  -> int
def update_owned(task_id, user_id, data)      -> bool
def move_column(task_id, user_id, column)     -> bool
def delete_owned(task_id, user_id)            -> bool
def daily_progress(user_id, date_iso)         -> {"total","completed","percent"}
```

`list_board()` devuelve las cuatro claves **siempre**, aunque estén vacías:

```python
{"backlog": [...], "todo": [...], "ongoing": [...], "done": [...]}
```

Si una clave falta, la plantilla revienta el día que un usuario no tenga tareas en
esa columna.

### 2. `scoring.py` — solo adaptación

La fórmula sigue igual: **Prioridad** 50/30/10 · **Urgencia** 40/20/10/5 ·
**Ajuste de tiempo** +15/0. El desempate sigue siendo puntaje ↓, `due_date` ↑,
`id` ↑. Lo único que cambia es que la lista que recibes ya viene filtrada por
`user_id`.

Sigue usando `today_local()`, **nunca** `datetime.now()`: el servidor corre en UTC
y Lima es UTC−5. Después de las 7 p.m. una tarea de hoy se marcaría como vencida.

### 3. Los cuatro estados, una sola columna

v1 tenía `status` con `pending | in_progress | completed`. v2 tiene
`kanban_column` con **cuatro** valores y **una sola fuente de verdad**:

| v1 | v2 | Significado |
|---|---|---|
| — | `backlog` | Intención. **No cuenta para el progreso del día** |
| `pending` | `todo` | Comprometido para hoy |
| `in_progress` | `ongoing` | En curso |
| `completed` | `done` | Hecho |

No mantengas las dos columnas "por compatibilidad": se desincronizan en la primera
semana. La migración ya hace el mapeo.

### 4. `/planner` — revisión del día (US8)

Solo **hoy**, ordenado por hora de inicio. Cada tarjeta con nombre, descripción,
`HH:MM - HH:MM` y su color en el borde izquierdo. El progreso del día se calcula
sobre `todo + ongoing + done`, **excluyendo `backlog`** (TC-22).

### 5. `/kanban` (US9)

Cuatro columnas con su contador. El movimiento va por `POST /tasks/<id>/column`.
Valida la columna contra `config.KANBAN_COLUMNS` **antes** de tocar la base:
cualquier otro valor es HTTP 400 (TC-21).

`kanban.js` pinta el movimiento de forma optimista y **devuelve la tarjeta a su
sitio si el servidor responde error**. Una interfaz que muestra un cambio que no
se guardó es peor que una lenta.

En móvil las columnas se apilan verticalmente — cuatro columnas de 90 px son
ilegibles (TC-43, ver Design System § 5.2).

### 6. `/equipo/tareas` — asignación (US10)

```python
assigned_to = request.form.get("assigned_to")
if assigned_to and has_permission("tarea.asignar"):
    owner_id = int(assigned_to)        # solo con el permiso
    assigned_by = current_user_id()
else:
    owner_id = current_user_id()       # por defecto, SIEMPRE tú
    assigned_by = None
```

Sin el permiso, el campo se ignora en silencio y la tarea se crea para quien la
envió (TC-24). Valida además que el destinatario exista y esté **activo**.

---

## 🕳️ Trampas concretas de este módulo

1. **El `user_id` no viene nunca del formulario.** Sale de la sesión. La única
   excepción es la asignación de US10, y exige el permiso `tarea.asignar`.
2. **`list_board()` devuelve las cuatro claves siempre**, aunque estén vacías.
3. **El progreso excluye `backlog`.** Es intención, no compromiso del día.
4. **El endpoint del desglose también necesita las dos llaves.** `GET
   /api/task/42/score-breakdown` de una tarea ajena responde 404 (TC-16).
5. **La suma del modal debe coincidir con la insignia.** Si difieren, se pierde
   el diferenciador del producto entero (TC-15).
6. **Valida en el servidor, no solo con `required` en el HTML.** Pruébalo con
   `curl` saltándote el navegador (TC-13).
7. **Los puntajes van en `--font-data`** (monoespaciada): los dígitos se alinean
   entre tarjetas y el ranking se compara de un vistazo.

---

## ✅ Listo cuando

- [ ] `ana` ve **solo** sus tareas en planner, kanban y métricas (**TC-11** ⚠️)
- [ ] Editar, borrar o auditar una tarea ajena responde 404 (**TC-08** ⚠️, TC-16)
- [ ] El orden del ranking es idéntico en cinco recargas seguidas (TC-14)
- [ ] La suma del modal coincide con la insignia (TC-15)
- [ ] `/planner` muestra solo hoy, ordenado por hora (TC-17)
- [ ] Mover una tarjeta y recargar con F5 conserva la columna (TC-20)
- [ ] `column=archivado` responde 400 (TC-21)
- [ ] El progreso excluye el backlog (TC-22)
- [ ] Sin `tarea.asignar`, el campo `assigned_to` se ignora (TC-24)
- [ ] Las cinco pantallas tienen estado vacío diseñado (TC-18)
- [ ] Tus asserts añadidos a `test_v2.py` pasan
