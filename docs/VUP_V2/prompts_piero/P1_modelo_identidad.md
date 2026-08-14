# P1 — Modelo de identidad: esquema, conexión, repositorio y semilla

**Objetivo:** que exista la base de datos con usuarios, roles y permisos
agregativos, sembrada y verificable desde consola. **Sin interfaz todavía.**

**Archivos que salen de aquí:** `config.py` · `schema_v2.sql` · `database.py` ·
`repo_users.py` · `seed.py`

**Tiempo estimado:** 2–3 horas incluyendo la verificación.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE.md` completo, y después esto:

---

Genera la capa de identidad de VibePlanner v2. Cinco archivos, nada más.

### 1. `config.py`

`SECRET_KEY` desde `os.environ.get("VIBEPLANNER_SECRET", <valor de desarrollo>)`,
`MIN_PASSWORD_LENGTH = 8`, `SESSION_COOKIE_HTTPONLY = True`,
`SESSION_COOKIE_SAMESITE = "Lax"`.

### 2. `schema_v2.sql`

Cinco tablas para identidad. Diseña pensando en que la base **crezca**:

- **`users`** — `id`, `username` UNIQUE, `email` UNIQUE, `password_hash`,
  `full_name`, `is_active` (por defecto 1), `created_at`, `updated_at`.
  `username` y `email` con `COLLATE NOCASE` en la restricción UNIQUE: `Piero` y
  `piero` deben ser la misma cuenta a nivel de base de datos, no solo por una
  normalización que hoy hace el repositorio y mañana alguien olvida.
- **`roles`** — `id`, `code` UNIQUE, `name`, `description`.
- **`permissions`** — `id`, `code` UNIQUE, `module`, `description`.
- **`role_permissions`** — `role_id`, `permission_id`, clave primaria compuesta,
  `FOREIGN KEY … ON DELETE CASCADE` en ambas.
- **`user_roles`** — `user_id`, `role_id`, `granted_by`, `granted_at`, clave
  primaria compuesta `(user_id, role_id)`. `granted_by` con
  `ON DELETE SET NULL`: si se borra el admin que otorgó un rol, el rol no
  desaparece.

Índices: `user_roles(user_id)` y `role_permissions(role_id)`. Son las columnas por
las que filtra la consulta de permisos, que se ejecuta en **cada petición**.

Nada de una columna `role` en `users`.

### 3. `database.py`

Solo conexión y arranque. **Ningún SQL de negocio.**

- `get_db()` — una conexión por petición, guardada en `flask.g`. Nunca una
  conexión global compartida.
- `close_db()` — la cierra.
- `init_db()` — lee `schema_v2.sql` y lo ejecuta. Idempotente.
- `raw_connection()` — conexión fuera del contexto Flask, para `seed.py` y tests.
- En **cada** conexión: `row_factory = sqlite3.Row`,
  `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`, `timeout = 10.0`.

Comenta por qué los PRAGMAs van en cada conexión y no en el `.sql`.

### 4. `repo_users.py`

Único componente autorizado a tocar las cinco tablas. Firmas exactas:

```python
create_user(data, role_codes, granted_by=None)  -> int | None
get_by_username(username)                       -> dict | None
get_by_id(user_id)                              -> dict | None
list_users(search=None, limit=50, offset=0)     -> list[dict]
count_users(search=None)                        -> int
get_permissions(user_id)                        -> set[str]
get_roles(user_id)                              -> list[dict]
assign_roles(user_id, role_codes, granted_by)   -> bool
set_active(user_id, is_active)                  -> bool
set_password(user_id, raw_password)             -> bool
verify_password(user_row, raw_password)         -> bool
count_admins()                                  -> int
```

**`get_permissions()` es el corazón del sistema.** Una sola consulta:

```sql
SELECT DISTINCT p.code
FROM   user_roles       ur
JOIN   role_permissions rp ON rp.role_id = ur.role_id
JOIN   permissions      p  ON p.id       = rp.permission_id
WHERE  ur.user_id = ?;
```

Devuelve un `set`. El `DISTINCT` es lo que elimina los permisos que dos roles
comparten.

Detalles que importan:

- `create_user()` inserta la cuenta **y** sus roles en la **misma transacción**.
  Una cuenta sin roles no tiene ningún permiso: es una cuenta rota. Si salta
  `sqlite3.IntegrityError` (usuario o correo duplicado), haz `rollback` y
  devuelve `None` — no dejes que la excepción suba al controlador.
- `username` y `email` se normalizan a minúsculas y sin espacios antes de guardar.
- `list_users()` acepta búsqueda y **paginación**. Sin `LIMIT` funciona con 10
  cuentas y se cae con 10 000: la paginación se pone ahora, cuando cuesta una
  línea.
- `count_admins()` cuenta administradores **activos** — un admin desactivado no
  puede administrar nada.
- Nunca escribas la contraseña en un `print` ni en un log, ni siquiera al depurar.

### 5. `seed.py`

Idempotente: ejecutarlo dos veces no debe duplicar ni romper nada. Usa
`ON CONFLICT(code) DO UPDATE` para permisos y roles.

**Exactamente dos roles.** Ojo con lo agregativo: `admin` **no repite** los
permisos de `usuario`, porque el administrador tendrá los dos roles y los permisos
se suman solos.

```python
ROLES = {
  "usuario": [
    "perfil.ver", "perfil.editar",
    "planner.ver", "planner.crear", "planner.editar", "planner.eliminar",
    "kanban.ver", "kanban.mover",
    "evento.ver", "evento.crear", "evento.editar", "evento.eliminar",
    "evento.invitar",
    "habito.ver", "habito.crear", "habito.registrar",
    "metrica.propia.ver",
  ],
  "admin": [
    "usuario.listar", "usuario.crear", "usuario.editar",
    "usuario.desactivar", "rol.asignar", "metrica.sistema.ver",
  ],
}
```

Cada permiso lleva también su `module` y una `description` en español, porque se
van a mostrar en la interfaz de asignación de roles.

Y crea el **administrador semilla** con **los dos roles** (`usuario` + `admin`),
tomando usuario, correo y contraseña de variables de entorno con valores de
respaldo. Si la contraseña es la de respaldo, imprime un aviso claro de que hay
que cambiarla antes de desplegar.

Al terminar, imprime un resumen: cuántos permisos, cuántos roles y si el admin se
creó o ya existía.

### Verificación que quiero que incluyas

Un bloque `if __name__ == "__main__":` en `seed.py` que, después de sembrar,
imprima los permisos efectivos del administrador y confirme que contiene tanto
`planner.ver` (que viene del rol `usuario`) como `usuario.listar` (que viene del
rol `admin`). Ese print es la demostración de que los roles agregativos funcionan.

---

## 🕳️ Revisa esto antes de aceptar el código

La IA falla en estos puntos concretos. Búscalos uno por uno:

1. **¿`PRAGMA foreign_keys = ON` está en cada conexión?** No es persistente en
   SQLite. Sin él, las claves foráneas se ignoran **en silencio**: borras un
   usuario y sus roles quedan apuntando a un id que ya no existe.
2. **¿Aparece una columna `role` en `users`?** Si sí, rechaza y repite el prompt:
   es el error que la IA propone con más frecuencia y rompe todo el requisito.
3. **¿`get_permissions()` usa `DISTINCT`?** Sin él, un usuario con dos roles que
   compartan permisos los recibe duplicados.
4. **¿`create_user()` maneja `IntegrityError` con `rollback`?** Sin rollback, la
   conexión queda en un estado sucio y la siguiente operación falla sin motivo
   aparente.
5. **¿`seed.py` es realmente idempotente?** Ejecútalo dos veces seguidas. Si la
   segunda falla o duplica filas, no lo es.
6. **¿`admin` repite los permisos de `usuario`?** Si los repite, no entendió lo
   agregativo. Debe aportar solo lo suyo.
7. **¿`list_users()` tiene `LIMIT`?** Si devuelve todo sin paginar, pídelo.
8. **¿Usa `INSERT OR IGNORE`?** Funciona, pero es sintaxis solo de SQLite.
   Prefiere `ON CONFLICT … DO NOTHING`, que es portable si algún día migran a
   PostgreSQL.

---

## ✅ Verificación del paso

```bash
python seed.py
python seed.py          # dos veces: debe salir igual, sin duplicar
```

Y una comprobación directa contra la base:

```bash
sqlite3 vibe_planner.db "SELECT COUNT(*) FROM permissions;"     # 23
sqlite3 vibe_planner.db "SELECT code FROM roles;"               # usuario, admin
sqlite3 vibe_planner.db "SELECT u.username, r.code FROM users u JOIN user_roles ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id;"
```

La última consulta debe devolver **dos filas** para la cuenta admin:
`admin|usuario` y `admin|admin`. **Eso es lo agregativo, funcionando.**

- [ ] `python seed.py` crea 24 permisos y 2 roles
- [ ] Ejecutarlo dos veces no duplica nada
- [ ] La cuenta admin tiene dos filas en `user_roles`
- [ ] Sus permisos efectivos incluyen `planner.ver` **y** `usuario.listar`
- [ ] `password_hash` no contiene la contraseña en claro
- [ ] Insertar un `user_roles` con un `role_id` inexistente **falla** (prueba de
      que las claves foráneas están activas)

---

## 📝 Anota en `_bitacora.md`

- Qué propuso la IA que rechazaste, y por qué.
- Si intentó meter SQLAlchemy o una columna `role`.
- El código exacto que generó mal (te sirve como evidencia para la rúbrica).
