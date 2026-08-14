# 🔍 Auditoría de integración — Módulos C (Jose) y D (Ana)

**Fecha:** 14/08/2026 · **Alcance:** `main` con A + C + D integrados, sin el Módulo B
**Método:** las tres suites del equipo + arranque real de la aplicación + 42
comprobaciones de integración cruzando dos cuentas + 8 verificaciones dirigidas
sobre cada hallazgo, para descartar falsos positivos antes de reportarlo.

---

## Resumen

| | |
|---|---|
| Suites del equipo | `test_module_c.py` 7/7 · `test_module_d.py` 9/10 (TC-37 omitido) · `test_v2.py` OK |
| Rutas GET que responden 500 | **0** |
| Permisos usados en `@requires` que no están sembrados | **0** |
| Formularios POST sin token CSRF | **0** |
| **Defectos encontrados** | **6** — 1 crítico, 1 grave, 4 medios/bajos |
| Falsos positivos descartados | 1 |

**El trabajo de ambos está bien hecho.** Los seis defectos no son de calidad de
código: son cosas que **solo aparecen al integrar** o al atacar una ruta desde
fuera del navegador, y por eso ninguna de las tres suites los veía. Cada suite
prueba su módulo por dentro; ninguna prueba lo que pasa entre dos.

Los seis están **corregidos y verificados**, con `test_auditoria.py` como red
para que no vuelvan.

---

## 🔴 A-01 — CRÍTICO · Cinco rutas de la v1 seguían vivas y sin autenticación

**Archivo:** `app.py` *(no es de Jose ni de Ana: es el puente heredado de la v1
que nadie retiró)*

Estas cinco rutas seguían registradas, **sin `@login_required` y sin `@requires`**:

```
GET  /                                 -> index.html con TODAS las tareas
POST /tasks                            -> crear
POST /tasks/<id>/delete                -> eliminar
POST /tasks/<id>/status                -> cambiar estado
GET  /api/task/<id>/score-breakdown    -> desglose del puntaje
```

**Verificado sin sesión, con un cliente anónimo:**

```
GET  /                          -> 200, y la página lista las tareas de todo el mundo
POST /tasks                     -> 302, fila creada por un anónimo
GET  /                          -> el anónimo LEE la tarea recién creada
GET  /api/task/1/score-breakdown-> 200 con el JSON completo
POST /tasks/1/delete            -> 302, la tarea DESAPARECE de la base
```

El token CSRF no protegía nada: se obtiene leyendo la propia página pública.

Rompe **TC-08** y **TC-11**, los dos casos críticos que bloquean el release. Y no
se arregla poniendo un decorador: `tasks` no tiene columna `user_id`, así que no
hay forma de saber de quién es cada fila. Además `database.get_daily_progress()`
cuenta las tareas de **toda** la base, así que la barra de progreso mezclaba el
trabajo de desconocidos.

**Segundo motivo para retirarlas, independiente de la seguridad:** `/tasks` y
`/api/task/<id>/score-breakdown` son **exactamente** los endpoints que trae el
blueprint de Lucero. Al registrarse, Flask conserva la primera regla que
coincide y la suya quedaría muerta **sin un solo error en consola**. Eso es un
día entero de depuración.

**Corrección aplicada:** las cinco rutas se retiran. `/` redirige a
`home.index`, que sí comprueba la sesión. `templates/index.html`,
`static/js/main.js` y las funciones v1 de `database.py` quedan sin usar pero
**no se borran**: son la referencia de la que parte Lucero.

> Después del arreglo, las únicas rutas sin decorador son `/`, `/login`,
> `/register` y `/logout`. Comprobado recorriendo `app.url_map` entero.

---

## 🟠 A-02 — GRAVE · HTTP 500 al editar un evento con un `status` cualquiera

**Archivo:** `calendar_bp.py` · Módulo C

```python
"status": request.form.get("status", "confirmado")   # sin lista blanca
```

El valor va directo a una columna con
`CHECK (status IN ('tentativo','confirmado','cancelado'))`. Cualquier otro valor
lanza `sqlite3.IntegrityError` **sin capturar** → pantalla de error 500.

```
POST /eventos/1/editar  status=INVENTADO
  -> IntegrityError: CHECK constraint failed: status IN (...)
```

Lo llamativo es que el **color** de la misma función sí tiene lista blanca
(`if color not in ALLOWED_COLORS`) — y de hecho neutraliza correctamente un
intento de inyección en el atributo `style`, lo comprobé. Solo se olvidó el
`status`.

**Corrección:** constante `ALLOWED_STATUS` y filtrado igual que el color.

---

## 🟡 A-03 — Editar un evento permite dejarlo sin título

**Archivo:** `calendar_bp.py` · Módulo C

`/eventos/nuevo` valida que el título no esté vacío. `/eventos/<id>/editar` no.
Verificado uno contra otro:

| Ruta | título vacío | Resultado |
|---|---|---|
| `POST /eventos/nuevo` | `""` | rechazado, 0 filas ✅ |
| `POST /eventos/<id>/editar` | `""` | **guardado como `''`** ❌ |

Un evento sin título es invisible en la cuadrícula del mes y no hay forma de
recuperarlo desde la interfaz.

**Corrección:** las mismas tres validaciones que en el alta (título, fechas,
fin > inicio), con el mismo mensaje.

---

## 🟡 A-04 — El calendario usa la hora del servidor, no la de Lima

**Archivo:** `calendar_bp.py` · Módulo C

Tres llamadas a `datetime.now()` sin zona horaria:

```python
def _current_local_year_month():
    now = datetime.now()                                   # mes por defecto
hoy = datetime.now().strftime("%Y-%m-%d")                  # celda "hoy"
default_date = request.args.get("date", datetime.now()...)  # fecha del formulario
```

PythonAnywhere corre en **UTC** y Lima es **UTC−5**: a partir de las 19:00 hora
local, el servidor ya está en el día siguiente. Consecuencias reales:

- la celda resaltada como "hoy" es la de mañana,
- el **31 a las 19:01** el calendario abre directamente en el mes siguiente,
- el formulario de evento propone la fecha equivocada.

Es exactamente el riesgo que la v1 documentó y resolvió con `scoring.today_local()`,
y que Ana resolvió en su módulo con `metrics.hoy_iso()`. El calendario se quedó
fuera.

**Corrección:** archivo nuevo **`fechas.py`** con `hoy_iso()`, `hoy_local()` y
`anio_mes_local()`, y `calendar_bp` pasa a usarlo.

> ⚠️ **Deuda que dejo señalada, no arreglada:** ahora la misma regla existe en
> **tres** sitios — `fechas.py`, `scoring.today_local()` (Lucero) y
> `metrics.hoy_iso()` (Ana). Tres definiciones es como se desincronizan. Que
> cada dueño apunte la suya a `fechas.py` cuando pueda tocar su archivo; no lo
> hago yo porque son archivos con dueño y estamos a mitad de merge.

---

## 🟢 A-05 — Eliminar un evento ajeno responde 302, no 404

**Archivo:** `calendar_bp.py` · Módulo C

Las tres rutas que operan sobre un evento concreto no se comportaban igual:

| Ruta | Evento ajeno |
|---|---|
| `POST /eventos/<id>/editar` | 404 ✅ |
| `POST /eventos/<id>/invitar` | 404 ✅ |
| `POST /eventos/<id>/eliminar` | **302 + flash** ❌ |

El dato estaba a salvo — comprobé que el evento sigue existiendo — y el mensaje
es el mismo para "no existe" y "no es tuyo", así que no hay fuga. Pero rompe la
consistencia de la regla de las dos llaves, y esa inconsistencia es la que
mañana alguien copia al escribir una ruta nueva.

**Corrección:** `get_owned()` + `abort(404)`, igual que sus dos hermanas.

---

## 🟢 A-06 — El registro diario de un hábito acepta valores absurdos

**Archivo:** `habits.py` · Módulo D

`repo_habits._validar()` valida muy bien la meta al crear el hábito
(`0 < meta <= 1000`, tipos y unidades con lista blanca). El **registro diario**
no valida el rango:

```
value='-5'      -> guardado: -5.0
value='999999'  -> guardado: 999999.0
value='abc'     -> rechazado ✅ (el ValueError sí se maneja)
```

Un valor negativo o imposible aparece en la tira de la semana y en las métricas,
y el usuario **no puede corregirlo desde ninguna pantalla**.

**Corrección:** el mismo rango que la meta, con el mismo mensaje de ayuda
("revisa la unidad: quizá querías minutos y no horas").

---

## ✅ Falso positivo descartado

Una comprobación automática marcó *"jose ve el hábito «Dormir 8 horas» de ana"*.
**No es una fuga.** Verificado creando un hábito con un nombre irrepetible
(`ZZUNICOANA`): no aparece en la página de jose, y `list_by_user(jose)` devuelve
0 filas. La coincidencia era el texto de ayuda del formulario:

```html
<span class="field-ayuda">Por ejemplo: Dormir 8 horas</span>
```

**El aislamiento del Módulo D está bien.** `get_owned()` lleva el `user_id`
dentro del `WHERE`, `logs_of_day_by_user` y `logs_range_by_user` hacen `JOIN`
con `habits` filtrando por usuario, y registrar un hábito ajeno responde 404.

---

## 👏 Lo que está particularmente bien y conviene no tocar

**Módulo C — Jose**

- El `UNION` de `list_month` (propios + aceptados) con rango `>= … <` en vez de
  `LIKE`: usa el índice y no se rompe si cambia el formato.
- El cruce de año funciona en las cuatro direcciones. Probé 2026-12 → 2027-01,
  febrero de un bisiesto y `mes=13`: ninguno revienta.
- Las invitaciones son **realmente idempotentes** y el token de un evento ya
  borrado muestra el aviso sin filtrar nada del evento.
- El comentario que explica por qué `count_attendees` dejó de sumar al anfitrión
  es justo el tipo de nota que salva a quien venga después.

**Módulo D — Ana**

- `_columnas(tabla)` preguntando por `PRAGMA table_info` en vez de suponer: es lo
  que hace que `/metricas` funcione hoy sin el Módulo B **y se encienda sola**
  cuando llegue. Diseño defensivo de verdad.
- `_porcentaje()` como único punto de división de todo el módulo.
- `racha_desde_logs()` separado de `habit_streak()` para que la pantalla calcule
  N rachas con una sola consulta en vez de N.
- El panel de administración no expone contenido privado **ni escondido en el
  HTML** — lo comprobé leyendo el fuente de la página.

**Transversal**

- CSRF global con lista de exenciones **vacía**, y los 100 % de formularios POST
  de las plantillas llevan su token.
- Los 17 permisos usados en `@requires` están sembrados. Ni un 403 fantasma.

---

## 🔧 Lo que queda abierto para el equipo

### 1. `schema_v2.sql` no contiene la tabla `tasks`

Un clon limpio + `python seed.py` produce una base donde `tasks` **la crea
`database.py` con la forma de la v1** (sin `user_id`, sin `kanban_column`).

Cuando Lucero traiga su `tasks` v2, ambos son `CREATE TABLE IF NOT EXISTS`:
**el primero que corra gana y el otro se ignora en silencio**, sin error. Hay que
acordar antes del merge quién define `tasks` y borrar la otra definición. Es de
los dos hallazgos que más tiempo pueden costar.

### 2. Los tres relojes

`fechas.py`, `scoring.today_local()` y `metrics.hoy_iso()` hacen lo mismo. Que
cada dueño apunte el suyo a `fechas.py`.

### 3. Los dos pendientes que Ana ya dejó anotados

- **Fuentes `.woff2`** — sin `static/fonts/` la app cae a `system-ui`. Decisión
  de grupo.
- **`style.css` es código muerto** — ninguna plantilla lo carga. Es de la v1, así
  que no es decisión unilateral del Módulo D. Confirmo que ninguna plantilla lo
  referencia.

---

## 🧪 `test_auditoria.py`

17 comprobaciones, una por defecto corregido más dos de control de aislamiento.
Se ejecuta sobre una base temporal y **no toca `vibe_planner.db`**.

```bash
python test_auditoria.py     # 17 OK - 0 FALLAS
```

Súbelo con el resto: si alguno vuelve a fallar, el defecto ha vuelto.

### Estado tras los arreglos

```
test_module_c.py    7/7 OK
test_module_d.py    9/10 (TC-37 omitido, espera al Módulo B)
test_v2.py          Núcleo en verde
repo_habits.py      5/5 asserts
metrics.py          5/6 (1 omitido, mismo motivo)
test_auditoria.py   17/17
auditoría cruzada   41 comprobaciones, 0 fallas reales
```

Ninguna suite existente se rompió con los arreglos.
