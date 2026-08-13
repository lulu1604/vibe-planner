# P4 — Home con menú de módulos (el shell de la aplicación)

**Objetivo:** la estructura que van a heredar las 8 pantallas del proyecto. El
menú muestra **solo** lo que los permisos del usuario permiten, y el
administrador ve una entrada extra que un usuario común no ve.

**Archivos que salen de aquí:** `templates/base.html` ·
`templates/components/_sidebar.html` · `_topbar.html` · `_bottom_nav.html` ·
`templates/home.html` · `home.py` (blueprint) · ampliación de `base.css`

**Tiempo estimado:** 3–4 horas.

> 🎁 **Este paso es un regalo para el equipo.** Lucero, Jose y Ana van a extender
> `base.html` para sus módulos. Si el shell está bien hecho, sus pantallas salen
> consistentes solas; si está mal, cada uno inventa su propio layout.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE.md` completo, y después esto:

---

Genera el shell responsive de VibePlanner v2 y su pantalla de inicio. Ya existen
`security.py` (con `current_user`, `has_permission` expuestos a Jinja2), `auth.py`
y los CSS `tokens.css`, `base.css`, `components.css`.

### 1. `base.html` — el shell que heredan todas las pantallas

Tres zonas: barra lateral, barra superior y contenido. Bloques Jinja2
`{% block titulo %}`, `{% block acciones %}` y `{% block contenido %}` para que
cada módulo rellene lo suyo.

**Comportamiento responsive (mobile-first):**

| Ancho | Navegación |
|---|---|
| `< 600px` | Barra **inferior** fija con 5 iconos y su etiqueta debajo |
| `600–1023px` | Barra lateral colapsada: solo iconos, con `title` y `aria-label` |
| `≥ 1024px` | Barra lateral fija de 240 px con icono + etiqueta |

El contenido se limita a 1200 px y se centra. En móvil, `padding-bottom` igual a
la altura de la barra inferior, o el último elemento queda tapado.

### 2. El menú — construido desde los permisos

**La parte importante.** Define la lista de módulos en Python, no en la plantilla,
y que cada entrada declare el permiso que la habilita:

```python
MODULOS = [
    {"clave": "planner",    "etiqueta": "Mi día",      "icono": "…",
     "endpoint": "planner.day_route",       "permiso": "planner.ver"},
    {"clave": "kanban",     "etiqueta": "Tablero",     "icono": "…",
     "endpoint": "planner.kanban_route",    "permiso": "kanban.ver"},
    {"clave": "calendario", "etiqueta": "Calendario",  "icono": "…",
     "endpoint": "calendario.month_route",  "permiso": "evento.ver"},
    {"clave": "habitos",    "etiqueta": "Hábitos",     "icono": "…",
     "endpoint": "habitos.list_route",      "permiso": "habito.ver"},
    {"clave": "metricas",   "etiqueta": "Mis métricas","icono": "…",
     "endpoint": "habitos.metrics_route",   "permiso": "metrica.propia.ver"},
    {"clave": "admin",      "etiqueta": "Administración", "icono": "…",
     "endpoint": "admin.list_users_route",  "permiso": "usuario.listar"},
]
```

La plantilla recorre la lista y pinta solo las entradas cuyo permiso el usuario
tiene, usando el `has_permission()` que `security.py` ya expone a Jinja2.

> Comenta que **ocultar la entrada es cortesía visual, no seguridad**: la ruta
> sigue protegida por `@requires` en el servidor, y quien escriba la URL a mano
> recibe un 403 igualmente.

**Problema práctico:** los blueprints de Lucero, Jose y Ana **todavía no
existen**, así que `url_for` fallaría. Resuélvelo con una función auxiliar que
devuelva `#` y marque la entrada como "próximamente" si el endpoint aún no está
registrado en `app.url_map`. Así puedes construir y probar el menú completo hoy, y
las entradas se activan solas cuando cada compañero haga su merge. Marca las
inactivas con `aria-disabled="true"` y un estilo apagado.

**Sección activa:** la entrada de la sección actual lleva fondo `--sky`, texto
`--navy`, una barra de 3 px a la izquierda y `aria-current="page"`.

### 3. `_topbar.html`

- El nombre de la pantalla actual a la izquierda (`{% block titulo %}`).
- A la derecha: el usuario y **sus roles como insignias**, por ejemplo
  `piero · [Usuario] [Administrador]`. Esto hace visible lo agregativo — se ve que
  una sola cuenta lleva los dos roles.
- Menú desplegable con "Mi perfil" y "Cerrar sesión". El logout es un `<form
  method="post">`, no un enlace.
- Zona `{% block acciones %}` para el botón primario de cada pantalla.

### 4. `home.py` y `home.html`

Ruta `GET /` con `@login_required`. La pantalla de inicio tiene:

1. **Saludo con el nombre**: "Buenos días, Piero" según la hora (usa la zona
   `America/Lima`, nunca `datetime.now()` sin zona: el servidor corre en UTC).
2. **Tarjetas de acceso a los módulos**, filtradas por permiso igual que el menú.
   Cada tarjeta: icono, nombre y una línea de qué hace. Las de módulos aún no
   construidos salen apagadas con la etiqueta "Próximamente".
3. **Un resumen** con marcadores de posición (`—`) para las cifras que llenarán
   los otros módulos: actividades de hoy, eventos del mes, hábitos marcados.
   Déjalo preparado para conectarlo después, sin inventar datos.
4. **Estado vacío** para la cuenta recién creada: "Estás empezando. Cuando agregues
   tu primera actividad, aquí verás tu día ordenado."

### 5. Iconos

SVG **inline**, sin librerías ni CDN. Trazo de 1.5 px, `currentColor` para que
hereden el color del contexto, `24×24`. Si son decorativos y el texto ya está al
lado, ponles `aria-hidden="true"`.

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | Sección activa marcada; usuario y roles visibles arriba |
| **H2** Idioma del usuario | "Mi día", "Tablero", "Administración" — no "planner", "kanban" |
| **H3** Control y libertad | El logo lleva al home desde cualquier pantalla |
| **H4** Consistencia | El mismo shell en las 8 pantallas del proyecto |
| **H6** Reconocer > recordar | Todos los módulos visibles en el menú, no escondidos |
| **H7** Eficiencia | Tarjetas de acceso directo en el home |
| **H8** Minimalismo | Icono + etiqueta, sin adornos que compitan con el contenido |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿El menú se construye con `has_permission()` o con el nombre del rol?** Si
   aparece algo como `if 'admin' in user.roles`, rechaza: rompe el modelo de
   permisos.
2. **¿`url_for` falla con los endpoints que aún no existen?** Necesita la función
   auxiliar que comprueba `app.url_map`.
3. **¿El logout es un enlace GET?** Debe ser un formulario POST.
4. **¿Los iconos vienen de un CDN?** Deben ser SVG inline.
5. **¿La barra inferior tapa el contenido en móvil?** Falta `padding-bottom` en el
   contenedor.
6. **¿Los objetivos táctiles llegan a 44 px?** Los iconos de la barra inferior son
   los primeros que se quedan cortos.
7. **¿Escribió el CSS de escritorio primero y luego `max-width` para móvil?**
   Pídelo mobile-first: al revés termina en un móvil lleno de parches.
8. **¿La entrada activa se distingue solo por color?** Necesita también la barra
   lateral o el peso de la fuente — 1 de cada 12 hombres no distingue bien los
   colores.

---

## ✅ Verificación del paso

**La prueba que importa** — dos cuentas, dos menús distintos:

```bash
# Como admin (roles: usuario + admin)
```
- [ ] Veo las 6 entradas, incluida "Administración"

```bash
# Como piero (rol: usuario)
```
- [ ] Veo 5 entradas y **no** aparece "Administración"
- [ ] Si escribo `/admin/usuarios` a mano, recibo **403** — la ruta está
      protegida, no solo oculta

Y el resto:
- [ ] La barra superior muestra el usuario con **sus dos insignias de rol** en la
      cuenta admin
- [ ] La sección activa se distingue sin leer la URL
- [ ] A 360 px: barra inferior, sin scroll horizontal, nada tapado
- [ ] A 768 px: barra lateral de iconos
- [ ] A 1280 px: barra lateral con etiquetas, contenido máx. 1200 px
- [ ] Recorro todo el menú **con `Tab`** y siempre veo dónde está el foco
- [ ] Las entradas de módulos no construidos salen apagadas, no rotas
- [ ] Contraste ≥ 4.5:1 en el texto de la barra lateral sobre `--navy`

---

## 🤝 Al cerrar este paso, avisa al equipo

> `base.html` ya está en `main`. Extiéndanlo así:
> ```jinja
> {% extends "base.html" %}
> {% block titulo %}Mi día{% endblock %}
> {% block acciones %}<button class="btn btn--primary">Agregar actividad</button>{% endblock %}
> {% block contenido %} ... {% endblock %}
> ```
> Sus entradas del menú ya están puestas y se activan solas cuando registren su
> blueprint con el nombre de endpoint acordado. Si necesitan cambiar el nombre,
> avísenme.
