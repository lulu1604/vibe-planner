# 📋 VUP Phase 4: Construction Phase I Document

**Project Name:** VibePlanner — Multi-User Activity Planner with Transparent Prioritization
**Version:** 2.0 (Update — Multiusuario, Roles y Permisos)
**Phase:** Construction Phase I (Project Blueprint & Task Mapping)

---

## ⚙️ 1. Stack tecnológico — decisiones congeladas

| Capa | Decisión | Por qué |
|---|---|---|
| Lenguaje | Python 3.10+ | Estándar del curso y de PythonAnywhere |
| Framework web | **Flask 3.0.3** con Blueprints, **sin** application factory | PythonAnywhere ejecuta `from app import app`. Los blueprints dan modularidad sin tocar el contrato de despliegue |
| Plantillas | Jinja2 (incluido en Flask) | Renderizado en servidor, cero build step |
| Frontend | HTML + CSS propio + JavaScript vanilla | El curso evalúa esto. Sin React, sin build, sin `node_modules` |
| Persistencia | SQLite3 (`sqlite3` de la librería estándar), un archivo `vibe_planner.db` | Sin ORM: SQL parametrizado directo, como en v1 |
| Contraseñas | `werkzeug.security` (`generate_password_hash` / `check_password_hash`) | **Ya viene instalado con Flask.** Hashear no cuesta una dependencia nueva |
| Sesiones | Cookie firmada de Flask (`session`) con `SECRET_KEY` | Sin Flask-Login: 20 líneas en `security.py` cubren el caso |
| Tokens | `secrets.token_urlsafe(32)` (librería estándar) | Invitaciones imposibles de adivinar |
| Fechas | `datetime` + `zoneinfo` con fallback UTC−5 | Heredado de v1: el servidor corre en UTC y Lima es UTC−5 |
| Entorno | `venv` por integrante + `requirements.txt` | El `venv/` **no** se sube al repo |
| Despliegue | PythonAnywhere free tier (WSGI) | Sin coste, sin red saliente necesaria |

### 1.1 `requirements.txt` — sigue teniendo una línea

```
Flask==3.0.3
```

`Werkzeug` y `Jinja2` entran como dependencias de Flask. `sqlite3`, `secrets`,
`datetime`, `zoneinfo` y `os` son librería estándar. **Añadir cualquier otra
línea a este archivo requiere acuerdo del equipo**, porque cada dependencia nueva
es una cosa más que puede fallar en el servidor el día de la presentación.

### 1.2 Configuración y secretos

```python
# config.py
import os

SECRET_KEY = os.environ.get("VIBEPLANNER_SECRET", "dev-only-no-usar-en-produccion")
DEFAULT_AVAILABLE_MINUTES = 120
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
```

> ⚠️ **El `SECRET_KEY` real se configura solo en el panel de PythonAnywhere**, como
> variable de entorno. Si la clave de producción aparece en el repositorio, queda
> en el historial público de GitHub para siempre y cualquiera puede falsificar
> sesiones. Es el riesgo R10 de Inception.

---

## 🏗️ 2. Estructura del proyecto

**24 archivos de aplicación**, planos y con un dueño único cada uno. La regla es
la misma de v1: *un archivo, una responsabilidad, un dueño*.

```
proyect_final/
├── app.py                     # A · crea `app`, registra blueprints. NADA más
├── config.py                  # A · SECRET_KEY y constantes
├── security.py                # A · login_required, requires(), current_user()
├── database.py                # A · conexión por petición, init_db()
├── schema_v2.sql              # A · esquema completo v2 (fuente única de verdad)
├── seed.py                    # A · roles, permisos, admin semilla, datos demo
├── migrate_v1_to_v2.py        # A · migración de bases de datos v1 existentes
│
├── auth.py                    # A · blueprint: /register /login /logout
├── repo_users.py              # A · SQL de users/roles/permissions
├── admin.py                   # A · blueprint: /admin/usuarios /admin/metricas
│
├── planner.py                 # B · blueprint: /planner /tasks /kanban /equipo
├── repo_tasks.py              # B · SQL de tasks
├── scoring.py                 # B · fórmula y desglose (SIN cambios de fórmula)
│
├── calendar_bp.py             # C · blueprint: /calendario /eventos /invitacion
├── repo_events.py             # C · SQL de events y event_invitations
│
├── habits.py                  # D · blueprint: /habitos /metricas
├── repo_habits.py             # D · SQL de habits y habit_logs
├── metrics.py                 # D · cálculo de métricas propias y del sistema
│
├── wsgi_pythonanywhere.py     # A · punto de entrada WSGI
├── requirements.txt           # A · Flask==3.0.3
├── test_v2.py                 # todos · suite de asserts automáticos
│
├── templates/
│   ├── base.html              # T · shell responsive: sidebar + topbar + bottom nav
│   ├── components/            # T · _task_card.html, _badge.html, _modal.html…
│   ├── auth/                  # A · login.html, register.html
│   ├── admin/                 # A · usuarios.html, metricas.html
│   ├── planner/               # B · dia.html, kanban.html, equipo.html
│   ├── calendario/            # C · mes.html, evento_form.html, invitacion.html
│   └── habitos/               # D · habitos.html, metricas.html
│
└── static/
    ├── css/
    │   ├── tokens.css         # T · variables: paleta, tipografía, espaciado
    │   ├── base.css           # T · reset, tipografía, layout responsive
    │   └── components.css     # T · tarjetas, insignias, formularios, modal
    ├── js/
    │   ├── main.js            # T · modal de puntaje, utilidades
    │   ├── kanban.js          # B · arrastrar y soltar
    │   └── calendario.js      # C · navegación entre meses
    └── fonts/                 # T · .woff2 auto-alojados (nunca CDN)
```

**Leyenda de módulos:** `A` Núcleo · `B` Planner · `C` Calendario · `D` Hábitos y
métricas · `T` Transversal (design system).

> 📌 El blueprint del calendario se llama `calendar_bp.py`, **no** `calendar.py`:
> `calendar` es un módulo de la librería estándar de Python y llamarlo igual
> provoca un import circular difícil de diagnosticar.

---

## 🎨 3. Design System — decisiones de diseño

La especificación completa (tokens listos para pegar, componentes, breakpoints y
verificación de contraste) está en **`docs/VUP_V2/00_Design_System.md`**. Resumen
de las decisiones cerradas:

### 3.1 Paleta principal — la identidad de la web

| Token | Hex | Uso |
|---|---|---|
| Navy | `#2F4156` | Barra lateral, textos principales, superficies oscuras |
| Teal | `#567C8D` | Acentos, bordes, botones secundarios |
| Sky Blue | `#C8D9E6` | Rellenos suaves, insignias informativas, estados hover |
| Beige | `#F5EFEB` | Fondo de la aplicación |
| White | `#FFFFFF` | Tarjetas y campos de formulario |

### 3.2 Paleta de importancia — semántica, nunca decorativa

| Token | Hex | Significado |
|---|---|---|
| Old Rose | `#D7707F` | Prioridad **alta** / vencido |
| Soft Blush | `#F5D5DA` | Relleno de la insignia de alta prioridad |
| Pale Slate | `#D8D2D8` | Prioridad **media** |
| Cool Steel | `#9DA3A4` | Prioridad **baja**, bordes neutros, elementos desactivados |
| Taupe Grey | `#4C4D53` | Texto secundario y metadatos |

> ⚠️ **Corrección de contraste obligatoria.** `#D7707F` sobre blanco da **3.20:1**
> y **no** cumple WCAG AA para texto normal (4.5:1). Por eso el design system
> añade un token derivado `--rose-700: #9E3B4B` (**6.60:1** sobre blanco,
> **4.84:1** sobre Soft Blush) que es el que se usa para **texto**; `#D7707F`
> queda reservado para **rellenos y bordes**. Lo mismo aplica a Cool Steel
> (2.56:1): solo bordes y fondos, nunca texto.

### 3.3 Tipografía

| Rol | Familia | Por qué |
|---|---|---|
| Interfaz y textos | **Inter** (variable) | Neutral, excelente legibilidad a 14–16 px, muy buena en pantallas pequeñas |
| Números y puntajes | **JetBrains Mono** | Los dígitos monoespaciados se alinean verticalmente entre tarjetas: el ranking se compara de un vistazo. Coherente con la promesa de "puntaje auditable" |
| Respaldo | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` | Si la fuente no carga, la interfaz no se rompe |

**Ambas se auto-alojan en `static/fonts/` como `.woff2`.** Corrección al documento
de v1: un `<link>` a Google Fonts **sí funcionaría** en PythonAnywhere, porque
quien descarga la fuente es el navegador del visitante, no el servidor — la
restricción de red saliente del free tier aplica al servidor. Aun así elegimos
auto-alojar por tres razones: la demo funciona aunque el aula se quede sin
internet, la página carga más rápido, y se mantiene el principio de cero
dependencias externas que define al producto.

### 3.4 Puntos de quiebre responsive

| Nombre | Ancho | Navegación | Contenido |
|---|---|---|---|
| Móvil | < 600 px | Barra inferior con 5 iconos | Una columna, Kanban apilado |
| Tablet | 600–1023 px | Barra lateral colapsada a iconos | Dos columnas donde quepa |
| Escritorio | ≥ 1024 px | Barra lateral fija y etiquetada | Máx. 1200 px de ancho de contenido |

**Mobile-first:** el CSS base es el de móvil y los `@media (min-width: …)` van
añadiendo. Al revés siempre termina en un móvil lleno de parches.

---

## ✅ 4. Checklist de implementación

### Módulo A — Núcleo *(bloquea a todos los demás)*

- [ ] `schema_v2.sql` con las 10 tablas, sus `FOREIGN KEY` y sus índices
- [ ] `database.py`: conexión por petición, `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`, `timeout=10`
- [ ] `repo_users.py`: CRUD de usuarios, asignación de roles, `get_permissions()` con `DISTINCT`
- [ ] `security.py`: `current_user()`, `effective_permissions()`, `@login_required`, `@requires()`
- [ ] `auth.py`: registro (**rol `usuario` forzado en servidor**), login, logout, `next` tras autenticar
- [ ] `seed.py`: 3 roles, ~20 permisos, sus vínculos, y el administrador semilla
- [ ] `admin.py`: listado, alta, edición, desactivación, asignación de roles, métricas del sistema
- [ ] `migrate_v1_to_v2.py`: migra bases v1 existentes mapeando los estados
- [ ] `app.py`: registra los 5 blueprints, `teardown_appcontext`, manejadores 403/404
- [ ] Asserts: TC 5.1, 5.3, 5.5, 6.1, 6.2, 6.4, 7.3

### Módulo B — Planner y Kanban

- [ ] `repo_tasks.py`: **toda** consulta con `user_id` en el `WHERE`
- [ ] `scoring.py`: fórmula intacta, adaptada a recibir listas ya filtradas
- [ ] `planner.py`: `/planner`, CRUD de tareas, `/kanban`, `/tasks/<id>/column`, `/equipo/tareas`
- [ ] Validación de servidor: título no vacío, minutos 1–480, fecha `YYYY-MM-DD`, columna en las 4 permitidas
- [ ] `templates/planner/`: revisión del día, tablero, vista de equipo
- [ ] `kanban.js`: arrastrar y soltar con reversión si el servidor responde error
- [ ] Asserts: TC 1.3, 2.1, 2.2, 3.2, 4.2, 9.1, 9.3, 10.2

### Módulo C — Calendario e invitaciones

- [ ] `repo_events.py`: eventos por mes, invitaciones con token, aceptación idempotente
- [ ] `calendar_bp.py`: cuadrícula mensual, navegación, CRUD de eventos, `/invitacion/<token>`
- [ ] Validación: `end_at > start_at`, color de la paleta permitida
- [ ] `templates/calendario/`: mes, formulario de evento, pantalla de invitación
- [ ] Asserts: TC 11.1, 11.3, 11.4, 12.2, 12.4

### Módulo D — Hábitos y métricas

- [ ] `repo_habits.py`: hábitos por usuario, `upsert` de registro diario, rango de fechas
- [ ] `metrics.py`: resumen del día por sección, racha, métricas agregadas del sistema
- [ ] `habits.py`: `/habitos`, `/habitos/<id>/registro`, `/metricas`
- [ ] Protección de división entre cero en **todos** los porcentajes
- [ ] `templates/habitos/`: hábitos con racha, panel de métricas
- [ ] Asserts: TC 13.2, 13.3, 13.4, 14.1, 14.2, 15.1

### Transversal — Design System

- [ ] `tokens.css` con las dos paletas, la escala tipográfica y el espaciado
- [ ] `base.html`: shell responsive (sidebar ≥1024 · bottom nav <600)
- [ ] `components/`: tarjeta, insignia, modal, formulario, estado vacío
- [ ] Fuentes `.woff2` auto-alojadas en `static/fonts/`
- [ ] Verificación de contraste en las 8 pantallas
- [ ] Asserts manuales: TC 16.1 – 16.4

---

## 🗺️ 5. User Story Mapping

| Historia | Archivos responsables | Ruta / Endpoint | Casos que la verifican |
|---|---|---|---|
| **US5** Registro y login | `auth.py`, `repo_users.py`, `templates/auth/` | `GET/POST /register`, `GET/POST /login`, `POST /logout` | TC 5.1 – 5.5 |
| **US6** Permisos agregativos | `security.py`, `repo_users.py` | *(transversal a todas las rutas)* | TC 6.1 – 6.4 |
| **US7** Gestión de usuarios | `admin.py`, `repo_users.py`, `templates/admin/` | `GET /admin/usuarios`, `POST /admin/usuarios`, `POST /admin/usuarios/<id>/estado`, `POST /admin/usuarios/<id>/roles` | TC 7.1 – 7.3 |
| **US1** CRUD de tareas | `planner.py`, `repo_tasks.py` | `POST /tasks`, `POST /tasks/<id>/edit`, `POST /tasks/<id>/delete` | TC 1.1 – 1.3 |
| **US2** Ranking | `scoring.py`, `planner.py` | `GET /planner` | TC 2.1 – 2.2 |
| **US3** Estado y progreso | `repo_tasks.py`, `planner.py` | `POST /tasks/<id>/column` | TC 3.1 – 3.2 |
| **US4** Modal de puntaje | `scoring.py`, `main.js` | `GET /api/task/<id>/score-breakdown` | TC 4.1 – 4.2 |
| **US8** Revisión del día | `planner.py`, `templates/planner/dia.html` | `GET /planner` | TC 8.1 – 8.3 |
| **US9** Kanban | `planner.py`, `kanban.js` | `GET /kanban`, `POST /tasks/<id>/column` | TC 9.1 – 9.3 |
| **US10** Asignación al equipo | `planner.py`, `repo_tasks.py` | `POST /tasks` (con `assigned_to`), `GET /equipo/tareas` | TC 10.1 – 10.3 |
| **US11** Calendario mensual | `calendar_bp.py`, `repo_events.py` | `GET /calendario/<año>/<mes>`, `POST /eventos` | TC 11.1 – 11.4 |
| **US12** Invitación por link | `calendar_bp.py`, `repo_events.py` | `POST /eventos/<id>/invitacion`, `GET/POST /invitacion/<token>` | TC 12.1 – 12.4 |
| **US13** Hábitos | `habits.py`, `repo_habits.py` | `GET /habitos`, `POST /habitos`, `POST /habitos/<id>/registro` | TC 13.1 – 13.4 |
| **US14** Métricas propias | `metrics.py`, `habits.py` | `GET /metricas` | TC 14.1 – 14.3 |
| **US15** Métricas del sistema | `metrics.py`, `admin.py` | `GET /admin/metricas` | TC 15.1 – 15.3 |
| **US16** Responsive | `tokens.css`, `base.css`, `base.html` | *(todas las pantallas)* | TC 16.1 – 16.4 |

**16 historias · 16 rutas principales · 45 casos de prueba.** Ninguna historia sin
archivo responsable, ningún archivo sin historia que lo justifique.

---

## 🗓️ 6. Fases de desarrollo e hitos

| Hito | Qué se cierra | Criterio de "listo" |
|---|---|---|
| **H1 — Esquema y núcleo** | `schema_v2.sql`, `database.py`, `repo_users.py`, `security.py`, `auth.py`, `seed.py` | Se puede registrar, iniciar sesión, y `security.py` devuelve la unión correcta de permisos para una cuenta con dos roles |
| **H2 — Contratos congelados** | `current_user()`, `@login_required`, `@requires()`, `schema_v2.sql` | Publicados en `main` y **anunciados al grupo**. A partir de aquí B, C y D arrancan en paralelo |
| **H3 — Módulos en paralelo** | Planner+Kanban · Calendario+invitaciones · Hábitos+métricas | Cada módulo pasa sus propios asserts contra la base sembrada |
| **H4 — Design System aplicado** | `tokens.css`, `base.html`, componentes | Las 8 pantallas usan los mismos tokens y pasan a 360/768/1280 px |
| **H5 — Integración y pruebas** | `test_v2.py` completo | Los 45 casos ejecutados; los 3 críticos (TC 5.3, 6.4, 1.3) en verde |
| **H6 — Despliegue** | PythonAnywhere + `SECRET_KEY` de producción + seed ejecutado | Dos cuentas reales usan la app desplegada al mismo tiempo |

> ⏱️ **H1 y H2 son el cuello de botella.** Mientras el núcleo no esté en `main`,
> los otros tres módulos maquetan a ciegas. Es la misma lección que el reparto de
> v1 dejó escrita: los módulos base primero.

---

## 🔗 7. Orden de dependencia entre módulos

```
schema_v2.sql  →  database.py  →  repo_users.py  →  security.py  →  auth.py + seed.py
                                                          │
                        ┌─────────────────────────────────┼─────────────────────────────────┐
                        ↓                                 ↓                                 ↓
              repo_tasks + scoring              repo_events                         repo_habits
                     planner.py                calendar_bp.py                        habits.py
                        └─────────────────────────────────┬─────────────────────────────────┘
                                                          ↓
                                                     metrics.py
                                                          ↓
                                              templates/ + static/  (design system)
                                                          ↓
                                                  wsgi_pythonanywhere.py
```

1. **`schema_v2.sql`** — nada existe antes del esquema. Dueño único: Jose.
2. **`security.py`** — todo lo demás lo importa. Su contrato se congela en H2.
3. **Repositorios** — un módulo nunca lee las tablas de otro módulo directamente;
   pide los datos al repositorio dueño.
4. **`metrics.py`** — depende de B y C, por eso se cierra al final.
5. **Design System** — puede avanzar en paralelo desde el día uno con datos falsos.

---

## 🔒 8. Reglas que no se rompen

1. La instancia de Flask se llama **exactamente `app`** a nivel de módulo en
   `app.py`. PythonAnywhere hace `from app import app`. **Sin application factory.**
2. `vibe_planner.db` **nunca** se sube al repositorio. Está en `.gitignore`.
3. Sin APIs externas, sin CDN, sin gunicorn, sin `node_modules`. Solo Flask y
   librería estándar.
4. **Toda** consulta que devuelva datos de un usuario lleva `user_id` en el `WHERE`.
   Filtrar en Python después de traer las filas no cuenta.
5. Los decoradores comprueban **permisos**, nunca nombres de rol.
6. El `user_id` sale **siempre** de la sesión, jamás del formulario — salvo la
   asignación de US10, que exige el permiso `tarea.asignar`.
7. Las contraseñas se hashean con `werkzeug.security`. Nunca se guardan, imprimen
   ni registran en claro.
8. El `SECRET_KEY` de producción vive en una variable de entorno del servidor,
   no en el código.
9. La fórmula de puntuación no se modifica. Vive solo en `scoring.py`.
10. Un módulo no toca las tablas de otro módulo: pasa por su repositorio.
11. Las plantillas no contienen lógica de negocio. Ningún cálculo dentro de Jinja2.
12. Cada uno crea **su propio** `venv`. Se comparte `requirements.txt`, no la carpeta.
13. Todo permiso nuevo se declara en `seed.py`. Un permiso que solo existe en un
    decorador y no en la tabla es un 403 permanente que nadie sabrá explicar.

---

## 🔀 9. Flujo de trabajo en Git

```bash
git checkout main
git pull origin main
git checkout -b feature/modulo-<letra>-<tu-nombre>
# ... trabajas solo en TUS archivos ...
git add .
git commit -m "modulo A: resolucion de permisos agregativos"
git push origin feature/modulo-a-piero
# Pull Request en GitHub → revisa otro integrante → merge
```

- **Merge a `main` todos los días**, aunque tu parte esté incompleta. Los
  conflictos de un día se resuelven en cinco minutos; los de una semana, no.
- Antes de abrir un PR: `python test_v2.py` en verde y la app arranca sin error.
- Si necesitas cambiar un archivo que **no es tuyo**, avisa al grupo **antes**.

---

## 📝 10. Evidencia para la rúbrica

Cada prompt usado con la IA se guarda en `docs/prompts/` **el mismo día**, con:

1. El prompt literal que escribiste.
2. Qué devolvió la IA.
3. Qué aceptaste, qué rechazaste y **por qué** (formato del registro de crítica de
   Elaboration II).
4. Al menos **un ejemplo real de código que la IA generó mal** y cómo se corrigió.

Eso no se reconstruye de memoria el último día, y la rúbrica lo pide
explícitamente.
