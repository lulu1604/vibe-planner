# 👥 Reparto de Trabajo y Guía Visual — VibePlanner

**Curso:** Fundamentals of Vibe Coding — ESAN Global Week 2026
**Repo:** `vibe-planner`

> Lee tu sección y el bloque de "Reglas que no se rompen". Si necesitas cambiar
> algo fuera de tus archivos, avisa al grupo **antes** de hacerlo.

---

## 📋 Resumen

| Integrante | Módulo | Archivos que le pertenecen | US que desbloquea |
|---|---|---|---|
| **Lucero Ayala** | Motor de puntuación | `scoring.py` | US2, US4 |
| **Jose Cabrera** | Persistencia (dueño único del esquema SQL) | `database.py` | US1, US3 |
| **Piero Calderón** | Rutas Flask + despliegue | `app.py`, `wsgi_pythonanywhere.py` | todas |
| **Ana Cusi** | Vistas, estilos y frontend | `templates/` (3), `static/css/`, `static/js/` | todas |

**Orden sugerido:** Jose y Lucero primero. Sin datos reales ni puntajes reales,
Ana maqueta a ciegas y Piero no puede probar nada de verdad. Ideal: sus dos
módulos en `main` al final del día 2.

---

## 🧮 Lucero — `scoring.py`

Implementar el cuerpo de las dos funciones que hoy son stubs.

**Qué hacer**
1. `calculate_score(task, available_minutes)` → devuelve `(total, breakdown)`.
2. `rank_tasks(tasks, available_minutes)` → ordena por puntaje ↓, luego
   `due_date` ↑, luego `id` ↑.

**La fórmula ya está definida en Elaboration — no la cambies ni la "mejores":**

| Componente | Regla |
|---|---|
| Prioridad | 1 Alta = 50 · 2 Media = 30 · 3 Baja = 10 |
| Urgencia | vencida u hoy = 40 · mañana = 20 · en 2–3 días = 10 · más de 3 = 5 |
| Ajuste de tiempo | +15 si `estimated_minutes <= available_minutes`, si no 0 |

**Dos trampas ya señaladas en el archivo**
- Usa `today_local()`, **nunca** `datetime.now()`. El servidor corre en UTC y
  Lima es UTC−5: después de las 7 p.m. una tarea de hoy se marcaría como vencida.
- El orden debe ser **determinista**: la misma entrada siempre produce la misma
  salida. Por eso el desempate tiene tres niveles.

**Listo cuando:** agregas al final del archivo 6 `assert` que cubran tarea
vencida, tarea de hoy, tarea a 5 días, empate exacto y ambos lados del bono de
tiempo. Esos asserts son la evidencia de la fase de Testing.

**No toques:** `app.py`, `database.py`, ni el diccionario `breakdown` (su forma
es contrato con el frontend de Ana).

---

## 🗄️ Jose — `database.py`

Tres funciones siguen vacías: `update_status()`, `delete_task()` y
`get_daily_progress()`. Las otras tres ya funcionan y te sirven de referencia de
estilo.

**Qué hacer**
1. `update_status(task_id, new_status)` → `UPDATE`, devuelve `True` si actualizó.
   Valida que `new_status` sea `pending`, `in_progress` o `completed`.
2. `delete_task(task_id)` → `DELETE` por id.
3. `get_daily_progress()` → devuelve `{"total": n, "completed": n, "percent": n}`.
   Cuidado con la división entre cero cuando no hay tareas.

**Eres el dueño único del esquema.** Si cambia el `CREATE TABLE`, lo cambias tú
y **avisas al grupo**, porque todos tienen que borrar su `vibe_planner.db` local
y dejar que se regenere.

**Reglas:** SQL puro, sin ORM. Una conexión por petición (nunca una conexión
global compartida). La ruta de la base de datos es absoluta y ya está calculada.

**Listo cuando:** puedes crear una tarea, cambiarle el estado, borrarla, reiniciar
el servidor y comprobar que los datos siguen ahí.

---

## 🛣️ Ana — `app.py` + despliegue

Las rutas ya están cableadas y funcionando. Falta endurecerlas y publicar.

**Qué hacer**
1. Validación en servidor en `add_task_route()`: título no vacío,
   `estimated_minutes` entero > 0, `due_date` en formato `YYYY-MM-DD`.
   Si algo falla, no insertar y mostrar el error al usuario.
2. Despliegue en PythonAnywhere usando `wsgi_pythonanywhere.py` como referencia.
3. Administrar el repo: colaboradores, revisión de Pull Requests, merge diario.

**Listo cuando:** la app está en línea, las 4 historias funcionan sobre el
entorno desplegado, y el enlace está en el README.

---

## 🎨 Piero — `templates/` + `static/`

Cinco archivos, toda la capa de vista. El HTML actual está deliberadamente feo
para que lo reemplaces; la estructura y los `name=` son los que ya funcionan.

**Qué hacer**
1. `static/css/style.css` — aplicar la guía visual de más abajo.
2. `templates/index.html` — maquetar formulario, tarjetas y barra de progreso.
3. `templates/score_modal.html` — el modal de explicabilidad (US4). **Es la
   pantalla más importante del producto:** es donde se ve la diferencia con
   Todoist y Motion.
4. `static/js/main.js` — ya consume la API correctamente; mejora la presentación.

**Puedes empezar sin esperar a nadie:** `main.js` ya recibe la estructura final
del `breakdown`, así que maquetas contra datos reales de forma aunque los
puntajes salgan en 0.

**No cambies** los atributos `name=` de los formularios ni los `id=` que usa
`main.js` (`score-modal`, `modal-total`, `modal-breakdown`, `modal-close`).
Si necesitas cambiar uno, avisa a Piero.

**Listo cuando:** el modal muestra las tres componentes del puntaje y la suma
coincide con la insignia de la tarjeta.

---

## 🎨 Guía Visual

### Decisión de diseño

La fórmula tiene tres componentes. **Cada componente tiene un color propio, y
ese color se usa en todos los lugares donde ese componente aparece**: la
insignia de prioridad, el texto de la fecha límite y el modal de desglose. El
usuario aprende a leer el ranking sin que nadie se lo explique.

| Componente | Color | Dónde aparece |
|---|---|---|
| Prioridad | Violeta | insignia de prioridad · barra del modal |
| Urgencia | Ámbar | fecha límite · barra del modal |
| Ajuste de tiempo | Verde azulado | duración estimada · barra del modal |

Un cuarto color, **coral**, se reserva solo para *vencida*. Si se usa en otro
lado pierde su fuerza de alerta.

### Paleta

| Token | Hex | Uso |
|---|---|---|
| `--fondo` | `#12151C` | fondo de la página |
| `--superficie` | `#1B2029` | tarjetas, modal |
| `--superficie-alta` | `#232935` | hover, campos de formulario |
| `--borde` | `#2E3543` | bordes de 1px |
| `--texto` | `#E7EAF0` | texto principal |
| `--texto-suave` | `#98A1B3` | metadatos, etiquetas |
| `--prioridad` | `#8B7CF6` | violeta — componente prioridad |
| `--urgencia` | `#F5A524` | ámbar — componente urgencia |
| `--tiempo` | `#2DD4A7` | verde azulado — componente tiempo |
| `--alerta` | `#F2555A` | coral — **solo** tareas vencidas |

### Variables listas para pegar

```css
:root {
  --fondo:           #12151C;
  --superficie:      #1B2029;
  --superficie-alta: #232935;
  --borde:           #2E3543;

  --texto:           #E7EAF0;
  --texto-suave:     #98A1B3;

  --prioridad:       #8B7CF6;
  --urgencia:        #F5A524;
  --tiempo:          #2DD4A7;
  --alerta:          #F2555A;

  --radio:           10px;
  --sombra:          0 1px 3px rgba(0,0,0,.4);

  /* Sin CDN: PythonAnywhere free tier no tiene red saliente.
     Solo tipografías del sistema. */
  --fuente:      system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --fuente-dato: ui-monospace, "SF Mono", "Cascadia Mono", Consolas, monospace;
}
```

### Reglas de aplicación

**Niveles de prioridad** — misma familia violeta, distinta intensidad. No son
tres colores sueltos: son la misma idea con más o menos peso.

| Nivel | Tratamiento |
|---|---|
| Alta | fondo `--prioridad` sólido, texto `#12151C` |
| Media | fondo `--prioridad` al 22 % (`#8B7CF638`), texto `--prioridad` |
| Baja | solo borde `--prioridad`, texto `--texto-suave` |

**El puntaje va en `--fuente-dato`.** Los números en monoespaciada se alinean
verticalmente entre tarjetas, y eso hace el ranking comparable de un vistazo.
Es coherente con la promesa del producto: un puntaje auditable.

**Las tareas completadas se apagan**, no se celebran: `opacity: .45` y
`text-decoration: line-through`. Lo terminado tiene que ceder el protagonismo a
lo que falta.

**El color nunca es la única señal.** Cada insignia lleva su texto
("Alta", "Vence hoy"). Hay daltonismo rojo-verde en aproximadamente 1 de cada
12 hombres.

### Textos de la interfaz

- Botones en voz activa y sentence case: "Agregar actividad", no "Enviar".
- El estado vacío es una invitación, no un lamento: *"Aún no hay actividades.
  Agrega la primera y verás tu plan del día ordenado."*
- Los errores dicen qué pasó y cómo arreglarlo: *"La duración debe ser mayor a
  0 minutos."*

---

## 🔒 Reglas que no se rompen

1. La instancia de Flask se llama **exactamente `app`** a nivel de módulo.
   PythonAnywhere hace `from app import app`. Sin application factory.
2. `vibe_planner.db` **nunca** se sube al repo.
3. Sin APIs externas, sin CDN, sin gunicorn. Solo Flask y librería estándar.
4. Toda la lógica de puntuación vive **solo** en `scoring.py`.
5. Cada uno crea **su propio** entorno virtual. El `venv/` no se sube; lo que se
   comparte es `requirements.txt`.

## 🔀 Git

```bash
git checkout -b feature/tu-modulo
git add .
git commit -m "descripcion clara de lo que hiciste"
git push origin feature/tu-modulo
# luego Pull Request en GitHub
```

**Merge a `main` todos los días**, aunque tu parte esté incompleta. Los
conflictos de un día se resuelven en cinco minutos; los de una semana, no.

## 📝 Evidencia para Construction

Cada prompt que uses con la IA va en `docs/prompts/` **el mismo día**. La rúbrica
exige prompts reales y un ejemplo de código que la IA generó mal. Eso no se
reconstruye de memoria el viernes.