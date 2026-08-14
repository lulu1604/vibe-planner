# 🎨 Auditoría del Design System (US16 · D7)

**Autora:** Ana Cusi · **Fecha:** 13 de agosto de 2026
**Alcance:** las 8 pantallas del proyecto, los 3 archivos CSS y las plantillas.

> ⚠️ **Esta auditoría corrige tres afirmaciones de `00_HALLAZGOS_Y_RIESGOS.md` y
> del propio prompt D7 que ya no se corresponden con el código.** El repositorio
> avanzó desde que se escribieron esos documentos. Todo lo que sigue está
> verificado contra el árbol de trabajo actual, no supuesto.

---

## 1. Hex sueltos fuera de `tokens.css`

**Resultado: 0 incumplimientos.** El objetivo ya se cumple.

| Archivo | Hex en declaraciones | Estado |
|---|---|---|
| `static/css/components.css` | **0** | ✅ |
| `static/css/base.css` | **0** | ✅ |
| `static/css/tokens.css` | 15 | ✅ correcto — es su sitio |
| `static/css/style.css` | 24 | ⚠️ ver abajo |

**Corrección al prompt D7:** decía que `components.css` tenía un hex suelto. Lo
que hay en la línea 481 es `#C8D9E6` **dentro de un comentario** que explica por
qué el color del evento va en el borde y no de fondo. No es una declaración.

**Lo único a resolver — `style.css` es código muerto.** Tiene 24 hex sueltos,
pero **ninguna plantilla lo carga**: `base.html` enlaza solo `tokens.css`,
`base.css` y `components.css`. Solo aparece citado en documentos antiguos
(`plan.md`, `docs/construction_spec.md`, `tareas/reparto.md`).

> 🤝 **Acción propuesta, no ejecutada:** borrar `static/css/style.css`. Es de la
> v1 y toca decidirlo en grupo, no unilateralmente desde el Módulo D.

---

## 2. Clases inexistentes en las plantillas

**Resultado: 0 incumplimientos.** El problema ya está resuelto.

**Corrección al prompt D7 y al hallazgo §5:** ambos denuncian que
`templates/calendario/mes.html` usa `btn-secondary`, `btn-outline`, `text-2xl`,
`text-navy-900`, `flex-between` y `mb-4`. **Ya no es cierto.** El archivo fue
reescrito sobre el design system; esos nombres solo sobreviven en el comentario
de cabecera (líneas 6-9) que documenta precisamente ese arreglo:

> *"La version anterior usaba clases de Tailwind (`flex-between`, `mb-4`,
> `text-gray-500`, `btn-primary`...) que aqui no existen"*

No hace falta la tabla de reemplazos que D7 pedía preparar para Jose, ni tocar
`templates/calendario/`.

---

## 3. Contraste — medido, no estimado

Ratios calculados con la fórmula WCAG 2.1 (luminancia relativa). AA exige
**4.5:1** para texto normal y **3:1** para texto grande (≥24 px o ≥19 px negrita).

### 3.1 Componentes nuevos del Módulo D — todos pasan

| Componente | Color de texto | Sobre | Ratio | AA |
|---|---|---|---|---|
| `.dia-casilla--cumplido` | `--beige` | `--teal-700` | **6.00:1** | ✅ |
| `.dia-casilla` | `--taupe` | `--sky` | **5.82:1** | ✅ |
| `.badge--marcado` | `--teal-700` | `--sky` | **4.73:1** | ✅ |
| `.badge--sin-marcar` | `--taupe` | `--sky` | **5.82:1** | ✅ |
| `.racha-cifra` (34 px) | `--teal-700` | `--white` | **6.83:1** | ✅ |
| `.metrica-cifra` (34 px) | `--teal-700` | `--white` | **6.83:1** | ✅ |
| `.habito-grupo-titulo` | `--navy` | `--beige` | **9.16:1** | ✅ |
| `.racha-texto` | `--taupe` | `--white` | **8.42:1** | ✅ |

El más ajustado es `.badge--marcado` con 4.73:1. Pasa, pero **no admite
retoques**: oscurecer `--sky` o aclarar `--teal-700` lo tumbaría bajo el umbral.

### 3.2 Tokens que NO pueden usarse como texto

Confirmado que siguen fallando, que es lo correcto: son relleno y borde.

| Token | Sobre `--white` | Sobre `--beige` (fondo real) | Sustituto para texto |
|---|---|---|---|
| `--teal` `#567C8D` | 4.50:1 | **3.95:1** ❌ | `--teal-700` (6.83:1) |
| `--rose` `#D7707F` | 3.22:1 ❌ | **2.83:1** ❌ | `--rose-700` (6.60:1) |
| `--steel` `#9DA3A4` | 2.56:1 ❌ | **2.25:1** ❌ | `--taupe` (8.42:1) |

> 📌 **Matiz importante:** el prompt D7 mide `--teal` contra blanco (4.49:1). El
> fondo real de la aplicación es `--bg-app: var(--beige)`, donde da **3.95:1** —
> falla por más margen del documentado. La regla "solo bordes y rellenos" es
> aún más necesaria de lo que decía el documento.

### 3.3 Anillo de foco

| Situación | Ratio | Estado |
|---|---|---|
| `--teal-700` sobre `--navy` (sidebar) | **1.53:1** | ❌ invisible |
| `--sky` sobre `--navy` (sidebar) | **7.22:1** | ✅ |

Ya resuelto en `tokens.css` con el token `--focus-ring-on-dark`. Ningún
`outline: none` sin sustituto en todo el CSS.

---

## 4. Información transmitida solo por color

**Resultado: 0 incumplimientos en el Módulo D.**

| Elemento | Señal además del color |
|---|---|
| Estado del día | Texto literal: "Marcado hoy" / "Sin marcar" |
| Casillas de los 7 días | Relleno **y borde** distintos, más `aria-label` completo por día |
| Día de hoy en la tira | `outline` propio, no solo tono |
| Barras de progreso | `role="progressbar"` + `aria-valuenow` + el número escrito al lado |
| Bloque de hábitos en `/metricas` | Separado por borde y por texto explicativo, no por color |

---

## 5. Lo que queda pendiente de verdad

**Las fuentes `.woff2` no están.** `static/fonts/` no existe, aunque `base.css`
ya declara sus dos `@font-face` con `font-display: swap` y un comentario que lo
advierte. Hoy la aplicación cae a las tipografías de respaldo de `tokens.css`
(`system-ui` y `Consolas`/`ui-monospace`), así que **se ve correcta, pero no es
la tipografía del design system**.

No lo he resuelto yo a propósito: descargar binarios de fuentes es traer
archivos externos al repositorio y eso se acuerda en grupo. Pasos:

1. Descargar `Inter-Variable.woff2` y `JetBrainsMono-Medium.woff2` (licencia
   SIL OFL, ambas libres).
2. Colocarlos en `static/fonts/`.
3. No hace falta tocar el CSS: los `@font-face` ya apuntan ahí.

**Nunca por CDN.** Verificado: cero enlaces externos en las plantillas
(`https://`, `cdn.`, `googleapis`, `unpkg`, `jsdelivr` → sin coincidencias).

---

## 6. Menú del calendario — ya no es un fallo

`00_HALLAZGOS_Y_RIESGOS.md` §5 dice que la entrada "Calendario" está apagada
porque `home.py` espera `calendario.mes` y el blueprint real es `calendar_bp`.
**Corregido en el repositorio.** `home.py:58` usa `calendar_bp.index`, con un
comentario que explica por qué no se usa `month_view` (necesitaría `year` y
`month`, y un `BuildError` en el menú tumbaría *todas* las pantallas porque el
menú vive en `base.html`).

---

## 7. Breakpoints y objetivos táctiles

Los componentes del Módulo D se escribieron mobile-first: el CSS base es el de
360 px y solo hay **un** `@media (min-width: 600px)` que añade la rejilla. Cero
`@media (max-width: …)` en la sección `MODULO D`.

| Ancho | Navegación | Contenido del Módulo D |
|---|---|---|
| `< 600px` | Barra inferior | Una columna; tarjetas de hábito apiladas |
| `600–1023px` | Sidebar de iconos | Rejilla `auto-fit` desde 18rem |
| `≥ 1024px` | Sidebar fijo | Máx. 1200 px (`--content-max`) |

Objetivos táctiles: `.dia-casilla` y el `<summary>` de "Nuevo hábito" llevan
`min-height: var(--touch-min)` (44 px). Los campos numéricos usan
`var(--text-base)` (16 px) para que iOS no haga zoom al enfocarlos.

---

## 8. Resumen para el equipo

| # | Hallazgo | Estado | A quién le toca |
|---|---|---|---|
| 1 | Hex sueltos en `components.css` | ✅ Ya cumplía (era un comentario) | — |
| 2 | Clases Tailwind en `mes.html` | ✅ Ya corregido por Jose | — |
| 3 | Contraste de los componentes nuevos | ✅ Los 8 pasan AA | — |
| 4 | Color como única señal | ✅ Cero casos | — |
| 5 | Menú de calendario apagado | ✅ Ya corregido | — |
| 6 | **Fuentes `.woff2` ausentes** | 🟠 **Pendiente** | Acordar en grupo |
| 7 | **`style.css` es código muerto** | 🟡 **Propuesta: borrarlo** | Acordar en grupo |

Las verificaciones visuales TC-43, TC-44 y TC-45 van en
[`evidencia_modulo_d.md`](evidencia_modulo_d.md).
