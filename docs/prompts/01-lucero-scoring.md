# Motor de Puntuación (scoring.py) - Lucero Ayala - 2026-08-12

## Prompt usado
"Implementa las funciones calculate_score y rank_tasks en scoring.py según las reglas del proyecto: Total = P_Prioridad (1:50, 2:30, 3:10) + P_Urgencia (vencida u hoy:40, mañana:20, 2-3 días:10, +3 días:5) + P_Tiempo (+15 si entra en el disponible). Debe usar today_local() con America/Lima, devolver el breakdown exacto congelado y realizar un ordenamiento determinista por puntaje desc, due_date asc e id asc. Agrega 6 asserts de prueba al final."

## Qué generó la IA
Generó la estructura de `calculate_score` con los 3 componentes, la función `rank_tasks` utilizando la clave de ordenamiento `(-x["score"], x["due_date"], x.get("id", 0))`, y la suite de pruebas al final del archivo con 6 `assert` para validar los casos límite.

## Qué corregí y por qué
Se corrigió la salida del mensaje `print` al final del bloque `if __name__ == '__main__':` cambiando el caracter emoji `✅` por texto plano `SUCCESS: ...`. Esto fue necesario porque en entornos de terminal Windows con codificación por defecto CP1252, la impresión de caracteres UTF-8 no estándar generaba un error `UnicodeEncodeError`.

## Apareció en local o solo en producción?
Apareció durante la prueba de ejecución directa local en Windows (`python scoring.py`).
