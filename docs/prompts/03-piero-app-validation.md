# Rutas y Validación de Servidor (app.py) - Piero Calderón - 2026-08-12

## Prompt usado
"Implementa la validación en el servidor dentro de la ruta `add_task_route` en `app.py`. Debe verificar que el título no esté vacío, que `estimated_minutes` sea un entero positivo mayor a 0, y que `due_date` tenga un formato válido YYYY-MM-DD. Si algún campo falla, debe retornar un mensaje de error o redireccionar sin insertar datos corruptos en SQLite."

## Qué generó la IA
Generó una función de validación `validate_task_data(form_data)` que comprueba la presencia del título, castea y valida `estimated_minutes > 0`, y parsea `due_date` con `datetime.strptime`. En caso de fallo, la ruta `add_task_route` maneja la respuesta devolviendo un código de estado 400 con un mensaje de error explicativo.

## Qué corregí y por qué
Se corrigió la redirección en caso de error para que la aplicación muestre un mensaje flash descriptivo ("La duración debe ser mayor a 0 minutos") en lugar de un error HTTP 500 no capturado, mejorando la experiencia del usuario final conforme a las reglas del proyecto.

## Apareció en local o solo en producción?
Apareció durante las pruebas locales al intentar enviar el formulario con campos vacíos o con minutos negativos.
