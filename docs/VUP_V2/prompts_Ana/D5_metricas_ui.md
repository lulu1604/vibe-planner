# D5 — `/metricas`: "¿cómo me fue hoy?" (US14)

**Objetivo:** la pantalla que responde la pregunta del final del día. Números
grandes, honestos y con contexto, sin un solo cálculo dentro de la plantilla.

**Archivos que salen de aquí:** vista `metricas` en `habits.py` ·
`templates/habitos/metricas.html` · componentes de métricas en `components.css`

**Tiempo estimado:** 2–3 horas

**Depende de:** D3 y D4 terminados

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Construye la pantalla `/metricas` (mis métricas del día). La vista ya está
declarada en `habits.py` como `metricas` con `@security.requires("metrica.propia.ver")`.
Lee `metrics.py` antes de escribir: **todos los números vienen ya calculados de
`daily_summary()`** y la plantilla solo los pinta.

### 1. La vista

```python
@habitos.route("/metricas")
@security.requires("metrica.propia.ver")
def metricas():
    user_id = security.current_user_id()
    fecha = request.args.get("fecha") or metrics.hoy_iso()
    # Una fecha que llega por la URL es entrada de usuario: valídala antes de
    # usarla, o un 'fecha=hola' revienta el date.fromisoformat de metrics.
    ...
    resumen = metrics.daily_summary(user_id, fecha)
    return render_template("habitos/metricas.html", resumen=resumen, ...)
```

- La fecha se valida con `date.fromisoformat` dentro de un `try`; si no es
  válida, se usa hoy y se avisa con un `flash` en vez de dar un 400.
- No se permite consultar fechas futuras: se recorta a hoy.
- Navegación "día anterior / hoy / día siguiente" con enlaces `GET`, para que se
  pueda compartir y volver atrás. El botón "día siguiente" se desactiva en hoy.

### 2. La pantalla

Extiende `base.html` con los bloques congelados y
`{% set seccion_activa = "metricas" %}`.

Estructura, de arriba abajo:

1. **La cifra principal.** El porcentaje del día en `--text-3xl` y `--font-data`,
   con su fracción debajo en lenguaje normal: *"6 de 8 actividades completadas"*.
   Nunca el porcentaje solo: un 75 % de 4 tareas y un 75 % de 40 no significan lo
   mismo.
2. **Barra de progreso** con `.barra-progreso` / `.barra-progreso-relleno`, que
   ya existen en `components.css`. Con `role="progressbar"`, `aria-valuenow`,
   `aria-valuemin` y `aria-valuemax`, y el porcentaje escrito al lado: la barra
   sola no la lee un lector de pantalla ni se ve en escala de grises.
3. **Desglose por sección**: Trabajo · Personal · Actividades. Cada una con su
   `completadas / total`, su porcentaje y su mini-barra. El orden lo da
   `metrics.py`, la plantilla solo recorre el diccionario.
4. **Hábitos, en su propio bloque visualmente separado**, con un encabezado que
   deje claro que es otro indicador: *"Hábitos de hoy: 2 de 3"*. **Sin
   porcentaje** y **sin sumarse** al de tareas (TC-39). Añade un `<p class="text-muted">`
   explicando en una línea por qué van aparte: son rutinas, no tareas del día.
5. **Eventos del día**: el número de eventos, con enlace al calendario.
6. **Estado vacío** cuando no hay nada que mostrar: *"Hoy no registraste
   actividad. Cuando completes algo, lo verás aquí."* con el botón para ir al
   planner.

### 3. Cuando el módulo de actividades aún no está conectado

`daily_summary` puede devolver `"tareas_conectadas": False` porque el Módulo B
todavía no ha añadido `user_id` a `tasks`. En ese caso, **no pintes un 0 %**: eso
parece un dato real y es mentira. Pinta un aviso `.alert .alert--info`:

> *"El módulo de actividades aún no está conectado. En cuanto lo esté, aquí
> verás tu porcentaje del día."*

Los hábitos y los eventos **sí** se muestran normalmente: esos ya funcionan.

### 4. Cero lógica en la plantilla

Ni un `{{ (completadas / total * 100) | round }}`. Si al maquetar te falta un
número, se añade a `daily_summary()` en `metrics.py`, donde se puede probar. Esto
no es purismo: el TC-38 (cuenta vacía sin error 500) es imposible de garantizar
si el cálculo está repartido entre Python y Jinja.

El ancho de las barras es el único cálculo admitido en la plantilla, y va como
`style="width: {{ seccion.porcentaje }}%"`, usando un número que ya viene
calculado.

### 5. Nada de gráficos de librería

Sin Chart.js, sin `<canvas>`, sin CDN. Las barras son `<div>` con `width` en
porcentaje y los números son texto. Se ven mejor, cargan al instante, funcionan
sin JavaScript y son accesibles sin trabajo extra.

### 6. CSS

Los componentes nuevos (cifra grande, tarjeta de sección, bloque de hábitos) van
al final de `components.css`, en la sección `MODULO D`. Solo tokens. Mobile-first:
una columna en móvil, dos o tres a partir de 600 px con `grid` y
`repeat(auto-fit, minmax(…))`.

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | El día entero se entiende en tres segundos |
| **H2** Idioma del usuario | "6 de 8 actividades completadas", no "tasks: 6/8" |
| **H4** Consistencia | Mismo shell, mismos tokens, mismas barras que el resto |
| **H6** Reconocer > recordar | La fracción acompaña siempre al porcentaje |
| **H8** Minimalismo | Un número principal; el resto es apoyo |
| **H10** Ayuda | El estado vacío dice qué hacer, no solo que no hay nada |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Algún porcentaje se calcula en la plantilla?** Recházalo.
2. **¿Los hábitos entran en el porcentaje de tareas?** Recházalo (TC-39).
3. **¿Una cuenta recién creada da un 500?** Es el defecto más probable del módulo
   (TC-38). Pruébalo de verdad: crea una cuenta nueva y entra directo a
   `/metricas`.
4. **¿`fecha=cualquier-cosa` en la URL revienta la vista?** Debe recortarse a hoy
   con un aviso.
5. **¿Metió Chart.js o un `<canvas>`?** Fuera: sin dependencias externas.
6. **¿La barra de progreso solo comunica con color y ancho?** Necesita el número
   escrito y los atributos `aria-*`.
7. **¿Pinta 0 % cuando en realidad no hay datos conectados?** Es engañoso: aviso
   explícito.
8. **¿Repitió los hex de los colores en el CSS de las barras?** Solo tokens.

---

## ✅ Verificación del paso

- [ ] Con 3 de Trabajo, 1 de Personal y 2 de Actividades completadas de 8 totales,
      la pantalla muestra las tres secciones y **75 %** (TC-37)
- [ ] Con una cuenta recién creada, `/metricas` muestra 0 % y el estado vacío,
      **sin error 500** (TC-38)
- [ ] Con 2 hábitos marcados de 3, aparece "2 de 3" aparte y el porcentaje de
      tareas **sigue siendo 75 %** (TC-39)
- [ ] `/metricas?fecha=hola` no rompe nada
- [ ] Sin el permiso `metrica.propia.ver`, la ruta responde **403**
- [ ] A 360 px: una columna, sin scroll horizontal
- [ ] Todos los números usan `--font-data`
- [ ] En escala de grises se siguen distinguiendo las secciones (llevan su texto)
