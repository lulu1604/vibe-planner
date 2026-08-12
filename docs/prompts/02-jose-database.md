# Capa de Persistencia y SQLite (database.py) - Jose Cabrera - 2026-08-12

## Prompt usado
"Implementa las funciones faltantes en database.py: update_status(task_id, new_status), delete_task(task_id) y get_daily_progress(). Asegúrate de validar los estados permitidos ('pending', 'in_progress', 'completed'), usar una conexión por petición con g.db, manejar la división por cero si no hay tareas y usar una ruta absoluta basada en __file__."

## Qué generó la IA
Generó las consultas SQL `UPDATE tasks SET status = ? WHERE id = ?` y `DELETE FROM tasks WHERE id = ?`, además del cálculo de progreso contando el total de tareas y las completadas para calcular el porcentaje.

## Qué corregí y por qué
Se corrigió un error en `get_daily_progress()` donde la división arrojaba `ZeroDivisionError` cuando la tabla de tareas estaba vacía al iniciar la app. Se agregó una verificación `if total == 0: return {"total": 0, "completed": 0, "percent": 0}`.

## Apareció en local o solo en producción?
Apareció en local al borrar todas las actividades y cargar la página principal con el estado inicial.
