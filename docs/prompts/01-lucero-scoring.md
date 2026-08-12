# Motor de Puntuación (scoring.py) - Lucero Ayala - 2026-08-12

## Prompt usado
Prompt 1: "ahora nos encontramos en la rama scoring, dame una lista de lo que haras para scoring y de lo que piden"
Prompt 2: "si"

## Qué generó la IA
La IA presentó el desglose de reglas congeladas del proyecto y luego implementó la función `calculate_score` con los 3 componentes (Prioridad, Urgencia con zona horaria America/Lima y Ajuste de Tiempo), el ordenamiento determinista en `rank_tasks`, y los 6 `assert` de pruebas automatizadas al final del archivo.

## Qué corregí y por qué
Se corrigió la salida del mensaje `print` al final del archivo cambiando el caracter emoji `✅` por texto plano `SUCCESS: ...`. La IA había generado inicialmente `print("✅ ¡Todas las 6 pruebas de assert pasaron exitosamente!")`, lo cual provocaba un fallo `UnicodeEncodeError` en Windows debido a la codificación CP1252 por defecto en la terminal de comandos.

## Apareció en local o solo en producción?
Apareció en local durante la ejecución directa del archivo en la consola de Windows (`python scoring.py`).
