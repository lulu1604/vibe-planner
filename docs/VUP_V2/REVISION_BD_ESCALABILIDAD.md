# 🔍 Revisión de escalabilidad de la base de datos

**Alcance:** el esquema v2 de `05_Construction_II.md` § 1.
**Pregunta que responde:** ¿qué se rompe primero cuando esto crezca, y qué cuesta
un peso hoy que costaría diez mañana?

**Conclusión corta:** el diseño **es escalable en lo que importa** — el modelo de
permisos, que es la decisión difícil de revertir. Lo que hay que corregir son
ocho detalles concretos, siete de ellos de una línea. El techo real del sistema no
está en el esquema: está en que SQLite bloquea el archivo al escribir, y eso está
medido y documentado más abajo.

---

## ✅ Lo que ya está bien y no hay que tocar

**1. El modelo de permisos escala sin tocar código.** Añadir un rol nuevo es una
entrada en `seed.py`; añadir un permiso, otra. Ninguna de las dos cosas obliga a
modificar un controlador, porque los decoradores comprueban códigos de permiso y
no nombres de rol. Esta es la decisión que habría sido carísima de revertir, y
está tomada bien. Cuando vuelva el rol `lider` de la v3, entra sin refactor.

**2. Las tablas puente con clave primaria compuesta** impiden duplicados a nivel
de motor: un usuario no puede tener el mismo rol dos veces aunque el código lo
intente.

**3. `granted_by … ON DELETE SET NULL`.** Si se borra el admin que otorgó un rol,
el rol sobrevive. Lo contrario habría sido un `CASCADE` que borra permisos de
gente que no tuvo nada que ver.

**4. El índice parcial de invitaciones** (`WHERE invited_user_id IS NOT NULL`) es
la forma correcta de exigir unicidad solo sobre las filas aceptadas. Además es
sintaxis portable a PostgreSQL.

**5. `UNIQUE (habit_id, log_date)`** convierte la idempotencia del registro diario
en una garantía del motor, no en una promesa del código.

**6. Fechas como TEXT ISO** (`YYYY-MM-DD`). Ordenan alfabéticamente igual que
cronológicamente y son portables. Es la elección correcta en SQLite.

---

## 🔧 Los ocho hallazgos

### 🔴 H1 — `username` y `email` no son insensibles a mayúsculas *(prioridad alta)*

`UNIQUE` en SQLite distingue mayúsculas. Hoy `repo_users` normaliza a minúsculas
antes de insertar, así que funciona — **hasta que alguien inserte desde otro
sitio**: un script de importación, la consola de `sqlite3`, una ruta nueva escrita
con prisa. Entonces conviven `Piero` y `piero` como dos cuentas distintas y el
login se vuelve ambiguo.

```sql
username TEXT NOT NULL UNIQUE COLLATE NOCASE,
email    TEXT NOT NULL UNIQUE COLLATE NOCASE,
```

La garantía baja del código al motor, que es donde debe estar.

---

### 🔴 H2 — `list_users()` sin paginación *(prioridad alta)*

```sql
SELECT ... FROM users u LEFT JOIN user_roles ... GROUP BY u.id ORDER BY u.username
```

Sin `LIMIT`, esta consulta trae **todas** las cuentas y las renderiza en una sola
página. Con 12 usuarios es invisible; con 5 000 es una página de varios megabytes
y un servidor free tier que se queda sin memoria.

Cuesta una línea ahora y un rediseño de la plantilla después:

```python
def list_users(search=None, limit=50, offset=0): ...
def count_users(search=None): ...
```

Es el único sitio del sistema que hace una consulta sin acotar, porque todas las
demás filtran por `user_id`.

---

### 🟡 H3 — Faltan `updated_at` *(prioridad media)*

Solo hay `created_at`. Sin `updated_at` no se puede responder "¿qué cambió desde
ayer?", que es lo que necesita cualquier sincronización, caché o auditoría futura.
Añadirlo hoy es una columna; añadirlo con datos en producción es una migración.

```sql
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

En `users`, `tasks` y `events`. SQLite no tiene `ON UPDATE CURRENT_TIMESTAMP`, así
que se actualiza en el `UPDATE` del repositorio o con un trigger.

---

### 🟡 H4 — Sintaxis solo de SQLite *(prioridad media — portabilidad)*

Dos puntos atan el código a SQLite sin necesidad:

| Ahora | Portable | Dónde |
|---|---|---|
| `INSERT OR IGNORE` | `INSERT … ON CONFLICT DO NOTHING` | `seed.py`, `_link_roles()` |
| `GROUP_CONCAT(r.code, ',')` | `string_agg(r.code, ',')` en PostgreSQL | `list_users()` |

`ON CONFLICT` funciona igual en SQLite 3.24+ y en PostgreSQL 9.5+: cambiarlo hoy
es gratis. El `GROUP_CONCAT` es más difícil de evitar; lo razonable es **aislarlo
en `repo_users.py`** —donde ya está— y dejar un comentario señalándolo, para que
el día de la migración se sepa exactamente qué línea tocar.

---

### 🟡 H5 — Los `CHECK` de catálogo son rígidos en SQLite *(prioridad media)*

```sql
CHECK (kanban_column IN ('backlog','todo','ongoing','done'))
CHECK (habit_type IN ('dieta','ejercicio','relajacion','sueno','general'))
CHECK (status IN ('tentativo','confirmado','cancelado'))
```

Dan integridad real, y eso es valioso. El problema es que **SQLite no permite
modificar un `CHECK`**: cambiarlo obliga a crear la tabla nueva, copiar los datos,
borrar la vieja y renombrar. Añadir una quinta columna al Kanban dejaría de ser
una línea.

**Recomendación: dejarlos.** Para el alcance de este proyecto, la integridad vale
más que la flexibilidad, y los cuatro estados del Kanban están congelados en
Elaboration. Pero conviene saberlo antes de prometer una columna nueva, y por eso
queda escrito aquí. Si en la v3 los estados se vuelven configurables, la solución
es una tabla catálogo `task_columns` con clave foránea, no ampliar el `CHECK`.

---

### 🟢 H6 — `_link_roles()` hace una consulta por rol *(prioridad baja)*

```python
for code in role_codes:
    role = db.execute("SELECT id FROM roles WHERE code = ?", (code,)).fetchone()
```

Es un N+1 clásico. Con dos roles es irrelevante — dos consultas sobre un índice
único, microsegundos. Se anota por dos razones: para que nadie lo copie a un bucle
sobre 500 tareas, y porque si el catálogo de roles crece se resuelve con un solo
`WHERE code IN (...)` o cacheando el mapa `code → id` al arrancar.

---

### 🟢 H7 — Índices que faltarán cuando vuelva US10 *(prioridad baja)*

Los siete índices actuales cubren exactamente las consultas de hoy. Cuando el rol
`lider` y la asignación de tareas vuelvan del backlog v3, la vista de equipo
filtrará por `assigned_by` sin índice:

```sql
CREATE INDEX ix_tasks_assigned_by ON tasks(assigned_by);
```

No lo añadas ahora: un índice sobre una columna que nadie consulta solo cuesta
escrituras. Queda anotado para el día que haga falta.

---

### 🟢 H8 — `CURRENT_TIMESTAMP` guarda en UTC *(prioridad baja — documentar)*

`created_at` se llena con la hora **UTC** del servidor. Las fechas de negocio
(`due_date`, `log_date`, `start_at`) sí están en hora de Lima, porque las calcula
`scoring.today_local()`.

Conviven dos zonas horarias en la misma base y eso es correcto —los metadatos
técnicos en UTC, las fechas del usuario en su zona— **siempre que esté escrito**.
Si no, alguien comparará `created_at` con `due_date` y obtendrá cinco horas de
diferencia sin entender por qué.

---

## 📈 El techo real: no es el esquema, es SQLite escribiendo

El esquema aguanta millones de filas sin despeinarse. Lo que pone el techo es que
**SQLite bloquea el archivo entero durante una escritura**.

| Escala | Qué pasa | ¿Sirve? |
|---|---|---|
| 1–20 usuarios simultáneos | WAL permite leer mientras uno escribe. Sin problemas | ✅ Objetivo del proyecto |
| 20–100 | Aparecen `database is locked` esporádicos. El `timeout=10` los absorbe | ⚠️ Aceptable |
| 100+ escrituras concurrentes | Los bloqueos se hacen visibles como lentitud | ❌ Toca migrar |

Las tres mitigaciones ya están en el diseño y hay que respetarlas:

1. **`PRAGMA journal_mode = WAL`** en cada conexión — lecturas concurrentes
   mientras alguien escribe.
2. **`timeout = 10.0`** — en vez de fallar al instante, espera a que se libere.
3. **Transacciones cortas.** Abrir, escribir, hacer `commit`. Nunca dejar una
   transacción abierta mientras se renderiza una plantilla o se espera al usuario:
   eso bloquea a todos los demás.

### Cuando toque migrar a PostgreSQL

La buena noticia es que el diseño no lo impide. Lo que cambia:

| Elemento | SQLite | PostgreSQL |
|---|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | | `SERIAL` / `IDENTITY` |
| `TEXT`, `INTEGER`, `REAL` | | `TEXT`, `INTEGER`, `DOUBLE PRECISION` — equivalen |
| `is_active INTEGER` (0/1) | | `BOOLEAN` |
| `GROUP_CONCAT` | | `string_agg` |
| `INSERT OR IGNORE` | | `ON CONFLICT DO NOTHING` *(H4)* |
| `ON CONFLICT DO UPDATE` | | Igual ✅ |
| Índice parcial `WHERE …` | | Igual ✅ |
| `CHECK`, `FOREIGN KEY`, PK compuesta | | Igual ✅ |
| Fechas TEXT ISO | | Migrables a `DATE` / `TIMESTAMPTZ` |

**Y lo que hace que la migración sea viable de verdad:** todo el SQL vive en los
repositorios (`repo_users`, `repo_tasks`, `repo_events`, `repo_habits`). Migrar es
reescribir cinco archivos, no buscar consultas repartidas por veinte
controladores. Esa fue la decisión de arquitectura que compró la opción.

---

## 📄 Parche `schema_v2.1.sql`

Lo mínimo a aplicar. Como todavía no hay datos en producción, se aplica **borrando
y regenerando** — no hace falta migración.

```sql
-- H1: unicidad insensible a mayúsculas, garantizada por el motor
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    DEFAULT '',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- H3
);

-- H3: en tasks y events
ALTER TABLE tasks  ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE events ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- H3: mantenerlo al día sin tocar cada UPDATE del repositorio
CREATE TRIGGER IF NOT EXISTS trg_users_updated
AFTER UPDATE ON users FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- H7: NO aplicar todavía. Solo cuando vuelva US10 del backlog v3.
-- CREATE INDEX ix_tasks_assigned_by ON tasks(assigned_by);
```

Y en `repo_users.py`:

```python
# H2
def list_users(search=None, limit=50, offset=0): ...
def count_users(search=None): ...

# H4: portable a PostgreSQL
INSERT INTO user_roles (user_id, role_id, granted_by)
VALUES (?, ?, ?)
ON CONFLICT (user_id, role_id) DO NOTHING;
```

---

## ✅ Resumen accionable

| # | Hallazgo | Prioridad | Coste | ¿Ahora? |
|---|---|---|---|---|
| H1 | `COLLATE NOCASE` en usuario y correo | 🔴 Alta | 2 líneas | **Sí** |
| H2 | Paginación en `list_users()` | 🔴 Alta | 1 función | **Sí** |
| H3 | Columnas `updated_at` | 🟡 Media | 3 columnas + trigger | **Sí** |
| H4 | `ON CONFLICT` en vez de `INSERT OR IGNORE` | 🟡 Media | Buscar y reemplazar | **Sí** |
| H5 | Rigidez de los `CHECK` en SQLite | 🟡 Media | — | Documentado, se dejan |
| H6 | N+1 en `_link_roles()` | 🟢 Baja | — | Anotado |
| H7 | Índice `tasks(assigned_by)` | 🟢 Baja | 1 línea | Cuando vuelva US10 |
| H8 | Dos zonas horarias conviviendo | 🟢 Baja | Comentario | **Sí**, documentar |

Los cuatro "Sí" caben en media hora y van **antes** del paso P1, cuando el esquema
todavía no tiene datos de nadie. Después cuestan una migración coordinada con todo
el equipo.
