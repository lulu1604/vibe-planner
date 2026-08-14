# Evidencia de uso de IA — Módulo D (Hábitos, Métricas y Design System)

**Autora:** Ana Cusi · **Fecha:** 13 de agosto de 2026
**Historias:** US13, US14, US15, US16 · **Casos:** TC-33 … TC-45

Los prompts completos están en `docs/VUP_V2/prompts_Ana/` (D1 … D8). Aquí va lo
que exige la rúbrica: qué se pidió, qué devolvió la IA, y qué se aceptó, cambió
o rechazó **con el porqué**.

---

## Cómo se trabajó

En vez de pegar cada prompt a mano, se le dio a la IA acceso al repositorio y se
le pidió leer primero `00_CONTEXTO_BASE_ANA.md` y luego ejecutar cada paso. El
propio README de la carpeta contempla este atajo, y su razón se confirmó: la IA
se equivoca menos leyendo los archivos reales que fiándose de lo que se le
cuente. Dos de los tres errores documentados abajo salieron precisamente de
**documentos desactualizados**, no del código.

---

## D1 — Esquema `habits` y `habit_logs`

**✅ ACEPTADO**
- El bloque DDL tal cual lo especificaba el prompt, al final de `schema_v2.sql`.
  `git diff --numstat` confirmó **35 líneas añadidas, 0 eliminadas**: puramente
  aditivo, que era la condición para no chocar con Jose (dueño del esquema).
- `UNIQUE (habit_id, log_date)`: es lo que hace posible TC-34. Corregir el
  registro de hoy actualiza la fila en vez de crear una segunda, y la garantía
  vive en la base, que no se olvida nunca — un `if` en Python sí.

**🔄 CAMBIADO**
- Se añadieron dos comentarios que el prompt no pedía: uno explicando por qué
  `sueno` va sin tilde y otro por qué existe el `UNIQUE`. Un `CHECK` sin
  explicación es lo primero que alguien "arregla" mal dentro de seis meses.

**Verificación:** sobre una base temporal se comprobó que el duplicado lanza
`IntegrityError`, que el `ON CONFLICT DO UPDATE` deja 1 fila con valor 8.0, y
que `habit_type='sueño'` (con tilde) es rechazado por el `CHECK`.

---

## D2 — `repo_habits.py`

**✅ ACEPTADO**
- Las 5 firmas congeladas más los 2 auxiliares de lectura.
- `upsert_log` con `ON CONFLICT … DO UPDATE`. **La IA no cometió el error que el
  prompt anticipaba** (`SELECT` y luego decidir), porque el prompt traía el
  fragmento correcto escrito.

**🔄 CAMBIADO**
- Se añadió una tercera función auxiliar, `logs_range_by_user(user_id, from, to)`,
  que el prompt no contemplaba. Sin ella, la pantalla de D4 necesitaba una
  consulta por hábito para la tira de 7 días y otra para la racha: N+1 puro.
  Es **aditiva** — no cambia ninguna firma congelada — así que no requería
  avisar al grupo.

**❌ RECHAZADO**
- Nada relevante en este paso.

### Código que generó mal *(evidencia para la rúbrica)*

El bloque de asserts terminaba borrando la base temporal así:

```python
os.unlink(ruta_temporal)
```

Falló en Windows con `PermissionError: [WinError 32] El proceso no tiene acceso
al archivo porque está siendo utilizado por otro proceso`. Corrección:

```python
        # Windows no borra un archivo con la conexión abierta, y el modo WAL
        # deja además dos ficheros satélite.
        database.close_db()

    for sufijo in ("", "-wal", "-shm"):
        try:
            os.unlink(ruta_temporal + sufijo)
        except OSError:
            pass
```

**Por qué estaba mal:** dos motivos que se acumulan. La conexión de `flask.g`
seguía abierta, y Windows —a diferencia de Linux— no permite borrar un archivo
en uso. Además `journal_mode = WAL` (que `database.py` aplica a toda conexión)
crea `-wal` y `-shm`, que también quedaban colgando. Los 5 asserts **habían
pasado**: el fallo estaba solo en la limpieza, que es justo el tipo de error que
un `SUCCESS` apresurado deja pasar.

---

## D3 — `metrics.py`

**✅ ACEPTADO**
- `_porcentaje()` como única división del archivo. Verificado con búsqueda: hay
  exactamente **una** división en todo `metrics.py`, dentro de esa función.
- El fallback de `tasks` con `_columnas()` + `PRAGMA table_info`. Es lo que
  permite que `/metricas` funcione hoy y se llene sola cuando el Módulo B migre
  la tabla, sin tocar una línea de aquí.
- `hoy_iso()` con `zoneinfo` y respaldo a offset fijo −5.

**🔄 CAMBIADO**
- Se extrajo `racha_desde_logs(fechas, today_iso)` de `habit_streak`, que ahora
  delega en ella. Motivo: D4 necesita calcular las rachas de todos los hábitos
  desde logs ya en memoria. La firma congelada `habit_streak(habit_id, today_iso)`
  **no se tocó** — solo se le sacó el cuerpo a una función nueva.
- El mensaje final decía *"Todas las 6 pruebas pasaron"* incluso cuando TC-37 se
  omitía. Se cambió a *"5 de 6 … (1 omitida)"*: un resumen que cuenta como
  pasada una prueba que no se ejecutó es peor que no tener resumen.

**❌ RECHAZADO**
- La tentación de añadir `user_id` a `tasks` para que TC-37 pasara. Esa tabla es
  del Módulo B y del dueño del esquema. Se resolvió con degradación honesta.

---

## D4, D5, D6 — Blueprint y pantallas

**✅ ACEPTADO**
- `Blueprint("habitos")` con las vistas `lista`, `crear`, `registrar`,
  `metricas`, `metricas_sistema`. Los nombres coinciden con lo que `home.py`
  tenía reservado, y la entrada del menú se encendió.
- 404 (no 403) para el hábito ajeno, `user_id` siempre desde la sesión, y
  `_csrf` en los tres formularios.
- La vista `lista` hace exactamente **3 consultas**, no una por hábito.

**🔄 CAMBIADO** *(dos correcciones propias, no de la IA)*

1. **La clase de solo-lectura estaba mal escrita.** Se usó `.solo-lector`; la que
   existe en `base.css:86` es `.solo-lectores`, en plural. Con el nombre
   equivocado, los `aria-label` de las 7 casillas se habrían **pintado como
   texto visible** dentro de cada cuadrito, reventando la maquetación — un fallo
   silencioso, porque el CSS que no existe no da error.

2. **El formulario de marcar impedía corregir.** La primera versión llevaba
   `done` en un `<input type="hidden">` con el valor invertido, así que un hábito
   ya marcado solo se podía **desmarcar**: enviar un valor corregido lo apagaba.
   Eso contradice TC-34, que exige poder cambiar el 7 por un 8. Se movió `done`
   al propio botón:

   ```jinja
   {% if habito.marcado_hoy %}
     <button type="submit" name="done" value="1">Guardar</button>
     <button type="submit" name="done" value="0">Desmarcar</button>
   {% else %}
     <button type="submit" name="done" value="1">Marcar hoy</button>
   {% endif %}
   ```

   **Por qué estaba mal:** el código era válido y la prueba de TC-34 a nivel de
   base de datos habría pasado igual (el `upsert` no duplica), pero **por la
   interfaz era imposible llegar al caso**. Un test verde sobre una función que
   el usuario no puede alcanzar no prueba nada.

---

## D7 — Design System

**❌ RECHAZADO — tres tareas del prompt que ya no procedían**

Este fue el hallazgo más útil del módulo: **el prompt D7 y
`00_HALLAZGOS_Y_RIESGOS.md` describían un repositorio que ya no existe.**
Ejecutarlos al pie de la letra habría significado "arreglar" cosas correctas.

| Lo que el documento mandaba | Lo que hay en el código |
|---|---|
| Quitar el hex suelto de `components.css` | Está **dentro de un comentario** que explica un ratio. 0 hex en declaraciones. |
| Dar a Jose la tabla de reemplazos de las 6 clases Tailwind de `mes.html` | Ya está reescrito sobre el design system. Esos nombres solo sobreviven en el comentario que documenta el arreglo. |
| Corregir el endpoint `calendario.mes` del menú | `home.py:58` ya usa `calendar_bp.index`, con el porqué comentado. |

**🔄 CAMBIADO**
- El prompt mide `--teal` contra blanco (4.49:1). El fondo real de la aplicación
  es `--beige`, donde da **3.95:1**: falla por más margen del documentado. La
  auditoría recalcula todo contra el fondo real.

**✅ ACEPTADO**
- Los 8 componentes nuevos del módulo pasan AA con ratios medidos, no estimados.
  El más ajustado es `.badge--marcado` con 4.73:1.

---

## D8 — Pruebas

**✅ ACEPTADO**
- 10 casos, 9 en verde y TC-37 omitido con mensaje explícito.
- El helper `_post()` copiado de `test_v2.py:49`. Sin él, **todos** los POST
  darían 400: `auth.py` hace `session.clear()` al iniciar sesión y el token CSRF
  cambia.

**🔄 CAMBIADO**
- La documentación de D8 decía que ese helper estaba en `test_module_c.py`. No
  está: `test_module_c.py` aporta el patrón de base temporal, y el helper vive
  en `test_v2.py`.

---

## Patrones observados en la IA

| Patrón | Veces | Cómo se previno |
|---|---|---|
| Confiar en documentación desactualizada del propio repo | 4 | Verificar cada afirmación contra el código antes de actuar |
| Limpieza de archivos temporales que ignora Windows y WAL | 1 | Cerrar la conexión y borrar también `-wal`/`-shm` |
| Resumen que cuenta como pasada una prueba omitida | 1 | Contar por estado, no por total |
| Interfaz que impide llegar al caso que la prueba cubre | 1 | Recorrer el flujo como usuario, no solo mirar el assert |
| Nombre de clase CSS inventado en plural/singular | 1 | Comprobar contra el archivo, no contra la memoria |

**La conclusión que me llevo:** los errores de la IA en este módulo casi nunca
fueron de sintaxis ni de lógica — fue código plausible, ejecutable y verde en
las pruebas. Lo que falló fue el *contexto*: documentos que envejecieron y un
formulario que no dejaba llegar al caso probado. Revisar la salida contra el
código real, y no contra lo que el documento dice del código, es lo que separó
un módulo correcto de uno que solo lo parecía.
