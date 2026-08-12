# Diseño Frontend y Modal de Explicabilidad (templates & static) - Ana Cusi - 2026-08-12

## Prompt usado
"Diseña el sistema de estilos en `static/css/style.css` aplicando la guía visual del proyecto: modo oscuro con paleta custom (--fondo: #12151C, --superficie: #1B2029, --prioridad: #8B7CF6, --urgencia: #F5A524, --tiempo: #2DD4A7, --alerta: #F2555A), fuentes de sistema y monoespaciada para puntajes. Maqueta la barra de progreso en `index.html` y los componentes de color en `score_modal.html` para la explicabilidad del algoritmo."

## Qué generó la IA
Generó las variables CSS en `:root`, las reglas de maquetación flexbox/grid para las tarjetas de actividades (`.task-card`), la insignia de puntaje en monoespaciado (`font-family: monospace`), la barra de avance diario, y la ventana modal con indicadores visuales diferenciados por color para cada componente del puntaje.

## Qué corregí y por qué
Se corrigió la regla de especificidad CSS en las insignias de prioridad para asegurar que la opacidad del texto y el contraste en modo oscuro cumplan con los estándares de accesibilidad para daltonismo (WCAG), además de verificar que los atributos `name` e `id` requeridos por `main.js` no sufrieran alteraciones.

## Apareció en local o solo en producción?
Apareció en produccion (PythonAnywhere) al detectar que algunas fuentes externas cargadas vía CDN eran bloqueadas por no tener red saliente en la cuenta free, por lo que se ajustó a fuentes nativas del sistema (`system-ui`).
