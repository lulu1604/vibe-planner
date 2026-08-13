# Validación de Rutas Flask (app.py) - Ana Cusi - 2026-08-13

## Prompt usado

"En `app.py` de VibePlanner endurece la validación en servidor de `add_task_route()`. Reglas: título no vacío y de máximo 120 caracteres; `due_date` en formato `YYYY-MM-DD` **que además sea una fecha real**; `estimated_minutes` entero mayor que 0; `priority_level` solo 1, 2 o 3. Si algo falla, **no insertes nada** y muestra el error al usuario con `flash()`, en español, diciendo qué pasó y cómo arreglarlo.

Restricciones que no puedes romper: la instancia de Flask se llama exactamente `app` a nivel de módulo (PythonAnywhere hace `from app import app`); no cambies nombres de rutas, ni las variables que recibe `index.html` (`tasks`, `available_minutes`, `progress`), ni las claves del JSON (`id`, `total`, `breakdown`) porque son contrato con el frontend; sin librerías externas, solo Flask y librería estándar; la lógica de puntuación vive solo en `scoring.py`.

Agrega al final una suite de `assert` ejecutable con `python app.py test` que corra sobre una base temporal."

## Qué generó la IA

La estructura completa: el helper `_validar_formulario_tarea()` que devuelve `(datos, errores)`, los `flash()` por cada error, el helper `_leer_minutos_disponibles()` con acotado de rango, y la suite de 11 asserts sobre una base temporal creada con `tempfile`.

## Qué corregí y por qué

**1. Validaba la fecha con una expresión regular.** La primera versión comprobaba el patrón `\d{4}-\d{2}-\d{2}`, que acepta `2026-02-31`: tiene el formato correcto pero esa fecha no existe. Lo reemplacé por `datetime.strptime(fecha, "%Y-%m-%d")`, que sí la rechaza. Quedó como el Assert 3 justamente para que nadie lo "simplifique" de vuelta a una regex.

**2. No distinguía "campo vacío" de "campo no numérico".** Usaba `request.form.get("estimated_minutes", 30, type=int)`, y Flask devuelve el valor por defecto cuando la conversión falla — así que escribir `abc` en la duración se guardaba silenciosamente como 30 minutos, sin avisar. Ahora leo primero el texto crudo: si viene vacío uso 30, pero si trae algo que no es número, es un error explícito.

**3. Los mensajes de error eran genéricos.** Generó cosas como `"Invalid input"`. El `reparto.md` pide que los errores digan qué pasó y cómo arreglarlo, así que los reescribí: `"La duración debe ser mayor a 0 minutos."` y `"La fecha «2026-02-31» no es válida. Usa el formato AAAA-MM-DD, por ejemplo 2026-08-20."`

**4. Faltaba el assert que protege el contrato.** Agregué el Assert 9, que verifica que el JSON del endpoint de desglose siga teniendo exactamente las claves `{id, total, breakdown}`. Si alguien cambia esa forma, la prueba falla antes de que se rompa el `main.js` del frontend en producción.

## Apareció en local o solo en producción?

Los cuatro aparecieron en local, corriendo `python app.py test`. El de la fecha del 31 de febrero es el más interesante: **el código se veía correcto en la revisión** y solo se cayó cuando escribí el assert con esa fecha concreta. Es exactamente el riesgo #3 de Inception — código generado por IA que parece correcto y contiene rutas no probadas.

## Efecto secundario detectado

Al implementar `flash()` descubrí que **ninguna plantilla renderiza `get_flashed_messages()`**, así que los mensajes se generaban y se perdían en silencio. Como `templates/` no es mi archivo, no lo modifiqué: dejé el bloque de 6 líneas documentado en `docs/para_piero_mensajes.md` para que lo integre Piero.
