# 🌱 MÓDULO D — Hábitos, métricas y Design System

**Dueña propuesta:** Ana Cusi
**Historias:** US13 (hábitos) · US14 (métricas del día) · US15 (métricas del sistema) · US16 (responsive)
**Depende de:** Módulo A (H2) para arrancar · Módulos B y C para cerrar las métricas

---

## 🎯 Qué construyes

Dos cosas que se complementan: el módulo que convierte tareas sueltas en
**rutinas sostenidas** (hábitos con rachas), el que responde *"¿cómo me fue hoy?"*
(métricas por sección), y — transversal a todo el proyecto — el **design system**
que hace que las 8 pantallas se vean como una sola aplicación.

> ⚠️ **Esta es la carga más repartida del equipo:** tienes un módulo funcional
> mediano **más** el trabajo transversal de diseño. Si al arrancar ves que no
> entra, plantéalo el primer día en la reunión: el design system puede pasar a
> quien cierre antes su módulo. Descubrirlo el jueves es tarde.

---

## 📁 Archivos que te pertenecen

| Archivo | Qué contiene |
|---|---|
| `repo_habits.py` | Único componente que toca `habits` y `habit_logs` |
| `metrics.py` | Métricas del día, rachas y agregados del sistema |
| `habits.py` | Blueprint: `/habitos`, `/metricas` |
| `templates/habitos/` | Hábitos con racha, panel de métricas |
| `templates/base.html` | 🎨 Shell responsive: sidebar + topbar + bottom nav |
| `templates/components/` | 🎨 Tarjeta, insignia, modal, formulario, estado vacío |
| `static/css/tokens.css` | 🎨 Variables: las dos paletas, tipografía, espaciado |
| `static/css/base.css` | 🎨 Reset, tipografía, layout responsive |
| `static/css/components.css` | 🎨 Componentes compartidos |
| `static/fonts/` | 🎨 Inter y JetBrains Mono en `.woff2` |

La especificación completa del diseño está en **`docs/VUP_V2/00_Design_System.md`**.
Todo lo que necesitas para `tokens.css` está ahí, listo para pegar.

---

## 📋 Parte 1 — Hábitos (US13)

### 1. `repo_habits.py` — contrato congelado

```python
def list_by_user(user_id)                       -> list[dict]
def get_owned(habit_id, user_id)                -> dict | None
def create(data, user_id)                       -> int
def upsert_log(habit_id, date_iso, value, done) -> bool
def logs_range(habit_id, from_iso, to_iso)      -> list[dict]
```

### 2. El registro diario es un `upsert`, no un `insert`

La tabla tiene `UNIQUE (habit_id, log_date)`. Corregir el valor de hoy **no puede**
crear una segunda fila (TC-34):

```python
def upsert_log(habit_id, date_iso, value, done):
    get_db().execute(
        """INSERT INTO habit_logs (habit_id, log_date, value, done)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(habit_id, log_date)
           DO UPDATE SET value = excluded.value, done = excluded.done""",
        (habit_id, date_iso, value, 1 if done else 0),
    )
```

### 3. La racha cuenta días **consecutivos**

Este es el error clásico que la IA genera: contar cuántos días cumpliste en total
en vez de cuántos seguidos.

```python
def habit_streak(habit_id, today_iso):
    """Días consecutivos terminando HOY (o ayer, si hoy aún no se marcó)."""
    logs = {row["log_date"] for row in logs_range(habit_id, ...) if row["done"]}
    streak = 0
    cursor = date.fromisoformat(today_iso)
    if cursor.isoformat() not in logs:
        cursor -= timedelta(days=1)      # hoy aún no se marcó: se cuenta hasta ayer
    while cursor.isoformat() in logs:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
```

Con cumplimientos el 17 y el 19 pero **no** el 18, la racha del día 19 es **1**,
no 2 (TC-36). Con el 17, 18 y 19 cumplidos y hoy siendo el 20 sin marcar, la racha
es **3**; al marcar hoy, **4** (TC-35).

### 4. Los cuatro tipos

`dieta` · `ejercicio` · `relajacion` · `sueno` (más `general`). Cada uno con su
meta y unidad: "Dormir **8 horas**", "Tomar **8 vasos** de agua", "Ejercicio
**30 minutos**". El `CHECK` del esquema los valida.

> 📌 El tipo se guarda como `sueno` sin tilde — las tildes en valores de base de
> datos causan problemas de codificación. En pantalla se muestra "Sueño".

---

## 📋 Parte 2 — Métricas (US14, US15)

### 5. `metrics.py` — contrato congelado

```python
def daily_summary(user_id, date_iso) -> dict   # por sección + %
def habit_streak(habit_id, today_iso) -> int
def system_metrics() -> dict                   # solo agregados
```

`daily_summary()` devuelve:

```python
{
  "secciones": {
      "Trabajo":     {"completadas": 3, "total": 4},
      "Personal":    {"completadas": 1, "total": 2},
      "Actividades": {"completadas": 2, "total": 2},
  },
  "tareas":  {"completadas": 6, "total": 8, "porcentaje": 75.0},
  "habitos": {"marcados": 2, "total": 3},        # ← indicador SEPARADO
  "eventos": 3,
}
```

### 6. División entre cero — el defecto más probable del módulo

```python
porcentaje = round(completadas / total * 100, 1) if total > 0 else 0.0
```

Una cuenta recién creada abre `/metricas` con cero de todo. Si eso da un 500, es
lo primero que ve un usuario nuevo (TC-38). Protege **todos** los porcentajes, no
solo el principal.

### 7. Los hábitos no entran en el porcentaje de tareas

Son dos indicadores distintos: "6 de 8 tareas (75 %)" y "2 de 3 hábitos". Mezclar
ambos hace que el número deje de significar nada (TC-39).

### 8. Métricas del sistema: solo agregados

```python
def system_metrics():
    return {
        "usuarios_total":  ...,   # COUNT(*) FROM users
        "usuarios_activos":...,   # WHERE is_active = 1
        "eventos_total":   ...,   # COUNT(*) FROM events
        "usaron_hoy":      ...,   # COUNT(DISTINCT user_id) de tasks movidas hoy
    }
```

> 🔒 **Nunca el contenido de nadie.** Ni títulos de tareas, ni nombres de eventos,
> ni datos de un usuario concreto — tampoco escondidos en el HTML "por si acaso"
> (TC-41). Administrar el sistema no es leer la vida privada de las personas.
> Revisa el HTML fuente de la página antes de dar el caso por bueno.

La ruta va protegida con `@requires("metrica.sistema.ver")`, y las métricas
propias con `@requires("metrica.propia.ver")`.

---

## 🎨 Parte 3 — Design System (US16)

### 9. Los tres archivos CSS, en este orden

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/tokens.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/components.css') }}">
```

`tokens.css` está completo en `00_Design_System.md` § 4. Cópialo tal cual.

### 10. Mobile-first, sin excepciones

El CSS base es el de móvil y los `@media (min-width: …)` van añadiendo. Al revés
siempre termina en un móvil lleno de parches.

| Ancho | Navegación | Contenido |
|---|---|---|
| `< 600px` | Barra inferior, 5 iconos | Una columna · Kanban apilado |
| `600–1023px` | Sidebar colapsado a iconos | Dos columnas donde quepa |
| `≥ 1024px` | Sidebar fijo y etiquetado | Máx. 1200 px |

### 11. Las dos paletas y su regla

> **El azul es la aplicación. El rosa es la importancia.**

Y la corrección de contraste que **no** puedes saltarte: `#D7707F` da 3.20:1 sobre
blanco y **no** cumple AA para texto. Es relleno y borde. Para texto se usa el
derivado `--rose-700: #9E3B4B` (6.60:1). Lo mismo con Teal `#567C8D` (4.49:1 →
usa `--teal-700: #3F5F6E`) y con Cool Steel (2.56:1 → solo bordes).

### 12. El color nunca es la única señal

Cada insignia lleva **también su texto**: "Alta", "Vence hoy", "En curso".
Alrededor de 1 de cada 12 hombres tiene daltonismo rojo-verde, y las dos paletas
del producto son azul y rosa: en escala de grises se confunden. Compruébalo con el
filtro de escala de grises del navegador (TC-45).

---

## 🕳️ Trampas concretas de este módulo

1. **División entre cero en todos los porcentajes**, no solo en el principal.
2. **La racha son días consecutivos**, no cumplimientos totales.
3. **El registro diario es `upsert`**, no `insert`.
4. **Los hábitos no entran en el porcentaje de tareas.**
5. **Las métricas del sistema no exponen contenido**, ni siquiera en el HTML.
6. **Campos de formulario a 16 px como mínimo**: por debajo, iOS hace zoom al enfocar.
7. **Nunca `outline: none` sin sustituto.** Quien navega con teclado necesita ver
   dónde está.
8. **Ningún hex suelto** en el CSS de un componente: todo sale de `tokens.css`.
9. **Cero lógica de negocio en las plantillas.** Ningún cálculo dentro de `{{ }}`:
   eso vive en `metrics.py`, donde se puede probar.

---

## ✅ Listo cuando

**Hábitos y métricas**
- [ ] Se crean hábitos de los cuatro tipos con su meta y unidad (TC-33)
- [ ] Corregir el registro de hoy no duplica la fila (TC-34)
- [ ] La racha da 3 → 4 al marcar hoy (TC-35) y se rompe con un hueco (TC-36)
- [ ] Las métricas agrupan por Trabajo / Personal / Actividades y dan 75 % (TC-37)
- [ ] Una cuenta vacía muestra 0 % **sin error 500** (TC-38)
- [ ] Los hábitos se reportan aparte del porcentaje de tareas (TC-39)
- [ ] Los números del panel de admin coinciden con `SELECT COUNT(*)` (TC-40)
- [ ] El panel no expone contenido de nadie, ni en el HTML fuente (TC-41)
- [ ] Sin el permiso, `/admin/metricas` responde 403 (TC-42)

**Design System**
- [ ] `tokens.css` con las dos paletas, la escala y el espaciado
- [ ] Las 8 pantallas sin scroll horizontal a 360 px (TC-43)
- [ ] Kanban apilado en móvil, en cuatro columnas en escritorio (TC-43)
- [ ] Sidebar colapsado a 768 px, fijo a 1280 px (TC-44)
- [ ] Contraste ≥ 4.5:1 en todo texto normal (TC-45)
- [ ] Toda insignia legible en escala de grises (TC-45)
- [ ] Fuentes `.woff2` auto-alojadas, sin ningún CDN
- [ ] Las 5 pantallas tienen estado vacío diseñado (TC-18)
