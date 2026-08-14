# 🧱 MÓDULO A — Núcleo: cuentas, roles y permisos

**Dueño:** Piero Calderón
**Historias:** US5 (registro/login) · US6 (permisos agregativos) · US7 (gestión de usuarios)
**Prioridad:** 🔴 **MÁXIMA — bloquea a los otros tres módulos**
**Alcance v2.1:** solo dos roles — `usuario` y `admin`. El rol `lider` pasó al backlog v3.
**Plan de trabajo paso a paso y prompts:** `docs/VUP_V2/prompts_piero/` *(carpeta personal, en .gitignore)*

> Este módulo es el esqueleto. Mientras `security.py` y `schema_v2.sql` no estén
> en `main`, B, C y D maquetan a ciegas y no pueden probar nada de verdad. Todo lo
> demás del proyecto empieza cuando este archivo se cierra.

---

## 🎯 Qué construyes

Un sistema de identidad con **roles agregativos**: un usuario puede llevar varios
roles a la vez y sus permisos son la **unión** de todos ellos. Por eso el
administrador es también un usuario normal — planifica su día y administra el
sistema con la misma cuenta.

**La decisión que gobierna todo:** el rol no es una categoría a la que perteneces,
es una **bolsa de permisos que cargas**.

```
permisos_efectivos(usuario) = ⋃ permisos(rol)   para cada rol asignado
```

---

## 📁 Archivos que te pertenecen

| Archivo | Qué contiene |
|---|---|
| `schema_v2.sql` | Esquema completo. **Coordinado con Jose**, que es el dueño único del esquema |
| `database.py` | Conexión por petición, `init_db()`, PRAGMAs |
| `repo_users.py` | Único componente que toca `users`, `roles`, `permissions`, `role_permissions`, `user_roles` |
| `security.py` | `current_user()`, `effective_permissions()`, `@login_required`, `@requires()` |
| `auth.py` | Blueprint: `/register`, `/login`, `/logout` |
| `admin.py` | Blueprint: `/admin/usuarios`, `/admin/metricas` |
| `seed.py` | Catálogo de permisos, roles y administrador semilla |
| `migrate_v1_to_v2.py` | Migración de bases v1 existentes |
| `app.py` | Ensamblado: crea `app`, registra blueprints, manejadores 403/404 |
| `config.py` | `SECRET_KEY`, constantes |
| `templates/auth/`, `templates/admin/`, `templates/errors/` | Sus vistas |

**El código completo y listo para ejecutar está en**
`docs/VUP_V2/05_Construction_II.md` §§ 1–10.

---

## 📋 Pasos, en orden

### 1. Esquema (`schema_v2.sql`)
Aplica primero los cuatro arreglos de `REVISION_BD_ESCALABILIDAD.md`
(H1 `COLLATE NOCASE`, H2 paginación, H3 `updated_at`, H4 `ON CONFLICT`): cuestan
media hora ahora y una migración coordinada después.

Las 10 tablas con sus `FOREIGN KEY`, sus `CHECK` y sus índices. Copia el bloque
de Construction II § 1 tal cual. **Acuerda con Jose** el día en que todos borran
su `vibe_planner.db` local.

### 2. Conexión (`database.py`)
Tres PRAGMAs que **no son persistentes** y hay que poner en cada conexión:
`foreign_keys = ON` (sin él SQLite **ignora** las claves foráneas silenciosamente),
`journal_mode = WAL` (lecturas concurrentes, riesgo R8) y `timeout = 10`.

### 3. Repositorio de identidad (`repo_users.py`)
La consulta que **es** el requisito central:

```sql
SELECT DISTINCT p.code
FROM   user_roles       ur
JOIN   role_permissions rp ON rp.role_id = ur.role_id
JOIN   permissions      p  ON p.id       = rp.permission_id
WHERE  ur.user_id = ?;
```

`create_user()` inserta la cuenta **y** sus roles en la **misma transacción**: una
cuenta sin roles es una cuenta sin ningún permiso, imposible de usar.

### 4. Guardia (`security.py`) 🔒 **CONTRATO CONGELADO EN H2**
Lo que B, C y D van a importar. Una vez publicado, cambiar una firma exige avisar
al grupo:

```python
current_user()        -> dict | None
current_user_id()     -> int  | None
@login_required
@requires("permiso.codigo")
has_permission("permiso.codigo") -> bool
```

Los permisos se cachean en `flask.g` (dura una petición), **jamás en la sesión**:
si vivieran en la cookie, quitarle un rol a alguien no tendría efecto hasta que
cerrara sesión (TC-09).

### 5. Autenticación (`auth.py`)
```python
PUBLIC_REGISTRATION_ROLES = ["usuario"]   # constante del servidor, NO del formulario
```
Un `role=admin` enviado desde DevTools o con `curl` se ignora por completo. Es
**TC-03**, uno de los tres casos que bloquean el release.

El mensaje de login fallido es **idéntico** para usuario inexistente y contraseña
incorrecta. Si difieren, se pueden enumerar las cuentas válidas.

### 6. Semilla (`seed.py`)
23 permisos, **2 roles** (`usuario` y `admin`) y el administrador inicial. **Idempotente:** cada vez que un
módulo añade un permiso, se vuelve a ejecutar y queda sembrado. Un permiso que
existe en un decorador pero no en la tabla es un 403 permanente que nadie sabrá
explicar.

Ojo con los roles agregativos en la semilla: `admin` **no repite** los permisos de
`usuario`. Se suman solos porque el administrador tiene los dos roles.

### 7. Panel de administración (`admin.py`)
Listar, crear, editar, desactivar y asignar roles. Aquí **sí** se leen los roles
del formulario, porque quien llega a esa línea ya demostró tener `usuario.crear` —
es exactamente lo contrario del registro público.

Guarda **TC-10**: el sistema nunca se queda sin administradores activos.

### 8. Ensamblado (`app.py`)
La instancia se llama **exactamente `app`** a nivel de módulo. PythonAnywhere hace
`from app import app`. Sin application factory.

### 9. Migración (`migrate_v1_to_v2.py`)
Mapea `pending → todo`, `in_progress → ongoing`, `completed → done` y adopta las
tareas huérfanas de v1.

---

## 🕳️ Trampas concretas de este módulo

1. **`PRAGMA foreign_keys = ON` en cada conexión.** No es persistente. Sin él, las
   claves foráneas se ignoran **en silencio**: borras un usuario y sus tareas
   quedan apuntando a un id que ya no existe.
2. **Nunca guardes permisos en la sesión.** Rompe TC-09 y pone un dato de
   seguridad en el cliente.
3. **`@requires()` comprueba permisos, nunca nombres de rol.** Un `@admin_required`
   vuelve a meter el rol en el código y anula la tabla entera: si mañana se crea
   el rol `soporte` con ese permiso, quedaría fuera.
4. **Ocultar el botón no es seguridad.** `has_permission()` en Jinja2 es cortesía
   visual; la ruta sigue protegida por `@requires` en el servidor.
5. **404, no 403, cuando el registro no es tuyo.** Un 403 confirma que ese id
   existe y permite enumerar los datos de los demás.
6. **El `SECRET_KEY` de producción no entra al repositorio.** Lo que llega al
   historial de Git es público para siempre, aunque después lo borres.

---

## ✅ Listo cuando

- [ ] `python seed.py` crea 23 permisos, 2 roles y el administrador
- [ ] Puedo registrarme, entrar, salir y volver a entrar
- [ ] `curl` con `role=admin` en el registro **no** otorga nada (**TC-03**)
- [ ] La cuenta `admin` abre `/planner` y `/admin/usuarios` en la misma sesión (**TC-06**)
- [ ] Una cuenta sin permiso recibe 403 real del servidor (**TC-07**)
- [ ] Quitar un rol surte efecto **sin cerrar sesión** (**TC-09**)
- [ ] Desactivar una cuenta conserva sus tareas y eventos (**TC-05**)
- [ ] No puedo dejar el sistema sin administradores (**TC-10**)
- [ ] `python test_v2.py` ejecuta el bloque del núcleo en verde
- [ ] 🔒 **El contrato de `security.py` está publicado en `main` y anunciado al grupo**

Este último punto es el hito **H2**: hasta que no ocurra, el resto del equipo está
esperándote.

---

## 🤝 Lo que entregas al resto del equipo

```python
from security import current_user, current_user_id, login_required, requires

@planner.route("/mis-cosas")
@requires("planner.ver")          # llave 1: el permiso
def mis_cosas():
    user_id = current_user_id()   # llave 2: el filtro que va DENTRO del WHERE
    ...
```

Y en las plantillas:

```jinja
{% if has_permission('usuario.listar') %}
  <a href="{{ url_for('admin.list_users_route') }}">Administración</a>
{% endif %}
```
