# 🎨 VibePlanner v2 — Design System

**Documento transversal.** Lo leen los cuatro módulos antes de maquetar una sola
pantalla. Si un color, un tamaño o un espaciado no está en este documento, no se
usa: se propone al grupo y se añade aquí primero.

---

## 0. La decisión de diseño en una frase

> **El azul es la aplicación. El rosa es la importancia.**

Dos paletas con dos trabajos distintos y sin solaparse:

- La **paleta principal (azules y beige)** construye la interfaz: fondo, barra
  lateral, tarjetas, botones, texto. Es lo que hace que VibePlanner se vea como
  VibePlanner.
- La **paleta de importancia (rosas y grises)** comunica **cuánto importa algo**:
  prioridad alta, media, baja, vencido. Nunca se usa para decorar.

Cuando el rosa aparece, significa algo. Si se usa para adornar un encabezado
bonito, pierde su fuerza y el usuario deja de leerlo como una señal.

---

## 1. Paleta principal — la identidad

| Token | Hex | Uso | Contraste verificado |
|---|---|---|---|
| **Navy** | `#2F4156` | Barra lateral, texto principal, superficies oscuras | **10.44:1** sobre blanco ✅ · **9.17:1** sobre beige ✅ |
| **Teal** | `#567C8D` | Bordes, iconos, rellenos de acento | 4.49:1 sobre blanco ⚠️ *(solo relleno/borde, no texto pequeño)* |
| **Teal 700** *(derivado)* | `#3F5F6E` | Botones primarios, enlaces, texto de acento | **6.90:1** con texto blanco ✅ |
| **Sky Blue** | `#C8D9E6` | Rellenos suaves, insignias informativas, hover | **7.22:1** con texto navy ✅ |
| **Beige** | `#F5EFEB` | Fondo de la aplicación | base |
| **White** | `#FFFFFF` | Tarjetas, campos de formulario, modales | base |

> ⚠️ **Teal `#567C8D` no cumple AA para texto normal** (4.49:1, el mínimo es
> 4.5:1). Se queda para bordes, iconos y rellenos. Para **texto y botones** se usa
> el derivado `--teal-700`. Es un token nuevo, no un capricho: sin él, media
> interfaz sería inaccesible por un margen de 0.01.

---

## 2. Paleta de importancia — la semántica

| Token | Hex | Significado | Contraste verificado |
|---|---|---|---|
| **Old Rose** | `#D7707F` | Acento de prioridad alta — **solo relleno y borde** | 3.20:1 sobre blanco ❌ *nunca texto* |
| **Rose 700** *(derivado)* | `#9E3B4B` | Texto de alta prioridad y vencido | **6.60:1** sobre blanco ✅ · **4.84:1** sobre Soft Blush ✅ |
| **Soft Blush** | `#F5D5DA` | Fondo de la insignia de alta prioridad | base |
| **Pale Slate** | `#D8D2D8` | Fondo de prioridad media, etiquetas de categoría | base |
| **Cool Steel** | `#9DA3A4` | Bordes neutros, prioridad baja, desactivado | 2.56:1 ❌ *nunca texto* |
| **Taupe Grey** | `#4C4D53` | Texto secundario y metadatos | **6.00:1** sobre blanco ✅ · **5.67:1** sobre Pale Slate ✅ |

### 2.1 Los cuatro estados de importancia

| Estado | Fondo | Texto | Borde | Etiqueta obligatoria |
|---|---|---|---|---|
| **Vencida** | `#9E3B4B` sólido | blanco | — | "Vencida" |
| **Alta** | `#F5D5DA` | `#9E3B4B` | `#D7707F` | "Alta" |
| **Media** | `#D8D2D8` | `#4C4D53` | transparente | "Media" |
| **Baja** | transparente | `#4C4D53` | `#9DA3A4` | "Baja" |

**Progresión de peso visual, no cuatro colores sueltos.** Vencida grita, Alta
llama, Media informa, Baja se hace a un lado. Un vistazo a la lista basta para
saber qué mira primero el ojo — y esa jerarquía es la misma que produce el motor
de puntuación.

### 2.2 Los tres componentes del puntaje

El modal de auditoría (US4) es la pantalla que diferencia a VibePlanner de
Todoist y de Motion. Cada componente de la fórmula tiene su color y **ese color
se repite en todos los sitios donde ese componente aparece**: la insignia de la
tarjeta, el texto de la fecha y la barra del modal. El usuario aprende a leer el
ranking sin que nadie se lo explique.

| Componente | Color | Dónde aparece |
|---|---|---|
| Prioridad (50/30/10) | `--rose-700` `#9E3B4B` | Insignia de prioridad · barra del modal |
| Urgencia (40/20/10/5) | `--navy` `#2F4156` | Fecha de vencimiento · barra del modal |
| Ajuste de tiempo (+15/0) | `--teal-700` `#3F5F6E` | Duración estimada · barra del modal |

---

## 3. Tipografía

| Rol | Familia | Pesos | Por qué |
|---|---|---|---|
| Interfaz y texto | **Inter** *(variable)* | 400 · 500 · 600 · 700 | Neutra, excelente a 14–16 px, muy legible en pantallas pequeñas |
| Números y puntajes | **JetBrains Mono** | 500 · 700 | Los dígitos monoespaciados se alinean verticalmente entre tarjetas: el ranking se compara de un vistazo. Coherente con la promesa de "puntaje auditable" |
| Respaldo | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` | — | Si la fuente no carga, la interfaz no se rompe |

### 3.1 Auto-alojadas, nunca CDN

```
static/fonts/
├── Inter-Variable.woff2
├── JetBrainsMono-Medium.woff2
└── JetBrainsMono-Bold.woff2
```

```css
@font-face {
  font-family: 'Inter';
  src: url('/static/fonts/Inter-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;   /* el texto se ve al instante con la fuente de respaldo */
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/static/fonts/JetBrainsMono-Medium.woff2') format('woff2');
  font-weight: 500;
  font-display: swap;
}
```

> 📌 **Corrección a la guía visual de v1.** Aquella decía que no se podía usar
> Google Fonts porque PythonAnywhere no tiene red saliente. Eso es **inexacto**:
> quien descarga la fuente es el **navegador del visitante**, no el servidor, así
> que un `<link>` a Google Fonts sí funcionaría. Aun así elegimos auto-alojar por
> tres razones concretas: (1) la demo funciona aunque el aula se quede sin
> internet, (2) la página carga más rápido sin una conexión externa, y (3) se
> mantiene el principio de cero dependencias externas que define al producto.

### 3.2 Escala tipográfica

| Token | Tamaño | Interlineado | Uso |
|---|---|---|---|
| `--text-xs` | 12 px | 1.4 | Metadatos, contadores de columna |
| `--text-sm` | 14 px | 1.5 | Texto secundario, etiquetas de formulario |
| `--text-base` | 16 px | 1.6 | Texto general. **Nunca menos de 16 px en campos de formulario**, o iOS hace zoom al enfocarlos |
| `--text-lg` | 18 px | 1.5 | Título de tarjeta |
| `--text-xl` | 22 px | 1.3 | Título de sección |
| `--text-2xl` | 28 px | 1.2 | Título de página |
| `--text-3xl` | 34 px | 1.15 | Cifra grande de métricas |

**Longitud de línea: máximo ~75 caracteres.** Por eso el contenido se limita a
1200 px aunque la pantalla sea más ancha.

---

## 4. `tokens.css` — listo para pegar

```css
/* =====================================================================
   VibePlanner v2 — Design tokens
   static/css/tokens.css  ·  se carga ANTES que base.css y components.css
   ===================================================================== */

:root {
  /* ---------- Paleta principal: la identidad ---------- */
  --navy:        #2F4156;
  --navy-dark:   #24334252;   /* solo para sombras y superposiciones */
  --teal:        #567C8D;     /* bordes e iconos — NO texto pequeño */
  --teal-700:    #3F5F6E;     /* botones, enlaces, texto de acento (6.90:1) */
  --sky:         #C8D9E6;
  --beige:       #F5EFEB;
  --white:       #FFFFFF;

  /* ---------- Paleta de importancia: la semántica ---------- */
  --rose:        #D7707F;     /* relleno y borde — NO texto (3.20:1) */
  --rose-700:    #9E3B4B;     /* texto de alta prioridad (6.60:1) */
  --blush:       #F5D5DA;
  --slate:       #D8D2D8;
  --steel:       #9DA3A4;     /* bordes y desactivado — NO texto (2.56:1) */
  --taupe:       #4C4D53;     /* texto secundario (6.00:1) */

  /* ---------- Roles semánticos: usa ESTOS en los componentes ---------- */
  --bg-app:          var(--beige);
  --bg-surface:      var(--white);
  --bg-sidebar:      var(--navy);
  --bg-subtle:       var(--sky);

  --text-strong:     var(--navy);
  --text-body:       #33404F;
  --text-muted:      var(--taupe);
  --text-on-dark:    var(--beige);

  --border:          #DCD5D0;
  --border-strong:   var(--steel);
  --focus-ring:      var(--teal-700);

  /* Componentes del puntaje (US4) */
  --score-priority:  var(--rose-700);
  --score-urgency:   var(--navy);
  --score-timefit:   var(--teal-700);

  /* ---------- Tipografía ---------- */
  --font-ui:    'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-data:  'JetBrains Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace;

  --text-xs:   0.75rem;    /* 12 */
  --text-sm:   0.875rem;   /* 14 */
  --text-base: 1rem;       /* 16 */
  --text-lg:   1.125rem;   /* 18 */
  --text-xl:   1.375rem;   /* 22 */
  --text-2xl:  1.75rem;    /* 28 */
  --text-3xl:  2.125rem;   /* 34 */

  /* ---------- Espaciado: base 4 px, sin valores intermedios ---------- */
  --space-1:  0.25rem;   /*  4 */
  --space-2:  0.5rem;    /*  8 */
  --space-3:  0.75rem;   /* 12 */
  --space-4:  1rem;      /* 16 */
  --space-6:  1.5rem;    /* 24 */
  --space-8:  2rem;      /* 32 */
  --space-12: 3rem;      /* 48 */

  /* ---------- Formas ---------- */
  --radius-sm:   6px;
  --radius-md:   10px;
  --radius-lg:   16px;
  --radius-pill: 999px;

  --shadow-sm: 0 1px 2px rgba(47, 65, 86, .08);
  --shadow-md: 0 4px 12px rgba(47, 65, 86, .10);
  --shadow-lg: 0 12px 32px rgba(47, 65, 86, .16);

  --transition: 160ms ease;

  /* ---------- Medidas del layout ---------- */
  --sidebar-width:           240px;
  --sidebar-width-collapsed: 68px;
  --bottom-nav-height:       64px;
  --content-max:             1200px;
  --touch-min:               44px;   /* tamaño mínimo de un objetivo táctil */
}
```

---

## 5. Layout responsive

### 5.1 Puntos de quiebre

| Nombre | Ancho | Navegación | Contenido |
|---|---|---|---|
| Móvil | `< 600px` | Barra inferior, 5 iconos con etiqueta | Una columna · Kanban apilado |
| Tablet | `600–1023px` | Barra lateral colapsada a iconos | Dos columnas donde quepa |
| Escritorio | `≥ 1024px` | Barra lateral fija y etiquetada | Máx. 1200 px de contenido |

**Mobile-first, sin excepciones:** el CSS base es el de móvil y los
`@media (min-width: …)` van añadiendo. Al revés siempre termina en un móvil lleno
de parches.

```css
/* base.css — móvil primero */
.app-shell { display: block; padding-bottom: var(--bottom-nav-height); }
.sidebar   { display: none; }
.bottom-nav{ display: flex; position: fixed; inset: auto 0 0 0;
             height: var(--bottom-nav-height); }

@media (min-width: 600px) {
  .app-shell  { display: grid; grid-template-columns: var(--sidebar-width-collapsed) 1fr;
                padding-bottom: 0; }
  .sidebar    { display: flex; }
  .bottom-nav { display: none; }
  .sidebar .nav-label { display: none; }
}

@media (min-width: 1024px) {
  .app-shell { grid-template-columns: var(--sidebar-width) 1fr; }
  .sidebar .nav-label { display: inline; }
  .content   { max-width: var(--content-max); margin-inline: auto;
               padding: var(--space-8); }
}
```

### 5.2 El Kanban en móvil

Cuatro columnas de 90 px son ilegibles. A menos de 600 px, las columnas se
**apilan verticalmente**, cada una con su cabecera y su contador, y se puede
plegar la que no interese (TC 16.3).

```css
.kanban { display: flex; flex-direction: column; gap: var(--space-6); }

@media (min-width: 1024px) {
  .kanban { display: grid; grid-template-columns: repeat(4, 1fr);
            align-items: start; }
}
```

---

## 6. Componentes

### 6.1 Tarjeta de actividad

```
┌──────────────────────────────────────────────┐
│ ▌ Informe de IoT                    [90 pts] │  ← borde izquierdo = color propio
│ ▌ [Alta] [Trabajo] · Vence hoy · 45 min      │     puntaje en --font-data
│ ▌ 10:00 - 10:45                              │
│ ▌ ───────────────────────────────────────    │
│ ▌ [¿Por qué este orden?]  [Estado ▾]  [🗑]   │
└──────────────────────────────────────────────┘
```

- Fondo `--bg-surface`, radio `--radius-md`, sombra `--shadow-sm`.
- Borde izquierdo de 4 px con el color de la actividad.
- El puntaje **siempre** en `--font-data`: los números monoespaciados se alinean
  entre tarjetas y el ranking se compara de un vistazo.
- **Las tareas completadas se apagan**, no se celebran: `opacity: .5` y
  `text-decoration: line-through`. Lo terminado cede el protagonismo a lo que falta.

### 6.2 Insignias

```css
.badge {
  display: inline-flex; align-items: center; gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs); font-weight: 600;
  border: 1px solid transparent;
}
.badge--vencida { background: var(--rose-700); color: var(--white); }
.badge--alta    { background: var(--blush); color: var(--rose-700);
                  border-color: var(--rose); }
.badge--media   { background: var(--slate); color: var(--taupe); }
.badge--baja    { background: transparent; color: var(--taupe);
                  border-color: var(--steel); }
.badge--info    { background: var(--sky); color: var(--navy); }
```

> 🔴 **Regla obligatoria: el color nunca es la única señal.** Cada insignia lleva
> **también su texto** ("Alta", "Vence hoy", "En curso"). Alrededor de 1 de cada
> 12 hombres tiene daltonismo rojo-verde, y las dos paletas de este producto son
> azul y rosa: en escala de grises se confunden. Es TC 16.4 y es bloqueante.

### 6.3 Botones

| Variante | Fondo | Texto | Cuándo |
|---|---|---|---|
| Primario | `--teal-700` | blanco | La acción principal de la pantalla — **una sola por pantalla** |
| Secundario | transparente | `--teal-700` | Acciones alternativas, borde `--border-strong` |
| Fantasma | transparente | `--text-muted` | Acciones terciarias |
| Destructivo | transparente | `--rose-700` | Eliminar, desactivar. Borde `--rose`. **Siempre pide confirmación** |

```css
.btn { min-height: var(--touch-min); padding: var(--space-3) var(--space-6);
       border-radius: var(--radius-sm); font: 600 var(--text-sm)/1 var(--font-ui);
       cursor: pointer; transition: var(--transition); border: 1px solid transparent; }
.btn:focus-visible { outline: 3px solid var(--focus-ring); outline-offset: 2px; }
.btn--primary { background: var(--teal-700); color: var(--white); }
.btn--danger  { background: transparent; color: var(--rose-700); border-color: var(--rose); }
```

**Nunca se quita el `:focus-visible`.** Quien navega con teclado necesita ver
dónde está; un `outline: none` sin sustituto deja la aplicación inutilizable.

### 6.4 Formularios

- Etiqueta **encima** del campo, nunca solo un `placeholder`: el placeholder
  desaparece al escribir y el usuario ya no sabe qué campo es.
- Campos a `--text-base` (16 px) como mínimo: por debajo, iOS hace zoom al enfocar.
- Error **debajo** del campo, en `--rose-700`, precedido de un icono y con texto
  que dice qué pasó **y cómo arreglarlo**: *"La duración debe estar entre 1 y 480
  minutos."*, no *"Valor inválido"*.
- Altura mínima de campo y botón: `--touch-min` (44 px).

### 6.5 Estado vacío

Nunca una pantalla en blanco. Tres piezas: qué falta, por qué importa, y el botón
para resolverlo.

| Pantalla | Mensaje |
|---|---|
| Planner | "Hoy no tienes nada planeado. Agrega tu primera actividad y verás tu día ordenado." |
| Kanban | "Tu tablero está vacío. Las actividades que crees aparecerán en Por hacer." |
| Calendario | "Sin eventos este mes. Crea el primero y aparecerá en su día." |
| Hábitos | "Aún no sigues ningún hábito. Empieza por uno: dormir, ejercicio o alimentación." |
| Métricas | "Hoy no registraste actividad. Cuando completes algo, lo verás aquí." |

### 6.6 Modal de auditoría del puntaje

**Es la pantalla más importante del producto.** Es donde se ve la diferencia con
Todoist y con Motion, y donde un usuario decide si confía en el orden o lo ignora.

```
┌────────────────────────────────────┐
│  ¿Por qué este orden?          [×] │
│                                    │
│  Informe de IoT          90 pts    │  ← --font-data, --text-3xl
│  ────────────────────────────────  │
│  ▬▬▬▬▬▬▬▬▬▬  Prioridad Alta   +50  │  ← --score-priority (rosa)
│  ▬▬▬▬▬▬▬▬    Vence hoy        +40  │  ← --score-urgency (navy)
│  ▬            Supera tu tiempo  +0 │  ← --score-timefit (teal)
│  ────────────────────────────────  │
│  Total                        90   │
└────────────────────────────────────┘
```

- La **suma mostrada debe coincidir exactamente** con la insignia de la tarjeta
  (TC-15). Si difieren, se pierde el diferenciador del producto entero.
- Se cierra con `Escape`, con el botón y al pulsar fuera.
- El foco entra al modal al abrirlo y **regresa al botón que lo abrió** al cerrarse.

---

## 7. Textos de la interfaz

- **Botones en voz activa y sentence case:** "Agregar actividad", no "ENVIAR".
- **Los errores dicen qué pasó y cómo arreglarlo.** "La duración debe estar entre
  1 y 480 minutos", no "Error de validación".
- **Los estados vacíos invitan, no lamentan.**
- **Sin jerga de programador en pantalla.** El usuario no sabe qué es un `user_id`
  ni un `kanban_column`. Dice "columna", "actividad", "tu plan".
- **Fechas legibles:** "Vence hoy", "Vence mañana", "Vence en 3 días" — no
  `2026-08-27`. El formato ISO es para la base de datos, no para las personas.

---

## 8. Lista de verificación antes de dar una pantalla por terminada

- [ ] Usa **solo** tokens de `tokens.css`. Ningún hex suelto en el CSS del componente.
- [ ] Se ve bien a **360 px**, **768 px** y **1280 px** (TC-43, TC-44).
- [ ] Sin scroll horizontal en móvil.
- [ ] Todo objetivo táctil mide al menos 44 × 44 px.
- [ ] Texto normal con contraste ≥ **4.5:1**, medido en DevTools (TC-45).
- [ ] Toda insignia lleva **texto además del color**.
- [ ] Los campos de formulario tienen etiqueta visible, no solo placeholder.
- [ ] Existe estado vacío diseñado.
- [ ] El foco de teclado es visible en todos los elementos interactivos.
- [ ] Los números y puntajes usan `--font-data`.
- [ ] **Cero lógica de negocio en la plantilla Jinja2.** Ningún cálculo dentro de `{{ }}`.
