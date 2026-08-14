# P5 — Gestión de usuarios (panel de administración)

**Objetivo:** que el administrador liste, cree, edite, desactive y asigne roles,
con las protecciones que impiden dejar el sistema sin administradores o dañar
datos sin querer.

**Archivos que salen de aquí:** `admin.py` · `templates/admin/usuarios.html` ·
`templates/admin/_form_usuario.html` · `templates/admin/_modal_roles.html`

**Tiempo estimado:** 3–4 horas.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE.md` completo, y después esto:

---

Genera el panel de gestión de usuarios de VibePlanner v2. Ya existen
`security.py`, `repo_users.py` y el shell `base.html`.

Recuerda el contrato disponible:

```python
repo_users.list_users(search=None, limit=50, offset=0) -> list[dict]  # con 'roles'
repo_users.count_users(search=None)                    -> int
repo_users.create_user(data, role_codes, granted_by)   -> int | None
repo_users.get_by_id(user_id)                          -> dict | None
repo_users.get_roles(user_id)                          -> list[dict]
repo_users.assign_roles(user_id, role_codes, granted_by) -> bool
repo_users.set_active(user_id, is_active)              -> bool
repo_users.set_password(user_id, raw_password)         -> bool
repo_users.count_admins()                              -> int
```

### 1. `admin.py` — blueprint con `url_prefix="/admin"`

| Ruta | Método | Permiso |
|---|---|---|
| `/admin/usuarios` | GET | `usuario.listar` |
| `/admin/usuarios` | POST | `usuario.crear` |
| `/admin/usuarios/<id>/roles` | POST | `rol.asignar` |
| `/admin/usuarios/<id>/estado` | POST | `usuario.desactivar` |
| `/admin/usuarios/<id>/password` | POST | `usuario.editar` |

Cada una con `@requires("…")`. **Un permiso distinto por acción**: listar no
implica crear, y crear no implica asignar roles.

**Reglas de negocio que el código debe hacer cumplir:**

1. **El sistema nunca se queda sin administradores activos.** Si la operación
   dejaría `count_admins()` en cero — quitarse el rol `admin` a uno mismo,
   desactivar al último admin — se rechaza con "No puedes dejar el sistema sin
   administradores". Escribe una función auxiliar `_dejaria_sin_admins(user_id,
   nuevos_roles)` y úsala en las dos rutas: es la misma regla en dos sitios y
   duplicarla es cómo se desincronizan.
2. **`usuario` siempre presente.** Al guardar los roles, si el formulario no lo
   trae, añádelo. Todos son usuarios; los demás roles **se suman** encima. Un
   administrador sin el rol `usuario` no podría ver su propio planner.
3. **Aquí sí se leen los roles del formulario**, porque quien llega a esta línea
   ya demostró tener el permiso. Es exactamente lo contrario del registro público.
   Aun así, valida contra la lista blanca `["usuario", "admin"]`: nunca insertes
   un código de rol que venga del navegador sin comprobar.
4. **Desactivar no es borrar.** No existe ninguna ruta de borrado. Las tareas y
   eventos de una cuenta desactivada siguen existiendo.
5. **Restablecer contraseña**, no verla. El administrador asigna una nueva; nunca
   se muestra ni se recupera la anterior.

### 2. `usuarios.html` — el listado

Extiende `base.html`. Una tabla con: usuario, nombre, correo, **roles como
insignias**, estado y acciones.

Requisitos de interfaz:

- **Buscador** por usuario, nombre o correo, y **paginación** cuando pase de 50
  cuentas.
- **Los roles como insignias con su nombre legible**: `[Usuario]` `[Administrador]`,
  no `usuario` / `admin`.
- **El estado con texto además de color**: "Activa" en `--sky` con texto navy,
  "Desactivada" en `--slate` con texto `--taupe`. En escala de grises se tiene que
  seguir distinguiendo.
- **Tu propia fila marcada** con un "(tú)" al lado del nombre. Evita que el
  administrador se desactive a sí mismo por descuido.
- **Estado vacío**: "Aún no hay más cuentas que la tuya. Crea la primera con el
  botón de arriba."
- **En móvil la tabla se convierte en tarjetas.** Una tabla de 6 columnas a 360 px
  es ilegible; cada cuenta pasa a ser una tarjeta con sus datos apilados.
- **Un solo botón primario**: "Nueva cuenta". Las acciones de fila son
  secundarias, y "Desactivar" es destructiva (texto `--rose-700`, borde `--rose`).

### 3. `_form_usuario.html` — alta de cuenta

Campos: usuario, nombre completo, correo, contraseña, y los roles como
**casillas con su descripción visible**:

```
☑ Usuario          Usa la aplicación: su planner, calendario y hábitos
☐ Administrador    Gestiona cuentas y ve las métricas del sistema
```

La casilla "Usuario" viene marcada y **deshabilitada**, con una nota que explique
por qué: *"Todas las cuentas son usuarios. Los demás roles se suman encima."*
Esa frase enseña el modelo agregativo en el momento en que importa.

> Ojo: un `<input disabled>` no se envía en el formulario. Añade un `<input
> type="hidden" name="roles" value="usuario">` para que llegue igualmente — y de
> todos modos el servidor lo añade por su cuenta.

### 4. `_modal_roles.html` — cambiar roles de una cuenta

Las mismas casillas, con los roles actuales premarcados. El título dice de quién:
"Roles de **ana**". Se cierra con ×, `Escape` y clic fuera. El foco entra al modal
al abrirlo y **vuelve al botón que lo abrió** al cerrarse.

### 5. Confirmación de lo destructivo

Desactivar pide confirmación, y la confirmación **dice qué va a pasar**:

> **¿Desactivar la cuenta de `ana`?**
> No podrá iniciar sesión. **Sus tareas y eventos no se borran** y puedes
> reactivarla cuando quieras.
> [Cancelar] [Desactivar cuenta]

Nada de `confirm()` de JavaScript: un diálogo nativo del navegador bloquea la
página, no se puede estilar y no dice nada útil.

### 6. Mensajes de resultado

Usa `flash()` y muéstralos en `base.html`. Que digan **qué** pasó, no "Guardado":

- "Cuenta `lucero` creada con los roles Usuario y Administrador."
- "Roles de `ana` actualizados: Usuario."
- "Cuenta de `jose` desactivada. Sus datos se conservan."
- "Contraseña de `ana` restablecida."

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | El mensaje dice qué roles quedaron, no "Guardado" |
| **H2** Idioma del usuario | "Administrador", no `admin`; "Desactivada", no `is_active=0` |
| **H3** Control y libertad | Desactivar es reversible; cancelar visible en todo formulario |
| **H5** Prevención de errores | Se impide quedarse sin admins; tu fila marcada con "(tú)" |
| **H6** Reconocer > recordar | Cada rol explica lo que hace, ahí mismo |
| **H8** Minimalismo | Un solo botón primario en la pantalla |
| **H9** Recuperación de errores | La confirmación dice exactamente qué va a pasar |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Existe alguna ruta de borrado de usuario?** No debe haberla. Solo desactivar.
2. **¿La regla de "sin admins" está duplicada en las dos rutas?** Debe ser una
   función auxiliar compartida.
3. **¿Valida los códigos de rol contra una lista blanca?** Si inserta lo que llega
   del formulario sin filtrar, un rol inventado entra a la base.
4. **¿Fuerza el rol `usuario` al guardar?** Sin eso, un admin puede quedarse sin
   acceso a su propio planner.
5. **¿Usa `confirm()` de JavaScript?** Pide un modal propio.
6. **¿La tabla se adapta a móvil?** A 360 px debe convertirse en tarjetas.
7. **¿El estado se distingue solo por color?** Necesita el texto también.
8. **¿Muestra la contraseña o la deja escrita en algún sitio?** Solo restablecer,
   nunca mostrar.
9. **¿`list_users()` se llama sin paginar?** Debe pasar `limit` y `offset`.
10. **¿El modal devuelve el foco al cerrarse?** Se olvida siempre y rompe la
    navegación por teclado.

---

## ✅ Verificación del paso

- [ ] Creo la cuenta `lucero` marcando Usuario + Administrador; el listado muestra
      las dos insignias
- [ ] `lucero` entra y **ve la entrada "Administración"** en su menú
- [ ] Le quito el rol `admin`; **recarga sin cerrar sesión** y recibe 403 (TC-09)
- [ ] Desactivo `jose`; no puede entrar, pero
      `SELECT COUNT(*) FROM tasks WHERE user_id=<jose>` sigue devolviendo lo mismo
- [ ] Intento quitarme `admin` siendo el único → se rechaza con el mensaje correcto
- [ ] Intento desactivarme siendo el único admin → se rechaza igual
- [ ] Restablezco la contraseña de `ana` y ella entra con la nueva
- [ ] Como `piero` (solo `usuario`), `/admin/usuarios` responde **403** (TC-07)
- [ ] La lista se ve como tarjetas a 360 px y como tabla a 1280 px
- [ ] Recorro el modal de roles entero con teclado y el foco vuelve al cerrarlo

**Con este paso cierras las tres historias del Módulo A: US5, US6 y US7.**
