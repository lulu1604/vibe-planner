# 📌 Contexto base de Ana — pegar al inicio de CADA prompt

> Copia todo lo que hay debajo de la línea y pégalo **antes** del prompt del paso.
> Sin este bloque la IA inventa una arquitectura distinta cada vez: propone
> Flask-SQLAlchemy, renombra los bloques de `base.html` y deja las páginas en
> blanco, o escribe el CSS de escritorio primero. Con este bloque genera lo que
> el proyecto ya tiene, a la primera.

---

Estás ayudándome a construir **VibePlanner v2**, un planificador de actividades
multiusuario para un curso universitario. Soy **Ana Cusi** y soy responsable del
**Módulo D: hábitos, métricas y el design system transversal** (US13, US14, US15,
US16). El núcleo de identidad (Módulo A) **ya está construido y en `main`**: no
lo reescribas, consúmelo.

## Stack — congelado, no proponer alternativas

- Python 3.10+ · **Flask 3.0.3** con Blueprints, **sin application factory**
- Jinja2 · CSS propio · JavaScript vanilla
- **SQLite3** con el módulo `sqlite3` de la librería estándar. **Sin ORM**, sin
  SQLAlchemy, sin Alembic, sin migraciones automáticas
- Sesiones con la cookie firmada de Flask. **Sin Flask-Login**
- Despliegue en **PythonAnywhere free tier**
- `requirements.txt` tiene **una sola línea**: `Flask==3.0.3`. No añadas
  dependencias: ni pandas, ni matplotlib, ni Chart.js por CDN

## El modelo de permisos — la decisión que gobierna todo

Los roles son **agregativos**: un usuario lleva varios roles a la vez y sus
permisos efectivos son la **unión** de los de todos ellos.

```
permisos_efectivos(usuario) = ⋃ permisos(rol)   para cada rol asignado
```

Por eso **el administrador es también un usuario normal**: lleva `usuario` y
`admin` a la vez. Los decoradores comprueban **permisos**, nunca nombres de rol.
Nada de `@admin_required` ni de `if 'admin' in roles`.

## Contratos YA CONGELADOS que debes consumir (no reescribir)

### `security.py` — la guardia (dueño: Piero, hito H2)

```python
current_user()            -> dict | None
current_user_id()         -> int  | None
effective_permissions()   -> set[str]
has_permission("codigo")  -> bool
current_roles()           -> list[dict]
@login_required
@requires("codigo", ...)          # 403 si falta el permiso
csrf_token()                      # expuesto a Jinja2
validate_csrf()
```

`security.init_app(app)` **ya valida CSRF en TODO POST** de la aplicación. Por lo
tanto **cada formulario `method="post"` que escribas debe llevar**:

```jinja
<input type="hidden" name="_csrf" value="{{ csrf_token() }}">
```

Si falta, la petición muere con un 400 y el mensaje "Tu sesión caducó…". Es el
fallo número uno al añadir una pantalla nueva a este proyecto.

### `database.py` — la conexión (dueño: Jose)

```python
get_db()          # una conexión por petición (usa flask.g)
raw_connection()  # fuera del ciclo de petición: seed, pruebas
init_db()         # ejecuta el SCHEMA v1 y, si existe, schema_v2.sql
close_db()
```

Los `PRAGMA foreign_keys = ON`, `journal_mode = WAL` y `busy_timeout` ya se
aplican en ambas. **No abras conexiones por tu cuenta con `sqlite3.connect()`.**

### Permisos que ya están sembrados en `seed.py` (no inventes códigos nuevos)

```
habito.ver          habito.crear         habito.registrar
metrica.propia.ver  metrica.sistema.ver
```

Los cinco existen ya en la tabla `permissions`. `habito.*` y `metrica.propia.ver`
son del rol `usuario`; `metrica.sistema.ver` es del rol `admin`. Un permiso que
aparece en un `@requires(...)` pero no en la tabla es un **403 permanente que
nadie sabe explicar**.

### `home.py` — el menú ya tiene reservadas tus entradas

```python
{"clave": "habitos",  "permiso": "habito.ver",         "endpoint": "habitos.lista"}
{"clave": "metricas", "permiso": "metrica.propia.ver", "endpoint": "habitos.metricas"}
```

⚠️ **Consecuencia directa e innegociable:** el blueprint debe llamarse
exactamente `habitos` y sus vistas deben llamarse exactamente `lista` y
`metricas`. Con cualquier otro nombre, las dos entradas del menú se quedan
apagadas como "Próximamente" para siempre y nadie entiende por qué.

```python
habitos = Blueprint("habitos", __name__)

@habitos.route("/habitos")
@security.requires("habito.ver")
def lista(): ...

@habitos.route("/metricas")
@security.requires("metrica.propia.ver")
def metricas(): ...
```

### `base.html` — BLOQUES CONGELADOS

El shell ya existe. Los nombres de bloque son estos y **no se renombran**:

```
title · encabezado · subtitulo · acciones · content · extra_css · extra_js
```

> 🚨 **Esto es una trampa mortal y silenciosa.** Documentos anteriores del
> proyecto mencionan `{% block titulo %}` y `{% block contenido %}`. **Están
> desactualizados.** Si escribes `contenido` en vez de `content`, Jinja no
> encuentra el bloque, **no lanza ningún error** y la página sale **en blanco**.
> Es el fallo más caro de diagnosticar que tiene este repositorio.

Plantilla mínima correcta:

```jinja
{% extends "base.html" %}
{% set seccion_activa = "habitos" %}   {# marca la entrada del menú con aria-current #}

{% block title %}Hábitos — VibePlanner{% endblock %}
{% block encabezado %}Mis hábitos{% endblock %}
{% block subtitulo %}<p class="text-muted">Tus rachas de sueño, ejercicio y alimentación.</p>{% endblock %}
{% block acciones %}<button class="btn btn--primary">Nuevo hábito</button>{% endblock %}

{% block content %}
  ...
{% endblock %}
```

`base.html` ya incluye la barra superior, la lateral, la barra inferior móvil y
los mensajes flash. **No los repintes.**

### Macros y componentes que ya existen — reutilízalos, no los dupliques

```jinja
{% from "components/_field.html" import campo, casilla_rol %}
```

Clases CSS ya definidas en `base.css` y `components.css`:

```
.card  .card--plano  .card-titulo      .btn  .btn--primary  .btn--secondary
.btn--ghost  .btn--danger  .btn--sm    .badge  .badge--info  .badge--activa
.field  .field-etiqueta  .field-control  .field-ayuda  .field-error
.estado-vacio   .tabla  .tabla-envoltura   .modal  .modal-cabecera  .modal-cuerpo
.barra-progreso  .barra-progreso-relleno   .alert  .alert--ok  .alert--error
.pila-2  .pila-4  .fila-entre  .btn-fila  .text-data  .text-muted
```

Si necesitas un componente nuevo (una tarjeta de hábito, una cifra grande de
métrica), añádelo a `components.css` **con tokens**, nunca con hex sueltos, y
siguiendo la nomenclatura en español que ya usa el archivo.

## Reglas que el código debe respetar SIEMPRE

1. La instancia de Flask se llama **exactamente `app`** a nivel de módulo en
   `app.py`. PythonAnywhere hace `from app import app`.
2. **Toda** consulta que devuelva datos de un usuario lleva `user_id` **dentro
   del `WHERE`**. Filtrar en Python después de traer las filas no cuenta.
3. **La regla de las dos llaves:** el decorador comprueba el **permiso**; el
   repositorio comprueba la **propiedad** del registro. Hacen falta las dos. Si
   el registro no es del usuario → **404**, no 403 (un 403 confirmaría que ese
   id existe).
4. El `user_id` sale **siempre** de la sesión (`security.current_user_id()`),
   jamás de un campo del formulario.
5. Todo el SQL va parametrizado con `?`. Cero concatenación de cadenas.
6. **Cero lógica de negocio en las plantillas.** Ningún cálculo dentro de
   `{{ }}`: los porcentajes y las rachas se calculan en `metrics.py`, donde se
   pueden probar.
7. Sin APIs externas, sin CDN, sin dependencias nuevas.
8. Comentarios **en español** y solo donde expliquen un *porqué*, no un *qué*.
9. Las fechas se guardan en ISO `YYYY-MM-DD` y se **muestran** en lenguaje
   humano ("Hoy", "Ayer", "Vence en 3 días").

## Diseño visual — dos paletas con dos trabajos distintos

> **El azul es la aplicación. El rosa es la importancia.**

Todos los valores ya están en `static/css/tokens.css` como variables CSS.
**Ningún hex suelto fuera de ese archivo.** Usa los roles semánticos
(`--bg-surface`, `--text-strong`, `--text-muted`, `--border`), no los colores
crudos.

**Correcciones de contraste que no se pueden saltar** (WCAG AA pide 4.5:1 para
texto normal):

| Token | Sobre blanco | Uso permitido |
|---|---|---|
| `--teal` `#567C8D` | 4.49:1 ❌ | Solo bordes, iconos y rellenos |
| `--teal-700` `#3F5F6E` | 6.90:1 ✅ | Botones, enlaces, texto de acento |
| `--rose` `#D7707F` | 3.20:1 ❌ | Solo rellenos y bordes |
| `--rose-700` `#9E3B4B` | 6.60:1 ✅ | Texto de alta prioridad y errores |
| `--steel` `#9DA3A4` | 2.56:1 ❌ | Solo bordes y desactivado |
| `--taupe` `#4C4D53` | 6.00:1 ✅ | Texto secundario y metadatos |

- **Tipografía:** `Inter` para la interfaz, `JetBrains Mono` (`--font-data`,
  clase `.text-data`) para **todos los números**: rachas, porcentajes, contadores.
  Auto-alojadas en `static/fonts/`, **nunca por CDN**.
- **Escala:** 12 · 14 · **16 (base)** · 18 · 22 · 28 · 34 px. Los campos de
  formulario nunca bajan de 16 px o iOS hace zoom al enfocarlos.
- **Espaciado:** base 4 px (4, 8, 12, 16, 24, 32, 48). Sin valores intermedios.
- **Objetivo táctil mínimo:** 44 × 44 px (`--touch-min`).
- **Mobile-first, sin excepciones:** el CSS base es el de móvil y los
  `@media (min-width: …)` van añadiendo. Breakpoints: `< 600px` móvil (barra
  inferior) · `600–1023px` tablet (sidebar de iconos) · `≥ 1024px` escritorio
  (sidebar fijo, contenido máx. 1200 px).
- **El color nunca es la única señal.** Cada insignia lleva **también su texto**
  ("Alta", "Racha activa", "Sin marcar"). ~1 de cada 12 hombres tiene daltonismo
  rojo-verde y las dos paletas del producto son azul y rosa: en escala de grises
  se confunden.
- **Nunca `outline: none` sin sustituto.** Quien navega con teclado necesita ver
  dónde está.
- **Estado vacío siempre.** Nunca una pantalla en blanco: qué falta, por qué
  importa y el botón para resolverlo (clase `.estado-vacio`).

## Cómo quiero que respondas

- Código completo y ejecutable, no fragmentos con `# ...resto igual`.
- Si algo de lo que pido te parece un error, **dímelo antes de generar el
  código** y explica el porqué. Prefiero discutirlo que recibir algo que parece
  correcto.
- No añadas funcionalidad que no pedí. Si se te ocurre algo útil, menciónalo al
  final como sugerencia, **fuera** del código.
- Si necesitas leer un archivo del repositorio para no inventarte su contenido,
  léelo antes de escribir nada.

---
