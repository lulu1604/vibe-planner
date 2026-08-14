# D3 — `metrics.py`: rachas, resumen del día y agregados del sistema

**Objetivo:** el cerebro del módulo. Aquí vive **toda** la lógica de negocio de
hábitos y métricas, para que las plantillas no calculen nada y las pruebas
puedan comprobarlo sin levantar el servidor.

**Archivos que salen de aquí:** `metrics.py`

**Tiempo estimado:** 3 horas

**Depende de:** D2 terminado

> 🔔 **Este es el hito del módulo.** Cuando `metrics.py` esté en `main`, avísale
> al grupo: es lo que Piero necesita para llenar las cifras del home, que hoy
> muestran `—`.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Genera `metrics.py`, la lógica de negocio del Módulo D. Lee antes
`repo_habits.py` (lo acabo de escribir) y `database.py`. Este archivo **no** tiene
rutas ni HTML: solo funciones puras que reciben datos y devuelven diccionarios.

### 1. Contrato congelado

```python
def daily_summary(user_id, date_iso) -> dict   # por seccion + %
def habit_streak(habit_id, today_iso) -> int   # dias CONSECUTIVOS
def system_metrics() -> dict                   # solo agregados
```

### 2. `habit_streak` — días **consecutivos**, no cumplimientos totales

Este es el error clásico que la IA genera: contar cuántos días cumpliste en total
en vez de cuántos seguidos.

```python
def habit_streak(habit_id, today_iso):
    """Dias consecutivos terminando HOY (o ayer, si hoy aun no se marco)."""
    hoy = date.fromisoformat(today_iso)
    desde = (hoy - timedelta(days=VENTANA_RACHA)).isoformat()
    logs = {fila["log_date"] for fila in repo_habits.logs_range(habit_id, desde, today_iso)
            if fila["done"]}

    racha = 0
    cursor = hoy
    if cursor.isoformat() not in logs:
        cursor -= timedelta(days=1)      # hoy aun no se marco: se cuenta hasta ayer
    while cursor.isoformat() in logs:
        racha += 1
        cursor -= timedelta(days=1)
    return racha
```

Comportamiento que debe cumplirse exactamente:

- Cumplidos el 17, 18 y 19; hoy es el 20 **sin marcar** → racha **3**. Al marcar
  hoy → **4** (TC-35).
- Cumplidos el 17 y el 19 pero **no** el 18; hoy es el 19 → racha **1**, no 2
  (TC-36).
- Sin ningún registro → **0**, sin excepción ni error.

`VENTANA_RACHA` es una constante (por ejemplo 400 días): una racha no se busca
hacia atrás hasta el principio de los tiempos, y sin ventana la consulta crece
sin límite. Comenta que ese es el motivo, y qué pasaría con una racha más larga
que la ventana.

### 3. `daily_summary` — la forma exacta del diccionario

```python
{
  "fecha": "2026-08-14",
  "secciones": {
      "Trabajo":     {"completadas": 3, "total": 4, "porcentaje": 75.0},
      "Personal":    {"completadas": 1, "total": 2, "porcentaje": 50.0},
      "Actividades": {"completadas": 2, "total": 2, "porcentaje": 100.0},
  },
  "tareas":  {"completadas": 6, "total": 8, "porcentaje": 75.0},
  "habitos": {"marcados": 2, "total": 3},        # <- indicador SEPARADO, sin %
  "eventos": 3,
  "tareas_conectadas": True,
}
```

### 4. División entre cero — el defecto más probable del módulo

```python
porcentaje = round(completadas / total * 100, 1) if total > 0 else 0.0
```

Una cuenta recién creada abre `/metricas` con cero de todo. Si eso da un 500, es
lo primero que ve un usuario nuevo (TC-38). **Protege todos los porcentajes**, no
solo el principal: el de cada sección también. Escribe una función
`_porcentaje(parte, total)` y úsala en todos los sitios; que no haya ni una
división suelta en el archivo.

### 5. Los hábitos NO entran en el porcentaje de tareas

Son dos indicadores distintos: *"6 de 8 tareas (75 %)"* y *"2 de 3 hábitos"*.
Mezclarlos hace que el número deje de significar nada (TC-39). Por eso
`"habitos"` no lleva clave `porcentaje`: si no existe, nadie la puede sumar por
descuido.

### 6. La tabla `tasks` todavía no tiene `user_id` — resuélvelo sin mentir

El Módulo B (Lucero) aún no ha migrado `tasks`: hoy tiene solo
`id, title, category, priority_level, due_date, estimated_minutes, status,
created_at`. **No la modifiques: no es mi archivo.**

En su lugar, pregunta a SQLite qué columnas existen antes de consultar:

```python
def _columnas(tabla):
    """Las columnas que la tabla tiene AHORA MISMO.

    Preguntar en vez de suponer permite que /metricas funcione hoy y se llene
    sola en cuanto el Modulo B anada user_id, sin tocar una linea de aqui.
    """
    return {fila["name"] for fila in database.get_db().execute(f"PRAGMA table_info({tabla})")}
```

Reglas de comportamiento:

- Si `tasks` **tiene** `user_id`: consulta normal, con `WHERE user_id = ? AND
  due_date = ?`, agrupando por `category`. Una tarea cuenta como completada si
  `status = 'completed'` o, si la columna existe, `kanban_column = 'done'`.
- Si `tasks` **no tiene** `user_id`: devuelve `secciones` vacío, `tareas` en
  ceros y **`"tareas_conectadas": False`**. La pantalla dirá *"El módulo de
  actividades aún no está conectado"* en vez de enseñar un 0 % que parece un dato
  real.
- El nombre de tabla del `PRAGMA` es una constante literal del módulo, nunca algo
  que venga de una petición.

Las secciones se ordenan **Trabajo, Personal, Actividades** primero y el resto de
categorías después, alfabéticamente. Que el orden sea estable importa: una
pantalla que reordena sus bloques en cada recarga se siente rota.

### 7. `system_metrics` — solo agregados

```python
def system_metrics():
    return {
        "usuarios_total":   ...,   # COUNT(*) FROM users
        "usuarios_activos": ...,   # WHERE is_active = 1
        "eventos_total":    ...,   # COUNT(*) FROM events
        "habitos_total":    ...,   # COUNT(*) FROM habits WHERE is_active = 1
        "usaron_hoy":       ...,   # COUNT(DISTINCT user_id) con actividad hoy
    }
```

> 🔒 **Nunca el contenido de nadie.** Ni títulos de tareas, ni nombres de
> eventos, ni datos de un usuario concreto (TC-41). Esta función devuelve
> **números y nada más**: si algún valor del diccionario es una cadena escrita
> por una persona, está mal.

`usaron_hoy` se calcula con lo que exista hoy: registros de hábitos de hoy
(`habit_logs.log_date = ?` con `JOIN habits`) más, si `tasks` ya tiene `user_id`,
las tareas con movimiento hoy. Cuenta **usuarios distintos**, no filas.

### 8. Zona horaria

La aplicación es para Lima. Una función `hoy_iso()` devuelve la fecha de **hoy en
`America/Lima`**, no `date.today()` a secas: el servidor de PythonAnywhere corre
en UTC y a partir de las 19:00 hora de Lima ya es "mañana" para él. Usa
`zoneinfo` de la librería estándar, con respaldo a un offset fijo de −5 si la
base de datos de zonas no está disponible (pasa en algunos Windows).

Esa función se usa en **todos** los sitios donde hoy se calcula la fecha actual,
y es lo que hace que la racha no se rompa sola a las siete de la tarde.

### 9. Asserts al final del archivo

Bloque `if __name__ == "__main__":` sobre base temporal, comprobando como mínimo:

1. Racha `3 → 4` al marcar hoy (TC-35).
2. Racha `1` con el hueco del día 18 (TC-36).
3. Racha `0` sin registros.
4. `daily_summary` de una cuenta vacía devuelve `0.0` y **no lanza** (TC-38).
5. `daily_summary` con 6 de 8 tareas da `75.0` y las secciones suman el total
   (TC-37) — sáltalo con un mensaje claro si `tasks` aún no tiene `user_id`.
6. `system_metrics()` devuelve solo valores numéricos: recórrelo y comprueba
   `isinstance(valor, (int, float))` para todas las claves (TC-41).

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | El resumen del día responde "¿cómo me fue hoy?" de un vistazo |
| **H2** Idioma del usuario | Las claves visibles son "Trabajo", "Personal", no `category_id` |
| **H5** Prevención de errores | Ninguna división sin proteger; ninguna fecha sin zona |
| **H9** Ayudar a reconocer errores | Estado "no conectado" explícito en vez de un 0 % engañoso |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿La racha cuenta cumplimientos totales?** Es el error clásico. Comprueba
   mentalmente el caso 17-19 sin el 18: debe dar **1**.
2. **¿La racha empieza en hoy aunque hoy no esté marcado?** Debe retroceder un
   día antes de contar, o un usuario que aún no ha marcado hoy ve su racha en 0 y
   piensa que la perdió.
3. **¿Hay alguna división sin `if total > 0`?** Búscalas todas, no solo la
   principal. Las de cada sección son las que se olvidan.
4. **¿Metió los hábitos en el porcentaje de tareas?** Recházalo (TC-39).
5. **¿`system_metrics` devuelve algún texto escrito por un usuario?** Recházalo:
   nombres, títulos y correos no entran ni "por si acaso" (TC-41).
6. **¿Usó `datetime.now()` sin zona?** En PythonAnywhere eso es UTC y desplaza el
   día cinco horas.
7. **¿Interpoló el nombre de tabla del `PRAGMA` desde algo que viene de fuera?**
   Debe ser una constante del módulo.
8. **¿Puso el cálculo de porcentajes en la plantilla?** Cero lógica en `{{ }}`.
9. **¿Consulta `habit_logs` directamente?** Debe pasar por `repo_habits`. La
   excepción justificable es `usaron_hoy`, que es un agregado del sistema: si la
   hace aquí, que quede comentado el porqué.

---

## ✅ Verificación del paso

```bash
python metrics.py
```

- [ ] Los 6 asserts pasan
- [ ] `grep -n "/ *total\|/ *len(" metrics.py` → toda división pasa por `_porcentaje`
- [ ] `grep -n "datetime.now()\|date.today()" metrics.py` → solo dentro de `hoy_iso()`
- [ ] `system_metrics()` devuelve **solo** números
- [ ] `python test_v2.py` sigue en verde

---

## 🤝 Al cerrar este paso, avisa al equipo

> `metrics.py` está en `main` con las tres funciones del contrato. Piero: ya
> puedes llenar las cifras del home con `metrics.daily_summary(user_id,
> metrics.hoy_iso())` — hoy muestran `—`. Lucero: en cuanto `tasks` tenga
> `user_id`, las secciones se llenan solas, no hay que tocar `metrics.py`.
