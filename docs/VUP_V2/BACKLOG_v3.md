# 📦 Backlog v3 — lo que queda fuera de esta versión

**Regla del equipo:** cualquier idea que aparezca durante la semana y no esté en
los requisitos funcionales de `01_Inception.md` § 4 **entra aquí**, no en el
código. Anotarla cuesta un minuto; construirla a medias cuesta el release.

---

## 🔻 Diferido desde la v2 por decisión de alcance

Acordado por el equipo: **la v2 tiene exactamente dos roles, `usuario` y `admin`.**

| Elemento | Qué era | Por qué se difiere |
|---|---|---|
| **Rol `lider`** | Rol intermedio con `tarea.asignar` y `tarea.ver_equipo` | Recorta superficie sin tocar la arquitectura. **Volver a añadirlo es una entrada en `seed.py`**, no un refactor: eso es exactamente lo que compra tener los permisos en tablas en vez de en un `if` |
| **US10 — Asignar tareas a otro usuario** | Crear una tarea cuyo dueño es otra persona y seguir su columna | Depende del rol `lider`. Las columnas `assigned_by` y la vista `/equipo/tareas` quedan diseñadas y documentadas, sin construir |
| **TC-23 y TC-24** | Casos de prueba de la asignación | Salen del plan manual de la v2. El total pasa de 45 a **43 casos** |
| **Índice `tasks(assigned_by)`** | — | No se crea todavía: un índice sobre una columna que nadie consulta solo cuesta escrituras (ver `REVISION_BD_ESCALABILIDAD.md` H7) |

La columna `assigned_by` **sí se deja en el esquema** aunque nadie la use: añadir
una columna con datos en producción es una migración coordinada; dejarla puesta
hoy es gratis.

---

## Por qué existe este documento

El alcance de la v2 ya es grande para cuatro personas en una semana. El riesgo R7
de Inception dice exactamente esto: *un módulo a medias vale menos que uno
completo más pequeño*. Este archivo es donde las buenas ideas esperan sin
contaminar el sprint.

---

## 🔐 Identidad y seguridad

| Idea | Por qué no ahora |
|---|---|
| Recuperación de contraseña por correo | PythonAnywhere free tier no permite SMTP saliente. Hoy la restablece un administrador |
| Verificación de correo al registrarse | Misma razón |
| Autenticación en dos pasos | Requiere una app externa o SMS |
| Inicio de sesión con Google / Microsoft | OAuth está explícitamente fuera de alcance |
| Bitácora de auditoría completa | Hoy solo se sabe quién otorgó un rol (`granted_by`). Una tabla `audit_log` con cada acción sensible es v3 |
| Límite de intentos de login | Mitigación de fuerza bruta. Necesita almacenar intentos por IP |
| Caducidad de tokens de invitación | Hoy un token vale hasta que se revoca |
| Roles personalizados desde la interfaz | Hoy los tres roles se definen en `seed.py`. Crear roles nuevos desde `/admin` es v3 |

---

## 🗂️ Planner y tareas

| Idea | Por qué no ahora |
|---|---|
| Actividades recurrentes (RRULE) | Fuera de alcance. Los hábitos cubren la repetición diaria |
| Subtareas y listas de verificación | Complica el modelo de puntaje y el Kanban |
| Etiquetas libres además de la categoría | Categoría única basta para las métricas por sección |
| Adjuntar archivos a una tarea | Sin almacenamiento binario en esta versión |
| Comentarios en las tareas asignadas | Requiere notificaciones para tener sentido |
| Plantillas de día ("mi lunes tipo") | Buena idea, cero espacio en el sprint |
| Historial y deshacer | Necesita versionado de filas |
| Espacios de trabajo o equipos formales | Hoy la asignación es directa entre usuarios |

---

## 📅 Calendario

| Idea | Por qué no ahora |
|---|---|
| Sincronización con Google Calendar / Outlook | Fuera de alcance: red saliente restringida |
| Exportar a `.ics` | Viable técnicamente, sin espacio en el sprint |
| Vista de semana y vista de día | La v2 entrega la vista de mes; el día ya lo cubre `/planner` |
| Arrastrar eventos dentro del calendario | Interacción costosa de hacer bien y accesible |
| Detección de conflictos de horario | Requiere reglas de negocio que no están especificadas |
| Invitar por correo electrónico | Sin SMTP. El link copiable lo sustituye |
| Zonas horarias por usuario | Todo el sistema asume `America/Lima` |

---

## 🌱 Hábitos y métricas

| Idea | Por qué no ahora |
|---|---|
| Gráficos de tendencia semanal y mensual | La v2 entrega números; los gráficos son v3 |
| Metas de racha con recompensas | Gamificación completa, alcance propio |
| Recordatorios de hábitos | Sin notificaciones en esta versión |
| Exportar métricas a CSV o PDF | Feature del tier de pago del modelo de negocio |
| Métricas comparativas entre usuarios | Choca con la privacidad: las métricas del admin son agregadas por diseño |
| Correlación hábitos ↔ cumplimiento de tareas | Analítica interesante, requiere datos de varias semanas |

---

## 🎨 Interfaz

| Idea | Por qué no ahora |
|---|---|
| Modo oscuro | Los tokens ya están preparados para soportarlo; la verificación de contraste de una segunda paleta no cabe en la semana |
| Aplicación instalable (PWA) y uso sin conexión | Service worker y sincronización: alcance propio |
| Atajos de teclado | Mejora de productividad, no de funcionalidad |
| Animaciones de transición entre vistas | Riesgo de accesibilidad si no se respeta `prefers-reduced-motion` |
| Personalizar el color de la interfaz por usuario | Rompe la coherencia del design system |
| Internacionalización (español / inglés) | Duplicaría todos los textos de la interfaz |

---

## 🏗️ Infraestructura

| Idea | Por qué no ahora |
|---|---|
| Migrar a PostgreSQL | SQLite basta para la escala esperada. El límite ya está documentado (riesgo R8) |
| Sistema de migraciones (Alembic o propio) | Hoy: borrar y regenerar con `seed.py`. Con datos reales de producción haría falta |
| Copias de seguridad automáticas | Manual por ahora |
| Integración continua (GitHub Actions) | `python test_v2.py` a mano cumple para el curso |
| Caché de consultas | Sin problema de rendimiento medido. Optimizar sin medir es adivinar |
| API REST pública documentada | Hoy los endpoints JSON son internos del frontend |

---

## 📝 Cómo se añade algo aquí

Durante la semana, cuando alguien proponga una idea nueva:

1. **No se discute si es buena.** Casi todas lo son.
2. Se añade a la tabla del módulo que le corresponde, con una línea de "por qué no
   ahora".
3. Se sigue con lo que estaba en el sprint.

Si alguien cree que una idea **debe** entrar en la v2, se plantea en la reunión
diaria y se decide en grupo qué sale a cambio. El alcance no crece: se
intercambia.
