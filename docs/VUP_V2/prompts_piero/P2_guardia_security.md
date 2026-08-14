# P2 — La guardia: `security.py`

**Objetivo:** el único lugar del proyecto donde se decide si una petición pasa.
Menos de 150 líneas que todo el equipo pueda leer enteras.

**Archivos que salen de aquí:** `security.py`

**Tiempo estimado:** 1 hora.

> 🔒 **Este paso es el hito H2.** En cuanto esté en `main`, avisa al grupo: Lucero,
> Jose y Ana están esperando este contrato para arrancar de verdad.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE.md` completo, y después esto:

---

Genera `security.py` para VibePlanner v2. Es el único componente que decide
autorización en todo el proyecto, y su contrato lo van a importar los otros tres
módulos del equipo, así que quiero que sea corto, legible y sin sorpresas.

Ya existe `repo_users.py` con estas funciones disponibles:

```python
repo_users.get_by_id(user_id)       -> dict | None   # incluye is_active
repo_users.get_permissions(user_id) -> set[str]      # unión de todos sus roles
```

### Contrato público — estas firmas se congelan

```python
current_user()                   -> dict | None
current_user_id()                -> int | None
effective_permissions()          -> set[str]
has_permission(code)             -> bool
@login_required
@requires(*permission_codes)
register_template_helpers(app)   -> None
```

### Cómo debe comportarse cada pieza

**`current_user()`** lee `session["user_id"]`, busca el usuario y lo cachea en
`flask.g` — que dura **una sola petición**. Si la cuenta existe pero tiene
`is_active = 0`, limpia la sesión y devuelve `None`: alguien desactivado a mitad
de sesión debe quedar fuera en su siguiente clic, sin esperar a que cierre sesión.

**`effective_permissions()`** devuelve la unión de permisos consultando
`repo_users.get_permissions()`, cacheada también en `flask.g`.

> Explica en un comentario por qué el caché va en `g` y **nunca** en `session`: si
> los permisos vivieran en la cookie, quitarle un rol a alguien no tendría efecto
> hasta que cerrara sesión. La consulta va sobre índices y cuesta menos que ese
> riesgo.

**`@login_required`** — si no hay sesión, guarda el destino en `session["next"]`
(usa `request.full_path` para no perder los parámetros de la URL) y redirige a
`auth.login_route`. Ese `next` es lo que permitirá que un invitado que abre un
link vuelva solo a donde iba después de autenticarse.

**`@requires(*codes)`** — exige **todos** los permisos indicados. Aplica
`@login_required` por dentro para que no haya que poner los dos decoradores. Si
falta alguno, `abort(403)`.

> Muy importante: comprueba **códigos de permiso**, nunca nombres de rol. Nada de
> un `@admin_required`. Si mañana se crea un rol `soporte` con el permiso
> `usuario.listar`, la ruta debe funcionar sin tocar una línea de código.

Usa `functools.wraps` en los dos decoradores, o Flask fallará con rutas duplicadas
al registrar varias vistas con el mismo nombre de función envuelta.

**`register_template_helpers(app)`** expone `current_user` y `has_permission` a
Jinja2 para poder ocultar entradas de menú.

> Añade un comentario dejando claro que **ocultar el botón es cortesía visual, no
> seguridad**: la ruta sigue protegida por `@requires` en el servidor. Quien
> escriba la URL a mano debe recibir un 403 igualmente.

### Lo que NO va en este archivo

Nada de SQL, nada de lógica de negocio, nada de rutas y nada de decisiones sobre
**propiedad** de registros. La propiedad la comprueba cada repositorio con
`user_id` dentro del `WHERE` — es la segunda llave, y no vive aquí.

### Ejemplo de uso que quiero que incluyas como comentario al final

```python
@planner.route("/tasks/<int:task_id>/edit", methods=["POST"])
@requires("planner.editar")                            # 🔑 llave 1: el permiso
def edit_task(task_id):
    task = repo_tasks.get_owned(task_id, current_user_id())   # 🔑 llave 2: propiedad
    if task is None:
        abort(404)   # 404 y no 403: un 403 confirmaría que ese id existe
```

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Los permisos se guardan en `session`?** Si sí, rechaza: rompe la revocación
   inmediata y pone un dato de seguridad en el cliente.
2. **¿Generó un `@admin_required` o compara `role == "admin"`?** Rechaza. Vuelve a
   meter el rol en el código y anula la tabla de permisos entera.
3. **¿Usa `functools.wraps`?** Sin él, Flask ve todas las vistas con el mismo
   nombre y falla al registrar la segunda.
4. **¿Comprueba `is_active`?** Si no, una cuenta desactivada sigue navegando con
   su sesión abierta hasta que la cierre.
5. **¿`@requires` incluye `@login_required` por dentro?** Si no, una ruta sin
   sesión daría 403 en vez de mandar al login, y el usuario no sabría qué hacer.
6. **¿Guarda `request.full_path` o solo `request.path`?** Con `path` se pierden
   los parámetros de la URL al volver del login.

---

## ✅ Verificación del paso

Todavía no hay interfaz, así que se prueba desde la consola de Python:

```python
from app import app          # o crea un app mínimo si aún no existe app.py
import repo_users

with app.test_request_context():
    from flask import session
    admin = repo_users.get_by_username("admin")
    session["user_id"] = admin["id"]

    import security
    perms = security.effective_permissions()
    print(len(perms), "permisos efectivos")
    assert "planner.ver"   in perms   # viene del rol usuario
    assert "usuario.listar" in perms  # viene del rol admin
    print("OK: los roles agregativos funcionan")
```

- [ ] Un usuario con dos roles devuelve la unión de ambos conjuntos
- [ ] Un usuario solo con `usuario` **no** tiene `usuario.listar`
- [ ] `current_user()` devuelve `None` si la cuenta está desactivada
- [ ] `@requires` con un permiso ausente responde 403
- [ ] `security.py` no contiene ni una sola sentencia SQL
- [ ] El archivo cabe en una pantalla y media: si pasa de ~150 líneas, algo que no
      es autorización se coló dentro

---

## 🔒 Al cerrar este paso

1. `git push` y merge a `main`.
2. **Escribe al grupo** con el contrato exacto:

> Ya está `security.py` en `main`. Lo que pueden usar:
> ```python
> from security import current_user, current_user_id, login_required, requires, has_permission
> ```
> `@requires("codigo.permiso")` protege la ruta · `current_user_id()` es el filtro
> que va **dentro del WHERE** de sus consultas. Si el registro no es del usuario,
> respondan 404, no 403. Los permisos disponibles están en `seed.py`; si necesitan
> uno nuevo, díganmelo y lo siembro.
