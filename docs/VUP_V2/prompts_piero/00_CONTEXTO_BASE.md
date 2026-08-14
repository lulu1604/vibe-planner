# 📌 Contexto base — pegar al inicio de CADA prompt

> Copia todo lo que hay debajo de la línea y pégalo **antes** del prompt del paso.
> Sin este bloque, la IA inventa una arquitectura distinta cada vez: propone
> Flask-SQLAlchemy, application factory, React, o una columna `role` de texto.
> Con este bloque, genera lo que necesitamos a la primera.

---

Estás ayudándome a construir **VibePlanner v2**, un planificador de actividades
multiusuario para un curso universitario. Soy responsable del **Módulo A: el
núcleo de identidad** (cuentas, roles, permisos).

## Stack — congelado, no proponer alternativas

- Python 3.10+ · **Flask 3.0.3** con Blueprints, **sin application factory**
- Jinja2 para plantillas · CSS propio · JavaScript vanilla
- **SQLite3** con el módulo `sqlite3` de la librería estándar. **Sin ORM**, sin
  SQLAlchemy, sin Alembic
- Contraseñas con `werkzeug.security` (ya viene con Flask)
- Sesiones con la cookie firmada de Flask. **Sin Flask-Login**
- Despliegue en **PythonAnywhere free tier** (sin red saliente, sin SMTP)
- `requirements.txt` tiene **una sola línea**: `Flask==3.0.3`

## El modelo de permisos — la decisión que gobierna todo

Los roles son **agregativos**: un usuario puede llevar varios roles a la vez y sus
permisos efectivos son la **unión** de los permisos de todos ellos.

```
permisos_efectivos(usuario) = ⋃ permisos(rol)   para cada rol asignado
```

Por eso **el administrador es también un usuario normal**: tiene los roles
`usuario` y `admin` a la vez, planifica su día y administra el sistema con la
misma cuenta.

Esto se modela con cinco tablas: `users`, `roles`, `permissions` y las dos tablas
puente `role_permissions` y `user_roles`. **Nunca** una columna `role` de texto en
`users`: eso haría imposible el requisito.

**En esta versión hay exactamente dos roles:** `usuario` y `admin`.

## Política de cuentas

| Vía | Quién | Roles que otorga |
|---|---|---|
| Registro público `/register` | Cualquier visitante | `usuario` — **siempre, sin excepción** |
| Alta administrativa `/admin/usuarios` | Quien tenga `usuario.crear` | Cualquier combinación |
| Semilla `seed.py` | Una vez, al desplegar | El admin inicial (`usuario` + `admin`) |

**No existe registro público de administrador** y **no existe** un flujo de
"solicitar permisos de admin".

## Reglas que el código debe respetar SIEMPRE

1. La instancia de Flask se llama **exactamente `app`** a nivel de módulo en
   `app.py`. PythonAnywhere hace `from app import app`.
2. **Toda** consulta que devuelva datos de un usuario lleva `user_id` **dentro del
   `WHERE`**. Filtrar en Python después de traer las filas no cuenta.
3. **La regla de las dos llaves:** el decorador comprueba el **permiso**; el
   repositorio comprueba la **propiedad** del registro. Hacen falta las dos. Si el
   registro no es del usuario, se responde **404**, no 403 — un 403 confirmaría
   que ese id existe.
4. Los decoradores comprueban **permisos** (`@requires("usuario.listar")`), nunca
   nombres de rol. Nada de `@admin_required`.
5. El `user_id` sale **siempre** de la sesión, jamás del formulario.
6. En la sesión se guarda **solo el id**. Los permisos se resuelven en cada
   petición y se cachean en `flask.g`, nunca en la cookie: si vivieran ahí,
   quitarle un rol a alguien no tendría efecto hasta que cerrara sesión.
7. Todo el SQL va parametrizado con `?`. Cero concatenación de cadenas.
8. Las contraseñas nunca se guardan, imprimen ni registran en claro.
9. El `SECRET_KEY` sale de una variable de entorno, con respaldo solo para
   desarrollo local.
10. Las plantillas no contienen lógica de negocio. Ningún cálculo dentro de `{{ }}`.
11. Sin APIs externas, sin CDN, sin dependencias nuevas.

## Diseño visual — dos paletas con dos trabajos distintos

> **El azul es la aplicación. El rosa es la importancia.**

```css
/* Identidad */
--navy: #2F4156;   --teal: #567C8D;    --teal-700: #3F5F6E;
--sky:  #C8D9E6;   --beige: #F5EFEB;   --white: #FFFFFF;

/* Importancia (semántica, nunca decorativa) */
--rose: #D7707F;   --rose-700: #9E3B4B;  --blush: #F5D5DA;
--slate: #D8D2D8;  --steel: #9DA3A4;     --taupe: #4C4D53;
```

**Correcciones de contraste que no se pueden saltar** (WCAG AA pide 4.5:1 para
texto normal):

| Color | Sobre blanco | Uso permitido |
|---|---|---|
| `--teal` `#567C8D` | 4.49:1 ❌ | Solo bordes, iconos y rellenos |
| `--teal-700` `#3F5F6E` | 6.90:1 ✅ | Botones, enlaces, texto de acento |
| `--rose` `#D7707F` | 3.20:1 ❌ | Solo rellenos y bordes |
| `--rose-700` `#9E3B4B` | 6.60:1 ✅ | Texto de alta prioridad y errores |
| `--steel` `#9DA3A4` | 2.56:1 ❌ | Solo bordes y elementos desactivados |
| `--taupe` `#4C4D53` | 6.00:1 ✅ | Texto secundario y metadatos |

**Tipografía:** `Inter` (variable) para toda la interfaz y `JetBrains Mono` para
números y puntajes. Ambas auto-alojadas en `static/fonts/`, **nunca por CDN**.
Escala: 12 · 14 · **16 (base)** · 18 · 22 · 28 · 34 px. Los campos de formulario
nunca bajan de 16 px, o iOS hace zoom al enfocarlos.

**Espaciado:** base de 4 px (4, 8, 12, 16, 24, 32, 48). Sin valores intermedios.

**Objetivo táctil mínimo:** 44 × 44 px.

**Mobile-first:** el CSS base es el de móvil y los `@media (min-width: …)` van
añadiendo. Breakpoints: `< 600px` móvil (navegación inferior) · `600–1023px`
tablet (sidebar de iconos) · `≥ 1024px` escritorio (sidebar fijo, contenido máx.
1200 px).

Todos los valores están en `static/css/tokens.css` como variables CSS.
**Ningún hex suelto en el CSS de un componente.**

## Cómo quiero que respondas

- Código completo y ejecutable, no fragmentos con `# ...resto igual`.
- Comentarios **en español** y solo donde expliquen un *porqué*, no un *qué*.
- Si algo de lo que pido te parece un error, **dímelo antes de generar el código**
  y explica el porqué. Prefiero discutirlo a recibir algo que parece correcto.
- No añadas funcionalidad que no pedí. Si se te ocurre algo útil, menciónalo al
  final como sugerencia, fuera del código.

---
