# 🔍 Hallazgos del repositorio — léelo antes del D1

Esto no es teoría: sale de revisar el código que hoy está en `main`. Son las
cinco cosas que te van a morder si arrancas sin saberlas. Quince minutos aquí te
ahorran una tarde.

---

## 1. Las tablas de hábitos NO existen todavía

`schema_v2.sql` tiene hoy: `users`, `roles`, `permissions`, `role_permissions`,
`user_roles`, `events`, `event_invitations`. **No tiene `habits` ni
`habit_logs`.** El bloque SQL está escrito en `05_Construction_II.md` § 1, pero
nadie lo ha pegado al archivo.

**Qué implica:** el paso **D1** es obligatorio y va primero. Y como Jose es el
**dueño único del esquema**, el bloque se le enseña antes de hacer merge — no se
mete a escondidas.

---

## 2. La tabla `tasks` sigue siendo la de la v1 (sin `user_id`) ⚠️ el riesgo grande

`database.py` crea `tasks` con estas columnas:

```
id · title · category · priority_level · due_date · estimated_minutes · status · created_at
```

El diseño v2 (`05_Construction_II.md`) dice que debe tener además `user_id`,
`description`, `start_time`, `end_time`, `color` y `kanban_column`. **Eso es del
Módulo B (Lucero) y todavía no está.**

**Qué implica para ti:** `daily_summary(user_id, date_iso)` necesita leer tareas
del usuario, y hoy **no hay forma de saber de quién es cada tarea**.

**Cómo se resuelve — y no es un parche feo:** `metrics.py` pregunta a SQLite qué
columnas existen antes de consultar:

```python
def _columnas(tabla):
    """Las columnas que la tabla tiene AHORA MISMO.

    El Modulo B todavia no ha anadido user_id a `tasks`. Preguntar en vez de
    suponer permite que /metricas funcione hoy y se llene sola en cuanto Lucero
    haga su merge, sin tocar una linea de aqui.
    """
    return {fila["name"] for fila in get_db().execute(f"PRAGMA table_info({tabla})")}
```

Y si `user_id` no está, `daily_summary` devuelve las secciones vacías con la
bandera `"tareas_conectadas": False`, y la plantilla dice
*"El módulo de actividades aún no está conectado"* en vez de inventar un 0 %
que parece un dato real.

> 🚩 **Lo que NO debes hacer:** añadir tú `user_id` a `tasks`. Esa tabla es de
> Lucero y de Jose. Tocarla desde el Módulo D es el clásico conflicto de merge
> del jueves por la noche.

**Coordinación:** dile a Lucero que en cuanto `tasks` tenga `user_id` y
`kanban_column`, tus métricas se encienden solas. Y acuerden los nombres de las
secciones: TC-37 espera exactamente **Trabajo**, **Personal** y **Actividades**
en la columna `category`.

---

## 3. El menú te reserva dos nombres exactos

`home.py` ya declara `endpoint: "habitos.lista"` y `endpoint: "habitos.metricas"`.
Si tu blueprint se llama `habits` o tu vista `index`, el menú no encuentra el
endpoint, atrapa el `BuildError` y pinta tu módulo como **"Próximamente"**
apagado — sin ningún error en consola. Blueprint `habitos`, vistas `lista` y
`metricas`. Punto.

---

## 4. Los bloques de `base.html` NO se llaman `titulo` ni `contenido`

Se llaman **`title`, `encabezado`, `subtitulo`, `acciones`, `content`,
`extra_css`, `extra_js`**. El propio archivo lo advierte en un comentario, porque
ya pasó: renombrarlos deja la página **en blanco sin ningún error**.

La ficha del Módulo D y el prompt P4 de Piero mencionan `titulo`/`contenido`.
Están desactualizados. Manda el archivo, no el documento.

---

## 5. El Módulo C se maquetó con clases que no existen

`templates/calendario/mes.html` usa `btn-secondary`, `btn-outline`, `text-2xl`,
`text-navy-900`, `flex-between`, `mb-4`… que parecen de Tailwind y **no están en
`components.css`**. Resultado: el calendario se ve distinto al resto de la
aplicación, que es exactamente lo que US16 existe para evitar.

Además, `home.py` espera el endpoint `calendario.mes` y el blueprint real de Jose
se llama `calendar_bp` con la vista `month_view`: **la entrada "Calendario" del
menú está apagada ahora mismo**. Es un `url_for` de una línea.

**Qué implica:** el paso **D7** incluye normalizar esa pantalla al design system.
Es trabajo tuyo por US16, pero es **código de Jose**: acuérdalo con él antes de
tocarlo, o pásale la lista de reemplazos para que lo haga él. Lo que no vale es
que llegue el viernes con dos estéticas distintas.

---

## 📋 Resumen para la reunión del primer día

| # | Hallazgo | A quién le toca | Urgencia |
|---|---|---|---|
| 1 | Faltan `habits` y `habit_logs` en `schema_v2.sql` | Ana propone, **Jose aprueba** | 🔴 Bloquea D2 |
| 2 | `tasks` sin `user_id` → métricas de tareas no se pueden calcular | **Lucero** (Módulo B) | 🔴 Bloquea TC-37 |
| 3 | Nombres `habitos.lista` / `habitos.metricas` | Ana | 🟡 Al escribir D4 |
| 4 | Bloques de `base.html` | Ana (y todo el que maquete) | 🟡 Al escribir D4 |
| 5 | Calendario fuera del design system + menú apagado | **Jose**, con la lista de Ana | 🟠 Antes de la demo |

> 📌 La ficha del Módulo D lo dice y conviene repetirlo: **esta es la carga más
> repartida del equipo** — un módulo funcional mediano *más* el design system
> transversal. Si al arrancar ves que no entra, plantéalo **el primer día**, no
> el jueves. El design system puede pasar a quien cierre antes su módulo.
