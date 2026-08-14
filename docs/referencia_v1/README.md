# 📦 Referencia de la v1 — código retirado, no muerto

Estos cuatro archivos son la **pantalla del planner de la v1**. Ya no forman
parte de la aplicación, pero se conservan porque son el punto de partida del
**Módulo B (Lucero)**.

| Archivo | Qué era | Para qué sirve ahora |
|---|---|---|
| `index.html` | La pantalla del planner diario | Maquetación de referencia para `templates/planner/dia.html` |
| `score_modal.html` | Modal de explicabilidad del puntaje (US4) | El diferenciador del producto, ya migrado a `<dialog>` |
| `main.js` | Pide el desglose a la API y pinta las barras | La lógica de US4, lista para reusar |
| `style.css` | CSS propio de la v1 | Superado por `tokens.css → base.css → components.css` |

---

## Por qué están aquí y no en `templates/` y `static/`

La auditoría de integración retiró las cinco rutas de la v1 (`GET /`,
`POST /tasks`, `/tasks/<id>/delete`, `/tasks/<id>/status` y
`/api/task/<id>/score-breakdown`) por dos razones: no tenían autenticación, y
colisionaban con los endpoints que trae el blueprint del Módulo B.

Al retirarlas, `index.html` quedó apuntando a endpoints que ya no existen:

```
BuildError: Could not build url for endpoint 'add_task_route'
```

Un archivo así **dentro de `templates/`** es una trampa: no falla hasta que
alguien lo renderiza, y entonces falla con un error que no dice qué pasó. Aquí
cumple la misma función de referencia sin poder romper nada.

## Qué tiene que hacer Lucero con esto

1. Copiar la maquetación de `index.html` a `templates/planner/dia.html`,
   cambiando los `url_for(...)` por los endpoints de su blueprint.
2. Reusar `main.js` para US4 — ojo: la versión viva del modal ya está en
   `static/js/ui.js` y usa `<dialog>`, que trae el cierre con `Escape` y la
   devolución del foco de fábrica.
3. **No** recuperar `style.css`. El design system vive en `static/css/` y es lo
   que hace que ocho pantallas hechas por cuatro personas parezcan una sola
   aplicación.

## Lo que sigue vivo en `database.py`

`get_tasks()`, `add_task()`, `update_status()`, `delete_task()` y
`get_daily_progress()` **no se han borrado**: son el contrato congelado de Jose
y `python database.py` sigue verificándolas. Su limitación conocida es que
`tasks` no tiene `user_id`, así que `get_daily_progress()` cuenta las tareas de
toda la base. Eso lo resuelve el Módulo B al migrar la tabla.
