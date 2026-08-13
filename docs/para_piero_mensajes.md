# 📩 Para Piero — bloque de mensajes de error (6 líneas)

**De:** Ana (dueña de `app.py`)
**Motivo:** el `reparto.md` me pide *"si algo falla, no insertar y **mostrar el error al usuario**"*.

Ya está hecha la validación en servidor: título vacío, fecha inválida, duración ≤ 0 o no numérica y prioridad fuera de rango **ya no se insertan**. Los mensajes salen por `flash()`.

**El problema:** ninguna plantilla renderiza `flash()` todavía, así que los mensajes se generan y se pierden en silencio.

---

## Lo que necesito que agregues

En `templates/base.html`, **dentro de `<main>`, justo antes de `{% block content %}`**:

```html
    {% with mensajes = get_flashed_messages(with_categories=true) %}
      {% if mensajes %}
        <div class="avisos">
          {% for categoria, texto in mensajes %}
            <p class="aviso aviso-{{ categoria }}">{{ texto }}</p>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
```

Es **puramente aditivo**: no toca tu diseño ni tus clases, y si no lo pegas nada se rompe — simplemente los errores siguen sin verse.

---

## Categorías que envío

| Categoría | Cuándo | Sugerencia de color |
|---|---|---|
| `error` | Validación fallida, actividad inexistente | `--alerta` (coral `#F2555A`) |
| `ok` | Actividad agregada o eliminada | `--tiempo` (verde azulado `#2DD4A7`) |

Estilo mínimo por si te sirve de arranque:

```css
.avisos { margin: 0 0 1rem; }
.aviso {
  padding: .6rem .9rem;
  border-radius: var(--radio);
  border: 1px solid var(--borde);
  font-size: .9rem;
  margin: 0 0 .5rem;
}
.aviso-error { border-color: var(--alerta); color: var(--alerta); }
.aviso-ok    { border-color: var(--tiempo); color: var(--tiempo); }
```

---

## Mensajes exactos que va a recibir tu maqueta

Sirven para probar cómo se ven sin tener que romper el formulario a propósito:

- `El título no puede estar vacío. Escribe qué actividad quieres registrar.`
- `La fecha «2026-02-31» no es válida. Usa el formato AAAA-MM-DD, por ejemplo 2026-08-20.`
- `La duración debe ser mayor a 0 minutos.`
- `La duración «abc» no es un número. Escribe los minutos, por ejemplo 45.`
- `La prioridad debe ser Alta, Media o Baja.`
- `Actividad agregada.`
- `Actividad eliminada.`

---

## Lo que NO cambié (tu contrato sigue igual)

- Las rutas: `/`, `/tasks`, `/tasks/<id>/delete`, `/tasks/<id>/status`, `/api/task/<id>/score-breakdown`
- Las variables de `index.html`: `tasks`, `available_minutes`, `progress`
- El JSON del desglose: `{"id", "total", "breakdown"}` con `puntos` y `razon`
- Los `name=` de los formularios y los `id=` de `main.js`

Hay un assert en `app.py` (el #9) que **falla a propósito** si alguien cambia la forma de ese JSON, justamente para que no te rompan el `main.js` sin darse cuenta.
