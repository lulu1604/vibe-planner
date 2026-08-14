# D4 — Blueprint `habitos` y la pantalla de hábitos (US13)

**Objetivo:** la pantalla donde se crean hábitos, se marca el día y se ve la
racha. Es la primera pantalla del módulo que ve una persona, y la que enciende
tu entrada del menú.

**Archivos que salen de aquí:** `habits.py` · `templates/habitos/lista.html` ·
`templates/habitos/_tarjeta_habito.html` · registro del blueprint en `app.py` ·
componentes nuevos en `components.css`

**Tiempo estimado:** 3–4 horas

**Depende de:** D2 y D3 terminados

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Genera el blueprint de hábitos y su pantalla. Antes de escribir, lee
`templates/base.html`, `templates/components/_field.html`,
`templates/admin/usuarios.html` (para copiar el estilo de una pantalla ya
terminada del proyecto) y `static/css/components.css`.

### 1. `habits.py` — el blueprint

**El nombre es obligatorio y no es negociable**, porque `home.py` ya lo tiene
reservado en el menú:

```python
habitos = Blueprint("habitos", __name__)

@habitos.route("/habitos")
@security.requires("habito.ver")
def lista(): ...

@habitos.route("/habitos", methods=["POST"])
@security.requires("habito.crear")
def crear(): ...

@habitos.route("/habitos/<int:habit_id>/registro", methods=["POST"])
@security.requires("habito.registrar")
def registrar(habit_id): ...

@habitos.route("/metricas")                 # <- se construye en el paso D5
@security.requires("metrica.propia.ver")
def metricas(): ...
```

Si el blueprint o las vistas se llaman de otra forma, las dos entradas del menú
se quedan apagadas como "Próximamente" **sin ningún error visible**. Deja un
comentario diciéndolo, para quien venga después.

### 2. Las tres reglas de cada vista

1. El `user_id` sale de `security.current_user_id()`, **nunca** del formulario.
2. Antes de tocar un hábito: `repo_habits.get_owned(habit_id, user_id)` y si
   devuelve `None` → `abort(404)`. **404, no 403**: un 403 confirmaría que ese id
   existe y es de otra persona.
3. Después de un POST correcto → `flash(...)` + `redirect` al listado. Nunca
   renderizar directamente tras un POST: recargar la página reenviaría el
   formulario.

### 3. La pantalla `lista.html`

Extiende `base.html` usando los bloques **congelados** (`title`, `encabezado`,
`subtitulo`, `acciones`, `content`) y marca la sección activa:

```jinja
{% extends "base.html" %}
{% set seccion_activa = "habitos" %}
```

Contenido:

- **Agrupada por tipo**: Sueño · Ejercicio · Dieta · Relajación · General. Cada
  grupo con su encabezado; los grupos vacíos no se pintan.
- **Una tarjeta por hábito** (`templates/habitos/_tarjeta_habito.html`) con:
  - nombre y meta legible: *"Dormir 8 horas"*, *"Tomar 8 vasos de agua"*
  - **la racha** como cifra grande en `--font-data` / clase `.text-data`, con su
    texto al lado: `7` + "días seguidos". Si la racha es 0: *"Empieza hoy"*, que
    invita en vez de lamentar.
  - **el control de hoy**: un formulario POST con el valor del día y un botón
    "Marcar hoy" / "Marcado ✓". Si ya está marcado, el control permite
    **corregir el valor** — y corregirlo no crea una fila nueva (TC-34).
  - Insignia de estado con **texto además de color**: "Marcado hoy" (`.badge`
    con `--ok-bg`) o "Sin marcar" (`.badge` neutra). Nunca solo un punto de
    color.
- **Los últimos 7 días** por hábito, como siete casillas pequeñas con la inicial
  del día y `aria-label` completo ("Lunes 11 de agosto: cumplido"). El estado se
  distingue por relleno **y por forma/borde**, no solo por color.
- **Formulario de alta**, en un `<details>` o en el modal que ya existe en
  `components.css`: nombre, tipo (los cinco), meta (número) y unidad
  (horas / minutos / vasos / veces). Reutiliza la macro `campo` de
  `components/_field.html` donde encaje.
- **Estado vacío** (`.estado-vacio`) con el texto del design system:
  *"Aún no sigues ningún hábito. Empieza por uno: dormir, ejercicio o
  alimentación."* + el botón para crear el primero.

### 4. CSRF en los tres formularios

`security.init_app(app)` valida CSRF en **todo** POST. Cada formulario lleva:

```jinja
<input type="hidden" name="_csrf" value="{{ csrf_token() }}">
```

Sin esto, marcar un hábito devuelve un 400 con el mensaje de sesión caducada. Es
el fallo número uno al añadir una pantalla nueva a este proyecto.

### 5. Rendimiento: nada de N+1

La vista `lista` hace **exactamente tres** consultas, no una por hábito:

1. `repo_habits.list_by_user(user_id)`
2. `repo_habits.logs_of_day_by_user(user_id, hoy)`
3. Los logs de los últimos 7 días de todos sus hábitos (una sola consulta)

Las rachas se calculan en Python desde esos logs ya traídos, llamando a
`metrics.habit_streak` solo con lo que ya está en memoria si es posible. Si eso
obliga a cambiar una firma de `metrics.py`, **dímelo antes de hacerlo** en vez de
cambiarla por tu cuenta: es un contrato congelado.

### 6. Registro en `app.py`

`app.py` es mi archivo (Ana). Añade el import y el `register_blueprint` junto a
los demás, en el mismo estilo y con el comentario de las rutas que expone. No
reordenes ni toques los otros registros.

### 7. CSS

Lo que necesites de nuevo (tarjeta de hábito, cifra de racha, casillas de los 7
días) va a `static/css/components.css`, al final, en una sección comentada
`MODULO D`. **Solo tokens, ningún hex suelto.** Mobile-first: primero el CSS de
móvil y luego `@media (min-width: …)`.

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | La racha y el estado de hoy se ven sin abrir nada |
| **H2** Idioma del usuario | "Sueño", "Dormir 8 horas" — nunca `habit_type` ni `target_value` |
| **H3** Control y libertad | Se puede corregir el registro de hoy, no queda congelado |
| **H5** Prevención de errores | El formulario acota el tipo y la unidad a listas cerradas |
| **H6** Reconocer > recordar | Los 7 días visibles: no hay que recordar si marcaste el martes |
| **H8** Minimalismo | Una acción primaria por pantalla: "Nuevo hábito" |
| **H9** Reconocer y recuperarse | Errores debajo del campo, con qué pasó y cómo arreglarlo |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿El blueprint se llama `habitos` y las vistas `lista` y `metricas`?** Con
   otro nombre, el menú queda apagado para siempre.
2. **¿Usó `{% block contenido %}` o `{% block titulo %}`?** Los bloques son
   `content` y `encabezado`. Con los otros nombres la página sale **en blanco sin
   ningún error**.
3. **¿Falta el `_csrf` en algún formulario?** Los tres lo llevan.
4. **¿Sacó el `user_id` de un campo oculto del formulario?** Sale de la sesión.
5. **¿Devuelve 403 cuando el hábito es de otro?** Debe ser **404**.
6. **¿Llama a `habit_streak` dentro de un bucle de plantilla?** Cero lógica en
   `{{ }}`, y además es N+1.
7. **¿El estado "marcado" se distingue solo por color?** Necesita texto.
8. **¿Los botones de marcar llegan a 44 × 44 px?** Las casillas de los 7 días son
   las primeras que se quedan cortas.
9. **¿Metió un `<canvas>`, Chart.js o un icono desde un CDN?** Sin dependencias
   externas: SVG inline, trazo 1.5, `currentColor`, `24×24`.
10. **¿Escribió el CSS de escritorio y luego `max-width` para móvil?** Pídelo
    mobile-first.

---

## ✅ Verificación del paso

```bash
python app.py       # y abre http://127.0.0.1:5000/habitos
```

- [ ] La entrada **Hábitos** del menú ya no dice "Próximamente" y lleva a la página
- [ ] Creo un hábito de cada uno de los cuatro tipos con su meta y unidad (TC-33)
- [ ] Marco hoy con valor 7, lo corrijo a 8, y
      `SELECT COUNT(*) FROM habit_logs WHERE habit_id=? AND log_date=?` devuelve **1** (TC-34)
- [ ] La racha sube al marcar hoy y el número usa `--font-data`
- [ ] Sin hábitos, sale el estado vacío con su botón, no una página en blanco
- [ ] Recorro la pantalla entera con `Tab` y siempre veo dónde está el foco
- [ ] A 360 px: sin scroll horizontal, barra inferior visible, nada tapado
- [ ] Con la cuenta de otro usuario, `/habitos/<id_ajeno>/registro` responde **404**
- [ ] En escala de grises se sigue distinguiendo marcado de sin marcar

---

## 🤝 Al cerrar este paso, avisa al equipo

> `/habitos` está en `main` y la entrada del menú ya se enciende. Añadí una
> sección `MODULO D` al final de `components.css` — si tocan ese archivo, hagan
> pull antes.
