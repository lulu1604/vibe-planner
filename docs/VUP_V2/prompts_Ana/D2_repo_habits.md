# D2 — `repo_habits.py`, el único componente que toca `habits`

**Objetivo:** un repositorio con cinco funciones, contrato congelado, que sea el
**único** sitio del proyecto donde aparezca la palabra `habit_logs` en un SQL.
Todo lo demás (blueprint, métricas, plantillas) pasa por aquí.

**Archivos que salen de aquí:** `repo_habits.py`

**Tiempo estimado:** 2 horas

**Depende de:** D1 terminado (las tablas existen)

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Genera `repo_habits.py`, la capa de acceso a datos del Módulo D. Antes de
escribir, lee `repo_events.py` (Módulo C) para copiar exactamente su estilo:
docstring de contrato en la cabecera, `database.get_db()`, filas convertidas a
`dict`, y `user_id` siempre dentro del `WHERE`.

### 1. Contrato congelado — estas cinco firmas y ninguna más

```python
def list_by_user(user_id)                       -> list[dict]
def get_owned(habit_id, user_id)                -> dict | None
def create(data, user_id)                       -> int
def upsert_log(habit_id, date_iso, value, done) -> bool
def logs_range(habit_id, from_iso, to_iso)      -> list[dict]
```

Escribe el contrato en el docstring del módulo, con el aviso de que cambiar una
firma obliga a avisar al grupo antes.

### 2. `upsert_log` es un **upsert**, no un insert

La tabla tiene `UNIQUE (habit_id, log_date)`. Corregir el valor de hoy **no
puede** crear una segunda fila (TC-34):

```python
def upsert_log(habit_id, date_iso, value, done):
    db = database.get_db()
    db.execute(
        """INSERT INTO habit_logs (habit_id, log_date, value, done)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(habit_id, log_date)
           DO UPDATE SET value = excluded.value, done = excluded.done""",
        (habit_id, date_iso, value, 1 if done else 0),
    )
    db.commit()
    return True
```

Comenta **por qué** es un upsert y no un `SELECT` seguido de `INSERT` o `UPDATE`:
esa versión tiene una condición de carrera y, sobre todo, duplica la fila si el
`SELECT` mira la fecha equivocada.

### 3. La propiedad se comprueba **en el `WHERE`**

- `get_owned(habit_id, user_id)` → `WHERE id = ? AND user_id = ?`. Devuelve
  `None` si no es suyo. **Nunca** traer la fila y comparar después en Python.
- `list_by_user(user_id)` → solo hábitos con `is_active = 1`, ordenados por
  `habit_type` y luego `name`, para que la pantalla salga siempre en el mismo
  orden.
- `create(data, user_id)` → devuelve el `id` nuevo (`cursor.lastrowid`). El
  `user_id` llega como argumento desde la sesión, **jamás** dentro de `data`.
- `logs_range(habit_id, from_iso, to_iso)` → `WHERE habit_id = ? AND log_date
  BETWEEN ? AND ? ORDER BY log_date`. Como `log_date` es ISO, el `BETWEEN` de
  texto funciona y usa el índice.

### 4. Dos funciones auxiliares que necesita la pantalla

Añádelas al mismo módulo (son lectura de `habit_logs`, así que su sitio es este):

```python
def log_of_day(habit_id, date_iso) -> dict | None   # el registro de un día concreto
def logs_of_day_by_user(user_id, date_iso) -> dict  # {habit_id: fila} de todos sus hábitos
```

`logs_of_day_by_user` existe para **evitar el problema N+1**: la pantalla de
hábitos necesita el registro de hoy de cada hábito, y hacer una consulta por
hábito dentro de un bucle es exactamente lo que no queremos. Una sola consulta
con `JOIN habits ON …WHERE habits.user_id = ?` y se devuelve indexado por
`habit_id`.

### 5. Validación de entrada — en el repositorio, no en la plantilla

`create()` debe rechazar (levantando `ValueError` con un mensaje en español apto
para mostrar al usuario):

- `name` vacío o de más de 80 caracteres
- `habit_type` fuera de `('dieta','ejercicio','relajacion','sueno','general')`
- `target_value` menor o igual a 0, o mayor que 1000
- `unit` fuera de `('horas','minutos','vasos','veces','vez')`

Los mensajes dicen **qué pasó y cómo arreglarlo**: *"La meta debe ser mayor que
0. Por ejemplo: 8 horas."*, no *"Valor inválido"*.

### 6. Al final del archivo, asserts ejecutables

Igual que `database.py` y `validators.py`, cierra con un bloque
`if __name__ == "__main__":` que corra sobre una base temporal (usa
`tempfile.mkstemp` y `database.raw_connection()`, nunca `vibe_planner.db`) y
compruebe al menos:

1. `create()` devuelve un id y el hábito aparece en `list_by_user()`.
2. `get_owned(id, otro_usuario)` devuelve `None`.
3. `upsert_log` dos veces sobre la misma fecha deja **una sola fila**, con el
   último valor (TC-34).
4. `create()` con `habit_type='sueño'` (con tilde) levanta `ValueError`.
5. `logs_range` acotado a tres días devuelve exactamente esos tres.

Termina con `print("SUCCESS: ...")` como los demás módulos del proyecto.

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿`upsert_log` hace `SELECT` y luego decide?** Recházalo: tiene condición de
   carrera y es justo el defecto que el `ON CONFLICT` elimina de raíz.
2. **¿`get_owned` trae la fila y compara `fila["user_id"] == user_id` en
   Python?** El filtro va en el `WHERE`. Si no, cualquier bug futuro que se salte
   la comparación filtra datos de otra persona.
3. **¿Calculó la racha aquí?** No. La racha es **lógica de negocio** y vive en
   `metrics.py` (paso D3). Este archivo solo lee y escribe filas.
4. **¿Abrió su propia conexión con `sqlite3.connect()`?** Debe usar
   `database.get_db()`, que ya trae los PRAGMAs y la conexión por petición.
5. **¿Devuelve objetos `sqlite3.Row`?** Conviértelos a `dict`, como
   `repo_events.py`: un `Row` no se serializa ni se prueba cómodamente.
6. **¿Concatenó algún valor en el SQL con f-string?** Todo va con `?`.
7. **¿`create()` acepta `user_id` dentro de `data`?** Debe ser un argumento
   aparte: si viene del diccionario del formulario, alguien acabará creando
   hábitos a nombre de otro.
8. **¿Falta `db.commit()`** en las tres funciones que escriben? SQLite no
   autocommite y el dato se pierde al cerrar la petición.

---

## ✅ Verificación del paso

```bash
python repo_habits.py
```

- [ ] Los 5 asserts pasan y sale el `SUCCESS`
- [ ] `grep -rn "habit_logs" --include=*.py .` devuelve **solo** `repo_habits.py`
- [ ] `grep -n "sqlite3.connect" repo_habits.py` no devuelve nada
- [ ] Ningún SQL del archivo tiene f-strings ni `%`
- [ ] `python test_v2.py` sigue en verde

---

## 🤝 Al cerrar este paso

Anota en `_bitacora.md` si la IA generó el `upsert` como `SELECT` + `INSERT`.
Es el error más probable de este paso y, si lo cometió, ese fragmento es
**material perfecto para la evidencia de la rúbrica**: código plausible,
sintácticamente válido y funcionalmente incorrecto.
