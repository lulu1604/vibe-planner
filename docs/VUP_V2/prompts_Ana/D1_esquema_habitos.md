# D1 — El esquema de hábitos (`habits` + `habit_logs`)

**Objetivo:** dejar las dos tablas del Módulo D creadas, con las restricciones
que hacen imposibles los defectos, **antes** de escribir una sola línea de
Python. Un `UNIQUE` en la base de datos vale más que diez validaciones en el
servidor: la base no se olvida nunca.

**Archivos que salen de aquí:** ampliación de `schema_v2.sql`

**Tiempo estimado:** 45 minutos (30 de ellos, coordinar con Jose)

> 🤝 **Antes de hacer merge:** Jose Cabrera es el **dueño único del esquema**.
> Escribe el bloque, verifícalo en local, y **enséñaselo antes de subirlo**. Que
> dos personas editen `schema_v2.sql` a la vez el mismo día es el conflicto más
> tonto y más caro que puede tener este proyecto.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Necesito añadir a `schema_v2.sql` las dos tablas del Módulo D. El archivo ya
existe y contiene `users`, `roles`, `permissions`, `role_permissions`,
`user_roles`, `events` y `event_invitations`. **Léelo antes de escribir nada** y
respeta su estilo: cabeceras de sección comentadas, `CREATE TABLE IF NOT EXISTS`,
comentarios en español sin tildes (el archivo evita tildes a propósito).

### 1. Lo que hay que añadir, al final y en una sección propia

```sql
-- ---------------------------------------------------------------------
-- 9. MODULO D: habitos y registro diario  (Ana Cusi)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS habits (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    habit_type   TEXT    NOT NULL DEFAULT 'general',
    target_value REAL    DEFAULT 1,
    unit         TEXT    DEFAULT 'vez',      -- 'horas' | 'minutos' | 'vasos' | 'vez'
    is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (habit_type IN ('dieta','ejercicio','relajacion','sueno','general')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS habit_logs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    log_date TEXT    NOT NULL,               -- 'YYYY-MM-DD'
    value    REAL    DEFAULT 0,
    done     INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    UNIQUE (habit_id, log_date),             -- idempotencia del registro (TC-34)
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_habits_user     ON habits(user_id);
CREATE INDEX IF NOT EXISTS ix_habit_logs_date ON habit_logs(habit_id, log_date);
```

### 2. Explícame en el mismo mensaje, en dos líneas cada una:

- Por qué `UNIQUE (habit_id, log_date)` es lo que hace posible corregir el
  registro de hoy sin crear una segunda fila (TC-34), y por qué eso **no** se
  puede garantizar solo con un `if` en Python.
- Por qué el tipo `sueno` va **sin tilde** en la base de datos y con "Sueño" en
  pantalla.
- Qué pasa exactamente con las filas de `habit_logs` cuando se borra el usuario
  dueño del hábito, y de qué depende que ese `ON DELETE CASCADE` funcione de
  verdad en SQLite.

### 3. Verificación que quiero poder ejecutar

Dame los comandos exactos (no un script nuevo, no una dependencia nueva) para
comprobar en la base local que:

1. Las dos tablas existen con sus columnas.
2. Insertar dos veces el mismo `(habit_id, log_date)` **falla** con
   `IntegrityError`, y el `INSERT … ON CONFLICT DO UPDATE` en cambio actualiza.
3. `habit_type = 'sueño'` (con tilde) es rechazado por el `CHECK`.

### 4. Lo que NO debes hacer

- **No toques la tabla `tasks`.** Es del Módulo B (Lucero) y del dueño del
  esquema (Jose). Aunque veas que le falta `user_id`, no es tu archivo hoy.
- No crees un `schema_v3.sql` ni un sistema de migraciones. El archivo es
  estrictamente aditivo y `CREATE TABLE IF NOT EXISTS` lo hace idempotente.
- No añadas columnas "por si acaso" (`notes`, `reminder_time`, `streak_cache`).
  Una racha guardada en columna es una racha que se queda desincronizada.

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Metió `ALTER TABLE` o un script de migración?** No hace falta: la base se
   crea con `IF NOT EXISTS` y `init_db()` la reejecuta sin daño.
2. **¿Puso `streak` como columna de `habits`?** Recházalo. La racha se **calcula**
   desde `habit_logs`; cacheada se desincroniza en cuanto alguien corrige un día
   pasado.
3. **¿Se le olvidó el `UNIQUE (habit_id, log_date)`?** Es el corazón del TC-34.
4. **¿Escribió `sueño` con tilde en el `CHECK`?** Rompe la codificación en
   PythonAnywhere y hace que el `CHECK` nunca coincida con lo que envía el
   formulario.
5. **¿Propuso guardar la fecha como `TIMESTAMP` o `DATE`?** SQLite no tiene tipo
   fecha: es `TEXT` en ISO `YYYY-MM-DD`, que además ordena y compara bien como
   cadena.
6. **¿Cambió algo por encima de la línea de tu sección?** Compara con
   `git diff`: tu cambio debe ser **solo añadidos al final**.

---

## ✅ Verificación del paso

```bash
python seed.py
sqlite3 vibe_planner.db ".schema habits"
sqlite3 vibe_planner.db ".schema habit_logs"
```

- [ ] `python seed.py` corre sin error y sigue diciendo "24 permisos sembrados"
- [ ] `.schema habits` muestra el `CHECK` de los cinco tipos
- [ ] `.schema habit_logs` muestra `UNIQUE (habit_id, log_date)`
- [ ] `git diff schema_v2.sql` muestra **solo** líneas añadidas al final
- [ ] `python test_v2.py` sigue en verde (no rompiste el núcleo)
- [ ] 🤝 Jose ha visto el bloque y está de acuerdo

---

## 🤝 Al cerrar este paso, avisa al equipo

> Añadí `habits` y `habit_logs` al final de `schema_v2.sql` (solo añadidos, nada
> modificado). Jose lo revisó. Ejecuten `python seed.py` después de hacer pull
> para que se creen en su base local.
