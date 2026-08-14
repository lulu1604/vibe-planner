# D7 — Design System transversal y responsive (US16)

**Objetivo:** que las 8 pantallas hechas por 4 personas parezcan **una sola
aplicación**. Este paso no construye una pantalla nueva: audita y unifica las que
ya existen. Es el trabajo menos visible del proyecto y el que más se nota en la
demo.

**Archivos que salen de aquí:** `static/css/tokens.css` (si falta algún token) ·
`static/css/base.css` · `static/css/components.css` · correcciones puntuales en
plantillas · `docs/VUP_V2/auditoria_design_system.md`

**Tiempo estimado:** 4 horas (es el paso más largo del módulo)

**Depende de:** que los módulos B y C hayan hecho merge de sus pantallas

> ⚠️ **Trabajo sobre código de otras personas.** Antes de reescribir la plantilla
> de alguien, pásale la lista de reemplazos y acuérdenlo. Lo que no vale es que
> llegue el viernes con dos estéticas distintas — ni que tú edites su archivo y
> él lo sobrescriba con un pull.

---

## 📋 El prompt — Parte A: auditoría

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Audita la consistencia visual del proyecto. Lee `static/css/tokens.css`,
`base.css`, `components.css`, `docs/VUP_V2/00_Design_System.md` y **todas** las
plantillas de `templates/`.

Genera `docs/VUP_V2/auditoria_design_system.md` con cuatro tablas:

### 1. Hex sueltos

Todo color escrito directamente en un CSS o en un `style=` de plantilla, que
debería ser un token. Para cada uno: archivo, línea, valor y **el token que le
corresponde**.

### 2. Clases inexistentes

Clases usadas en plantillas que **no están definidas** en ningún CSS. Ya sé de
una fuente importante: `templates/calendario/mes.html` usa `btn-secondary`,
`btn-outline`, `text-2xl`, `text-navy-900`, `flex-between`, `mb-4` y otras que
parecen de Tailwind y no existen en este proyecto. Para cada una, propón el
reemplazo real (`btn--secondary`, `.card-titulo`, `.fila-entre`…) en una tabla de
buscar-y-reemplazar que pueda pasarle a su autor.

### 3. Contraste

Toda combinación de texto sobre fondo que no llegue a **4.5:1** para texto normal
o 3:1 para texto grande (≥ 24 px o ≥ 19 px en negrita). Calcula el ratio real, no
lo estimes, y di qué token usar en su lugar. Vigila especialmente:

- `--teal` `#567C8D` como color de texto (4.49:1 ❌ → `--teal-700`)
- `--rose` `#D7707F` como color de texto (3.20:1 ❌ → `--rose-700`)
- `--steel` `#9DA3A4` como color de texto (2.56:1 ❌ → `--taupe`)
- El anillo de foco sobre la barra lateral navy: `--teal-700` da 1.53:1, o sea
  **invisible**. Ahí va `--focus-ring-on-dark`.

### 4. Información que depende solo del color

Insignias, estados y puntos de color **sin texto que los acompañe**. Cada uno
con la etiqueta que le falta.

Ordena todo por gravedad: primero lo que rompe accesibilidad, después lo que
rompe la consistencia, al final lo cosmético.

---

## 📋 El prompt — Parte B: corrección

> Después de revisar la auditoría y acordar con el equipo qué se toca, en una
> sesión nueva:

---

Aplica las correcciones de la auditoría, en este orden y **sin cambiar el
comportamiento** de ninguna pantalla:

### 1. Tokens que falten

Si algún valor se repite en tres sitios y no tiene token, añádelo a `tokens.css`
en la sección que le corresponda, con su ratio de contraste medido en el
comentario. Nada más: `tokens.css` no crece por gusto.

### 2. Mobile-first, verificado

El CSS base es el de móvil; los `@media (min-width: …)` van añadiendo. Si
encuentras `@media (max-width: …)`, dale la vuelta. Los tres breakpoints:

| Ancho | Navegación | Contenido |
|---|---|---|
| `< 600px` | Barra inferior, 5 iconos | Una columna · Kanban apilado |
| `600–1023px` | Sidebar colapsado a iconos | Dos columnas donde quepa |
| `≥ 1024px` | Sidebar fijo y etiquetado | Máx. 1200 px, centrado |

### 3. Las ocho pantallas, sin scroll horizontal a 360 px

`/planner`, `/kanban`, `/calendario`, `/habitos`, `/metricas`, `/admin/usuarios`,
`/login`, `/register`. Las causas habituales, en orden de frecuencia: tablas sin
`.tabla-envoltura` con `overflow-x`, `min-width` en píxeles fijos, imágenes sin
`max-width: 100%`, y `grid-template-columns` con anchos fijos que no caben.

### 4. Objetivos táctiles

Todo lo pulsable mide al menos `var(--touch-min)` (44 px) en ambas dimensiones.
Los primeros que se quedan cortos: los iconos de la barra inferior, los botones
de borrar de las tarjetas y las casillas de los 7 días de hábitos.

### 5. Foco visible en todo

Ni un `outline: none` sin sustituto. Sobre fondos claros, `--focus-ring`; sobre
la barra lateral navy, `--focus-ring-on-dark`. Recorre la aplicación entera con
`Tab` y dime dónde se pierde el foco.

### 6. Estados vacíos en las cinco pantallas

Con los textos del design system § 6.5, ni uno inventado:

| Pantalla | Mensaje |
|---|---|
| Planner | "Hoy no tienes nada planeado. Agrega tu primera actividad y verás tu día ordenado." |
| Kanban | "Tu tablero está vacío. Las actividades que crees aparecerán en Por hacer." |
| Calendario | "Sin eventos este mes. Crea el primero y aparecerá en su día." |
| Hábitos | "Aún no sigues ningún hábito. Empieza por uno: dormir, ejercicio o alimentación." |
| Métricas | "Hoy no registraste actividad. Cuando completes algo, lo verás aquí." |

Cada uno con las tres piezas: qué falta, por qué importa, y el botón para
resolverlo.

### 7. Fuentes auto-alojadas

`Inter-Variable.woff2` y `JetBrainsMono-Medium.woff2` en `static/fonts/`, con sus
`@font-face` y `font-display: swap`. **Ningún `<link>` a Google Fonts ni a ningún
CDN**: la demo tiene que funcionar aunque el aula se quede sin internet.

### 8. El menú del calendario, apagado por un nombre

`home.py` espera el endpoint `calendario.mes` y el blueprint real de Jose se llama
`calendar_bp` con la vista `month_view`, así que la entrada "Calendario" aparece
como "Próximamente". Se arregla con una línea — **pero es el archivo de Piero o
el de Jose**. Diagnostícalo, propón la corrección exacta y dime a quién hay que
pedírsela. No lo edites por tu cuenta.

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Cambió el comportamiento de alguna pantalla?** Esto es una unificación
   visual, no un rediseño. Si "de paso" reorganizó el Kanban, recházalo.
2. **¿Escribió `@media (max-width: …)`?** Mobile-first significa `min-width`.
3. **¿Añadió tokens que solo se usan una vez?** El token existe para lo que se
   repite.
4. **¿Estimó los ratios de contraste?** Que los calcule o los mida; la diferencia
   entre 4.49 y 4.51 decide si cumple.
5. **¿Quitó un `outline` "porque se veía feo"?** Nunca sin sustituto visible.
6. **¿Metió `!important`?** Casi siempre indica que el problema es el orden de
   carga, no la especificidad.
7. **¿Tocó `templates/calendario/` o archivos del Módulo B sin acuerdo previo?**
   Consúltalo antes: el merge del jueves es del tamaño de lo que se toque sin
   avisar.
8. **¿Usó `px` en lugar de `rem` para el texto?** La escala tipográfica es en
   `rem` para que respete el tamaño de fuente del sistema.

---

## ✅ Verificación del paso

Con DevTools, las 8 pantallas a tres anchos:

**360 px (TC-43)**
- [ ] Sin scroll horizontal en ninguna de las 8
- [ ] La navegación es la barra inferior
- [ ] El Kanban apila sus columnas con su cabecera y su contador
- [ ] Todo botón mide ≥ 44 × 44 px

**768 px y 1280 px (TC-44)**
- [ ] A 768 px el sidebar está colapsado a iconos, con `title` y `aria-label`
- [ ] A 1280 px el sidebar está fijo y etiquetado
- [ ] El contenido no pasa de 1200 px ni las líneas de ~75 caracteres
- [ ] No hay saltos rotos entre los tres tamaños

**Contraste y color (TC-45)**
- [ ] Todo texto normal ≥ 4.5:1, medido en DevTools
- [ ] Con el filtro de escala de grises del navegador, se siguen distinguiendo
      prioridad, urgencia y estado — porque cada insignia lleva su texto
- [ ] El foco se ve en todos los elementos, también sobre la barra lateral navy

**Consistencia**
- [ ] `grep -rn "#[0-9A-Fa-f]\{6\}" static/css/components.css static/css/base.css`
      no devuelve nada fuera de `tokens.css`
- [ ] Las 5 pantallas tienen su estado vacío diseñado (TC-18)
- [ ] Ningún `<link>` a un dominio externo en ninguna plantilla
- [ ] `python test_v2.py` y `python app.py test` siguen en verde
