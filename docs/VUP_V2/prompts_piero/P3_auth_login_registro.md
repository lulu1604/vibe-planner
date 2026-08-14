# P3 — Login, registro y logout (con su interfaz)

**Objetivo:** que una persona pueda registrarse, entrar, salir y volver a entrar,
en pantallas que ya se vean como el producto final.

**Archivos que salen de aquí:** `auth.py` · `app.py` (mínimo) ·
`templates/base_auth.html` · `templates/auth/login.html` ·
`templates/auth/register.html` · `templates/errors/403.html` · `404.html` ·
`static/css/base.css` · `static/css/components.css`

**Tiempo estimado:** 3–4 horas.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE.md` completo, y después esto:

---

Genera la autenticación de VibePlanner v2 **con sus pantallas**. Ya existen
`config.py`, `database.py`, `repo_users.py`, `seed.py` y `security.py` con este
contrato:

```python
repo_users.create_user(data, role_codes, granted_by=None) -> int | None
repo_users.get_by_username(username)                      -> dict | None
repo_users.verify_password(user_row, raw_password)        -> bool
security.current_user()                                   -> dict | None
security.register_template_helpers(app)
```

### 1. `auth.py` — blueprint

Rutas: `GET/POST /register` · `GET/POST /login` · `POST /logout`.

**La regla de oro de este archivo:**

```python
PUBLIC_REGISTRATION_ROLES = ["usuario"]   # constante del servidor, NO del formulario
```

Un `role=admin` enviado desde DevTools o con `curl` debe ignorarse por completo.
Nunca leas un rol del formulario en el registro público.

Comportamiento exigido:

| Situación | Respuesta | Código |
|---|---|---|
| Registro válido | Crea la cuenta, abre sesión, redirige al home | 302 |
| Usuario < 3 caracteres, correo inválido o contraseña < 8 | Vuelve al formulario con los errores **y los datos ya escritos** | 400 |
| Usuario o correo duplicado | "Ese usuario o correo ya está registrado" | 409 |
| Login correcto | Abre sesión y va a `session["next"]` si existe, si no al home | 302 |
| Usuario o contraseña incorrectos | **El mismo mensaje en ambos casos** | 401 |
| Cuenta desactivada | "Tu cuenta está desactivada. Contacta al administrador" | 403 |
| Ya autenticado y abre `/login` o `/register` | Redirige al home | 302 |

> El mensaje idéntico en los dos fallos de login es **deliberado**: si dijera "ese
> usuario no existe", cualquiera podría enumerar las cuentas del sistema. Es el
> único sitio del producto donde la seguridad gana a la claridad.

`session.clear()` antes de `session["user_id"] = ...` en login y registro, para
evitar fijación de sesión — pero **guarda antes** el valor de `next`, o lo pierdes
al limpiar.

`/logout` solo por **POST**, con un formulario. Si fuera GET, cualquier `<img
src="/logout">` en otra página cerraría la sesión del usuario.

### 2. `app.py` mínimo

Crea `app` a nivel de módulo, carga la configuración, llama a
`database.init_db()`, registra el blueprint `auth`, llama a
`security.register_template_helpers(app)`, registra `teardown_appcontext` y los
manejadores de 403 y 404. Nada más: la lógica vive en los blueprints.

### 3. Las plantillas

**`base_auth.html`** — shell mínimo para login y registro: fondo `--beige`, la
tarjeta centrada sobre `--white`, el logotipo de VibePlanner arriba. Carga los
tres CSS en orden: `tokens.css`, `base.css`, `components.css`.

**`login.html`** y **`register.html`** deben cumplir esto, que no es opcional:

- `<label for="...">` **visible encima** de cada campo. Nunca solo `placeholder`:
  el placeholder desaparece al escribir y el usuario ya no sabe qué campo es.
- `autocomplete` correcto: `username`, `current-password` en login,
  `new-password` y `email` en registro. Le ahorra escribir al usuario.
- `autofocus` en el primer campo.
- Los campos a **16 px como mínimo**: por debajo, iOS hace zoom al enfocarlos.
- Los requisitos de la contraseña **visibles antes de escribir**, como texto de
  ayuda debajo del campo: *"Mínimo 8 caracteres. Se guarda cifrada."* Prevenir el
  error es mejor que explicarlo.
- Los errores **debajo de su campo**, en `--rose-700`, con un icono además del
  color, y el campo marcado con `aria-invalid="true"`.
- Al fallar, el formulario **conserva lo ya escrito** menos la contraseña. Volver
  a teclear todo es la forma más rápida de perder a un usuario.
- Botón primario a ancho completo, `min-height: 44px`, con `--teal-700` y texto
  blanco.
- Enlace cruzado entre las dos pantallas: "¿No tienes cuenta? Crea una" y "¿Ya
  tienes cuenta? Inicia sesión".
- Al enviar, el botón se deshabilita y cambia a "Entrando…" — así el usuario ve
  que pasó algo y no envía dos veces.

**`errors/403.html`** — "No tienes permiso para esta sección. Si crees que
deberías tenerlo, pídeselo a un administrador." Con un enlace de vuelta al home.
Nunca la palabra "Forbidden" ni un código HTTP suelto.

**`errors/404.html`** — "No encontramos esa página", con enlace al home.

### 4. `base.css` y `components.css`

`base.css`: reset, `@font-face` de las dos fuentes auto-alojadas, tipografía
base, y el layout responsive mobile-first con los tres breakpoints.

`components.css`: `.btn` (primario, secundario, fantasma, destructivo), `.field`
(label + input + ayuda + error), `.card`, `.alert` y `.badge`.

Todo saliendo de las variables de `tokens.css`. **Ningún hex suelto.**

Y el foco, que se olvida siempre:

```css
:focus-visible { outline: 3px solid var(--focus-ring); outline-offset: 2px; }
```

Nunca `outline: none` sin sustituto: quien navega con teclado necesita ver dónde
está.

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | El botón cambia a "Entrando…" al enviar |
| **H2** Idioma del usuario | "Tu cuenta está desactivada", no "403 Forbidden" |
| **H3** Control y libertad | Enlace cruzado entre login y registro |
| **H4** Consistencia | Los mismos `.btn` y `.field` en las dos pantallas |
| **H5** Prevención de errores | Requisitos de contraseña visibles **antes** de escribir |
| **H6** Reconocer > recordar | Etiqueta visible, no solo placeholder |
| **H7** Eficiencia | `autofocus`, `autocomplete`, `Enter` envía |
| **H8** Minimalismo | El login es un formulario, no un folleto del producto |
| **H9** Recuperación de errores | Error debajo del campo, con icono, sin perder lo escrito |
| **H10** Ayuda | Texto de ayuda al lado del campo que lo necesita |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿`/register` lee algún rol del formulario?** Si aparece
   `request.form.get("role")`, rechaza inmediatamente. Es TC-03, uno de los tres
   casos que bloquean el release.
2. **¿Los dos mensajes de login fallido son idénticos?** Compáralos carácter por
   carácter. La IA tiende a "mejorar" la UX con "ese usuario no existe".
3. **¿`/logout` acepta GET?** Debe ser solo POST.
4. **¿Se pierde `next` al hacer `session.clear()`?** Guárdalo en una variable
   antes de limpiar.
5. **¿El formulario conserva los datos al fallar?** Si vuelve vacío, pídelo otra vez.
6. **¿Hay `<label for>` en todos los campos?** O solo placeholders.
7. **¿Algún hex suelto en el CSS?** Todo sale de `tokens.css`.
8. **¿Usó `--teal` `#567C8D` para texto?** No cumple contraste. Debe ser
   `--teal-700`.
9. **¿Quitó el `outline` del foco sin poner otro?** Rechaza.
10. **¿Metió Flask-Login o Flask-WTF?** `requirements.txt` sigue con una línea.

---

## ✅ Verificación del paso

```bash
python app.py
```

Manualmente:
- [ ] Me registro, la sesión se abre sola y llego al home
- [ ] Cierro sesión y vuelvo a entrar
- [ ] Usuario duplicado → 409 con mensaje claro
- [ ] Contraseña de 5 caracteres → 400 y **conserva** usuario y correo escritos
- [ ] Contraseña incorrecta y usuario inexistente dan **el mismo** mensaje
- [ ] Una cuenta desactivada (`UPDATE users SET is_active=0`) no puede entrar
- [ ] Recorro login y registro entero **solo con el teclado**, y siempre veo el foco
- [ ] A 360 px no hay scroll horizontal y los campos no hacen zoom en móvil

El de seguridad, sin navegador:

```bash
curl -X POST http://localhost:5000/register \
  -d "username=atacante&email=a@b.pe&password=Hack2026!&role=admin&roles=admin"

sqlite3 vibe_planner.db "SELECT r.code FROM users u JOIN user_roles ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.username='atacante';"
```

Debe devolver **una sola fila: `usuario`**. Si aparece `admin`, para todo y
arréglalo antes de seguir.

- [ ] **TC-03 en verde** ⚠️
