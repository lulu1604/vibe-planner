# 📋 VUP Phase 2: Elaboration Phase I Document

**Project Name:** VibePlanner — Multi-User Activity Planner with Transparent Prioritization
**Version:** 2.0 (Update — Multiusuario, Roles y Permisos)
**Phase:** Elaboration Phase I (SMART User Stories & Acceptance Criteria)

> Cada historia de esta fase es **SMART**: específica, medible, alcanzable,
> relevante y acotada en el tiempo del sprint. Ninguna historia entra a
> Construction sin al menos un caso Given-When-Then con **valores exactos**.
> Si un criterio no se puede verificar con números concretos, no es un criterio:
> es un deseo.

**Índice de historias**

| Módulo | Historias |
|---|---|
| A — Núcleo (cuentas, roles, permisos) | US5, US6, US7 |
| B — Planner diario y Kanban | US1, US2, US3, US4, US8, US9, US10 |
| C — Calendario e invitaciones | US11, US12 |
| D — Hábitos y métricas | US13, US14, US15 |
| Transversal — Interfaz | US16 |

---

## 🧱 MÓDULO A — Núcleo: cuentas, roles y permisos

### 🔹 US5 — Registro e inicio de sesión

**As a** visitor, **I want to** create an account with a unique username, a unique
email and a password of at least 8 characters, and then log in with those
credentials, **so that** my planner is private, persistent and tied only to me.

#### Acceptance Test Cases (Given-When-Then)

- **TC 5.1 — Registro válido**
  - **Given** no existe ninguna cuenta con el usuario `piero` ni el correo `piero@esan.pe`,
  - **When** envío el formulario de `/register` con usuario `piero`, correo `piero@esan.pe` y contraseña `Vibe2026!`,
  - **Then** se crea una fila en `users` con `is_active = 1`, se crea **exactamente una** fila en `user_roles` apuntando al rol `usuario`, la columna `password_hash` **no** contiene el texto `Vibe2026!`, y se me redirige al planner ya autenticado.

- **TC 5.2 — Duplicados rechazados**
  - **Given** ya existe la cuenta `piero` con correo `piero@esan.pe`,
  - **When** intento registrarme otra vez con el mismo usuario **o** el mismo correo,
  - **Then** no se crea ninguna fila nueva en `users`, permanezco en el formulario y veo el mensaje "Ese usuario o correo ya está registrado".

- **TC 5.3 — Escalada de privilegios bloqueada** ⚠️ *crítico*
  - **Given** estoy en el formulario de registro,
  - **When** envío el formulario manipulado añadiendo el campo `role=admin` (por ejemplo desde DevTools o con `curl`),
  - **Then** la cuenta se crea igualmente **solo** con el rol `usuario`, el campo enviado se ignora por completo, y al consultar `user_roles` para esa cuenta hay una única fila cuyo `role_id` corresponde a `usuario`.

- **TC 5.4 — Login fallido**
  - **Given** existe la cuenta `piero` con contraseña `Vibe2026!`,
  - **When** intento iniciar sesión con la contraseña `Vibe2025!`,
  - **Then** no se crea sesión, vuelvo al login y el mensaje es genérico — "Usuario o contraseña incorrectos" — sin revelar cuál de los dos falló.

- **TC 5.5 — Cuenta desactivada**
  - **Given** la cuenta `ana` tiene `is_active = 0`,
  - **When** intenta iniciar sesión con su contraseña correcta,
  - **Then** el acceso se rechaza con el mensaje "Tu cuenta está desactivada. Contacta al administrador" y no se crea sesión.

---

### 🔹 US6 — Permisos agregativos

**As the** system, **I want** each user's effective permission set to be the exact
union of the permissions of every role assigned to them, resolved on each request
from the `roles`–`role_permissions`–`permissions` tables, **so that** one account
can be simultaneously an ordinary user and an administrator without duplicating
data or hard-coding role names in the controllers.

#### Acceptance Test Cases (Given-When-Then)

- **TC 6.1 — Unión de permisos**
  - **Given** el rol `usuario` tiene los permisos `{planner.ver, planner.crear, evento.crear, habito.registrar, metrica.propia.ver}` y el rol `admin` tiene `{usuario.listar, usuario.crear, rol.asignar, metrica.sistema.ver}`, y la cuenta `piero` tiene **ambos** roles asignados,
  - **When** el sistema resuelve sus permisos efectivos al entrar,
  - **Then** obtiene los **9** permisos, la unión no contiene duplicados, y `piero` puede abrir tanto `/planner` como `/admin/usuarios` en la misma sesión sin cambiar de cuenta.

- **TC 6.2 — Permiso ausente bloquea la ruta**
  - **Given** la cuenta `ana` solo tiene el rol `usuario`, que **no** incluye `usuario.listar`,
  - **When** escribe directamente `/admin/usuarios` en la barra de direcciones,
  - **Then** recibe **HTTP 403**, ve la pantalla "No tienes permiso para esta sección", y **no** se ejecuta ninguna consulta a la tabla `users`.

- **TC 6.3 — Revocación inmediata**
  - **Given** `ana` tiene los roles `usuario` y `lider`, y con `lider` puede abrir `/equipo/tareas`,
  - **When** un administrador le quita el rol `lider` y `ana` recarga `/equipo/tareas` **en su sesión ya abierta**,
  - **Then** recibe HTTP 403 sin necesidad de cerrar sesión, porque los permisos se resuelven por petición y nunca se cachean en la cookie.

- **TC 6.4 — Propiedad además de permiso** ⚠️ *crítico*
  - **Given** `ana` y `jose` tienen ambos el permiso `planner.editar`, y la tarea `#42` pertenece a `jose`,
  - **When** `ana` envía `POST /tasks/42/edit` con datos válidos,
  - **Then** recibe HTTP 404, la tarea `#42` conserva sus valores originales, y queda claro que **tener el permiso no implica ser el dueño del registro**.

---

### 🔹 US7 — Gestión de usuarios

**As an** administrator holding `usuario.listar`, `usuario.crear`, `usuario.editar`,
`usuario.desactivar` and `rol.asignar`, **I want to** list every account with its
roles, create accounts with any role combination, edit their data, reset their
password and deactivate them, **so that** I control who enters the platform and
what each person can do, without any of it depending on public registration.

#### Acceptance Test Cases (Given-When-Then)

- **TC 7.1 — Alta administrativa con roles**
  - **Given** estoy autenticado como el administrador semilla y hay 3 cuentas en el sistema,
  - **When** creo la cuenta `lucero` marcando los roles `usuario` y `lider`,
  - **Then** el listado muestra 4 cuentas, la fila de `lucero` muestra las dos etiquetas de rol, y al iniciar sesión `lucero` accede a `/equipo/tareas` sin recibir 403.

- **TC 7.2 — Desactivación conserva los datos**
  - **Given** la cuenta `lucero` tiene 5 tareas y 2 eventos,
  - **When** el administrador la desactiva,
  - **Then** `is_active` pasa a `0`, sus 5 tareas y 2 eventos **siguen existiendo** en la base de datos, y `lucero` ya no puede iniciar sesión (TC 5.5). Desactivar **no** es borrar.

- **TC 7.3 — El administrador no se puede autodestruir**
  - **Given** soy el único usuario con el rol `admin` en el sistema,
  - **When** intento quitarme a mí mismo el rol `admin` o desactivar mi propia cuenta,
  - **Then** la operación se rechaza con "No puedes dejar el sistema sin administradores", y mi cuenta conserva el rol.

---

## 🗂️ MÓDULO B — Planner diario y Kanban

### 🔹 US1 — Ciclo de vida de la actividad *(heredada de v1, ahora por cuenta)*

**As a** user, **I want to** create, edit and delete my activities with a valid
title, ISO deadline, category, priority level (1-Alta, 2-Media, 3-Baja) and
estimated duration (1–480 min), **so that** I keep an accurate list of everything
I have pending — and only I can see it.

#### Acceptance Test Cases (Given-When-Then)

- **TC 1.1 — Alta válida** *(v1, vigente)*
  - **Given** estoy autenticado como `piero` y mi lista está vacía,
  - **When** creo la tarea "Math Assignment", `due_date` `2026-08-15`, prioridad 1, categoría "Academic", 45 minutos,
  - **Then** se guarda en SQLite con `user_id` = mi id, `status` = `todo`, y aparece en mi lista activa.

- **TC 1.2 — Entrada inválida rechazada** *(v1, vigente)*
  - **Given** estoy en el formulario de nueva actividad,
  - **When** envío el título vacío **o** `estimated_minutes = -10`,
  - **Then** no se crea ningún registro y se muestra el error en línea.

- **TC 1.3 — Aislamiento entre cuentas** `[v2]` ⚠️ *crítico*
  - **Given** `piero` tiene 3 tareas y `ana` tiene 2 tareas,
  - **When** `ana` abre su planner,
  - **Then** ve exactamente **2** tarjetas, ninguna de `piero`, y la consulta ejecutada incluye `WHERE user_id = ?` con su propio id.

---

### 🔹 US2 — Ranking determinista *(heredada de v1, fórmula congelada)*

**As a** user, **I want** the system to compute a deterministic total score for
each of my active tasks from deadline urgency, priority level and available-time
fit, **so that** my day is ordered from highest to lowest without manual sorting.

> 🔒 **La fórmula NO cambia en v2.** Prioridad 50/30/10 · Urgencia 40/20/10/5 ·
> Ajuste de tiempo +15/0. Lo único que cambia es que el conjunto de tareas de
> entrada ya viene filtrado por `user_id`.

- **TC 2.1 — Orden y desempate** *(v1, vigente)*
  - **Given** tengo 3 tareas pendientes: A (85 pts), B (90 pts) y C (85 pts, creada después de A),
  - **When** se renderiza el plan del día,
  - **Then** el orden es B → A → C, desempatando por `due_date` ascendente y luego por `id` ascendente.

- **TC 2.2 — El ranking no cruza cuentas** `[v2]`
  - **Given** `ana` tiene una tarea de 95 pts y `piero` una de 90 pts,
  - **When** `piero` abre su planner,
  - **Then** su tarea de 90 pts aparece en el puesto #1 de **su** lista; la tarea de 95 pts de `ana` no aparece en ninguna posición.

---

### 🔹 US3 — Estado y progreso *(heredada de v1)*

**As a** user, **I want to** move each task between `backlog`, `todo`, `ongoing`
and `done`, **so that** my daily completion percentage recalculates in real time.

- **TC 3.1 — Progreso dinámico** *(v1, adaptada a 4 columnas)*
  - **Given** tengo 4 tareas para hoy con 2 en `done` (50 %),
  - **When** marco una tercera como `done`,
  - **Then** el estado se actualiza en SQLite y la barra de progreso pasa a 75 %.

- **TC 3.2 — Backlog fuera del cálculo** `[v2]`
  - **Given** tengo 4 tareas en `todo`/`ongoing`/`done` y 3 más en `backlog`,
  - **When** se calcula el progreso del día,
  - **Then** el denominador es **4**, no 7: el backlog es intención, no compromiso del día.

---

### 🔹 US4 — Modal de auditoría del puntaje *(heredada de v1)*

**As a** user, **I want to** click a task's score badge and read the exact
itemised breakdown (Prioridad + Urgencia + Ajuste de tiempo), **so that** I can
verify why it holds its position.

- **TC 4.1 — Desglose auditable** *(v1, vigente)*
  - **Given** la tarea A está #1 con 90 puntos (Prioridad 50, Urgencia 40, Tiempo 0),
  - **When** hago clic en la insignia "90 pts",
  - **Then** el modal muestra "+50 Prioridad Alta", "+40 Vence hoy", "+0 Supera tus minutos disponibles", y **la suma mostrada coincide exactamente con la insignia**.

- **TC 4.2 — El desglose ajeno no se sirve** `[v2]`
  - **Given** la tarea `#42` pertenece a `jose`,
  - **When** `ana` solicita `GET /api/task/42/score-breakdown`,
  - **Then** la respuesta es HTTP 404 y no incluye ningún dato de la tarea.

---

### 🔹 US8 — Revisión del día `[v2]`

**As a** user, **I want** one screen showing only today: my scheduled activities
with their times, my ranked task list and my completion percentage, **so that** I
do not have to open the full calendar to know what my day looks like.

- **TC 8.1 — Solo hoy**
  - **Given** hoy es `2026-08-20`, y tengo 3 actividades hoy, 2 mañana y 1 ayer,
  - **When** abro `/planner`,
  - **Then** veo exactamente las **3** de hoy, ordenadas por hora de inicio ascendente, y las otras 3 no aparecen.

- **TC 8.2 — Cada actividad con sus campos**
  - **Given** creé la actividad "Pasear al perro" con descripción "Parque Kennedy", horario `18:00–19:00` y color `#D7707F`,
  - **When** abro la revisión del día,
  - **Then** la tarjeta muestra nombre, descripción, `18:00 - 19:00`, y su borde izquierdo usa exactamente `#D7707F`.

- **TC 8.3 — Estado vacío útil**
  - **Given** no tengo nada planificado hoy,
  - **When** abro `/planner`,
  - **Then** veo "Hoy no tienes nada planeado. Agrega tu primera actividad y verás tu día ordenado", con el botón de alta visible — nunca una pantalla en blanco.

---

### 🔹 US9 — Tablero Kanban `[v2]`

**As a** user, **I want to** see my tasks in four columns — Backlog, To do,
Ongoing, Done — and move a card between them, **so that** I can read the state of
my work at a glance.

- **TC 9.1 — Distribución en columnas**
  - **Given** tengo 8 tareas: 3 en `backlog`, 2 en `todo`, 2 en `ongoing`, 1 en `done`,
  - **When** abro `/kanban`,
  - **Then** cada columna muestra su contador correcto (3 / 2 / 2 / 1) y la suma de las tarjetas visibles es 8.

- **TC 9.2 — Mover persiste**
  - **Given** la tarea "Informe IoT" está en `todo`,
  - **When** la muevo a `ongoing` y **recargo la página**,
  - **Then** sigue en `ongoing`, porque el cambio se guardó en SQLite y no solo en el DOM.

- **TC 9.3 — Columna inválida rechazada**
  - **Given** estoy autenticado,
  - **When** envío `POST /tasks/7/column` con `column=archivado`,
  - **Then** la respuesta es HTTP 400, la tarea conserva su columna y ningún valor fuera de las cuatro permitidas llega a la base de datos.

---

### 🔹 US10 — Tareas asignadas al equipo `[v2]`

**As a** user holding `tarea.asignar`, **I want to** create a task whose owner is
another user and follow which column it sits in, **so that** I can coordinate a
small team from the same planner.

- **TC 10.1 — Asignación válida**
  - **Given** `lucero` tiene el permiso `tarea.asignar` y `ana` es una cuenta activa,
  - **When** `lucero` crea la tarea "Revisar maqueta" asignada a `ana`,
  - **Then** la tarea se guarda con `user_id` = id de `ana` y `assigned_by` = id de `lucero`, aparece en el Kanban de `ana` en la columna `todo`, y `ana` ve la etiqueta "Asignada por lucero".

- **TC 10.2 — Sin permiso no se asigna**
  - **Given** `jose` **no** tiene `tarea.asignar`,
  - **When** envía el formulario de alta incluyendo `assigned_to=ana`,
  - **Then** el campo se ignora y la tarea se crea para **él mismo**; nunca aparece en el tablero de `ana`.

- **TC 10.3 — Vista de equipo**
  - **Given** `lucero` asignó 4 tareas repartidas en distintas columnas,
  - **When** abre `/equipo/tareas`,
  - **Then** ve las 4 agrupadas por persona con su columna actual, y el contador "2 pendientes de 4".

---

## 📅 MÓDULO C — Calendario e invitaciones

### 🔹 US11 — Gestión de horario mensual `[v2]`

**As a** user, **I want to** create events with name, description, start and end
datetime and a colour, and see them laid out on a monthly grid I can move
forward and backward through, **so that** I can plan the current month and the
ones ahead.

- **TC 11.1 — El evento cae en su día**
  - **Given** estoy viendo agosto de 2026,
  - **When** creo el evento "Examen de IoT" para el `2026-08-27` de `09:00` a `11:00` con color `#567C8D`,
  - **Then** aparece en la celda del 27, muestra `09:00` y su color, y sigue ahí al recargar.

- **TC 11.2 — Navegación entre meses**
  - **Given** estoy en agosto de 2026 con 3 eventos,
  - **When** avanzo dos meses hasta octubre de 2026,
  - **Then** la cabecera dice "Octubre 2026", la cuadrícula corresponde a ese mes y los 3 eventos de agosto no se muestran.

- **TC 11.3 — Horario incoherente rechazado**
  - **Given** estoy creando un evento,
  - **When** pongo hora de inicio `15:00` y hora de fin `14:00`,
  - **Then** no se guarda nada y aparece "La hora de fin debe ser posterior a la de inicio".

- **TC 11.4 — Calendario privado**
  - **Given** `jose` tiene 5 eventos en septiembre,
  - **When** `ana` abre septiembre en su calendario,
  - **Then** ve **0** eventos: solo se listan los propios y aquellos cuya invitación aceptó.

---

### 🔹 US12 — Invitación por link `[v2]`

**As a** host, **I want to** generate a unique link for one of my events and share
it, **so that** another registered user can accept it and see the event in their
own calendar, with no email service involved.

- **TC 12.1 — Generar y aceptar**
  - **Given** `piero` creó el evento "Reunión VUP" el `2026-08-22`,
  - **When** genera el link de invitación y `ana` — con sesión iniciada — lo abre y pulsa "Aceptar",
  - **Then** se crea una fila en `event_invitations` con `status = accepted` e `invited_user_id` = id de `ana`, el evento aparece en el calendario de `ana` marcado como "Invitado por piero", y el panel del evento muestra "1 asistente confirmado".

- **TC 12.2 — Token inválido**
  - **Given** un token que nunca existió o que fue revocado,
  - **When** alguien abre ese link,
  - **Then** ve "Esta invitación no es válida o fue cancelada" y **no** se revela el título, la fecha ni el anfitrión del evento.

- **TC 12.3 — Invitación exige sesión**
  - **Given** un visitante sin sesión abre un link de invitación válido,
  - **When** carga la página,
  - **Then** se le pide iniciar sesión o registrarse y, tras autenticarse, **regresa automáticamente** a la pantalla de aceptación del mismo evento.

- **TC 12.4 — Aceptar dos veces no duplica**
  - **Given** `ana` ya aceptó la invitación,
  - **When** vuelve a abrir el mismo link y pulsa "Aceptar",
  - **Then** sigue existiendo **una sola** fila en `event_invitations` para ella y el contador de asistentes sigue en 1.

---

## 🌱 MÓDULO D — Hábitos y métricas

### 🔹 US13 — Gestión de hábitos `[v2]`

**As a** user, **I want to** define habits of type diet, exercise, relaxation or
sleep — with a daily target and unit — and tick them off each day, **so that** I
sustain routines instead of only isolated tasks.

- **TC 13.1 — Alta de hábito con meta**
  - **Given** no tengo hábitos definidos,
  - **When** creo "Dormir 8 horas" de tipo `sueño` con meta `8` y unidad `horas`,
  - **Then** aparece en `/habitos` con su meta visible y con el registro de hoy sin marcar.

- **TC 13.2 — Registro diario idempotente**
  - **Given** el hábito "Dormir 8 horas" existe y hoy es `2026-08-20`,
  - **When** registro `7` horas y luego corrijo a `8`,
  - **Then** existe **una sola** fila en `habit_logs` para ese hábito y esa fecha, con valor `8`. Corregir no duplica.

- **TC 13.3 — Racha correcta**
  - **Given** cumplí "Ejercicio" los días 17, 18 y 19 de agosto y hoy es el 20,
  - **When** abro el módulo de hábitos,
  - **Then** la racha muestra `3 días` antes de marcar hoy, y `4 días` inmediatamente después de marcarlo.

- **TC 13.4 — La racha se rompe con el hueco**
  - **Given** cumplí el 17 y el 19, pero **no** el 18,
  - **When** consulto la racha el día 19,
  - **Then** muestra `1 día`, no `2`: la racha cuenta días consecutivos, no cumplimientos totales.

---

### 🔹 US14 — Métricas del día `[v2]`

**As a** user, **I want to** see at the end of the day what I did and achieved,
broken down into Trabajo, Personal and Actividades, **so that** I close my day
with an honest picture of it.

- **TC 14.1 — Agrupación por sección**
  - **Given** hoy completé 3 tareas de categoría "Trabajo", 1 de "Personal" y 2 de "Actividades", y dejé 2 sin completar,
  - **When** abro `/metricas`,
  - **Then** veo `Trabajo 3`, `Personal 1`, `Actividades 2`, un total de 6 completadas de 8, y `75 %` de cumplimiento.

- **TC 14.2 — Día sin actividad**
  - **Given** hoy no registré ninguna tarea ni hábito,
  - **When** abro `/metricas`,
  - **Then** veo `0 %` con el mensaje "Hoy no registraste actividad" — **sin división entre cero ni error 500**.

- **TC 14.3 — Los hábitos suman a su sección**
  - **Given** hoy marqué 2 hábitos de 3 definidos,
  - **When** abro `/metricas`,
  - **Then** la sección de hábitos muestra `2 / 3` y ese conteo **no** altera el porcentaje de tareas, que se calcula por separado.

---

### 🔹 US15 — Métricas del sistema `[v2]`

**As an** administrator holding `metrica.sistema.ver`, **I want to** see how many
accounts exist, how many are active, how many events were created and how many
users used their daily list, **so that** I can tell whether the platform is
actually being used.

- **TC 15.1 — Conteos exactos**
  - **Given** el sistema tiene 12 cuentas (10 activas, 2 desactivadas), 34 eventos y 7 usuarios que movieron al menos una tarea hoy,
  - **When** el administrador abre `/admin/metricas`,
  - **Then** lee exactamente `12 usuarios`, `10 activos`, `34 eventos`, `7 usaron su lista hoy`.

- **TC 15.2 — Métricas agregadas, nunca contenido**
  - **Given** el administrador consulta el panel,
  - **When** revisa cualquier tarjeta de métrica,
  - **Then** solo ve **números agregados**: en ninguna parte aparecen los títulos de las tareas ni los eventos de un usuario concreto. Administrar el sistema no es leer la vida privada de las personas.

- **TC 15.3 — Panel cerrado sin el permiso**
  - **Given** `piero` solo tiene el rol `usuario`,
  - **When** abre `/admin/metricas`,
  - **Then** recibe HTTP 403 (mismo criterio que TC 6.2).

---

## 📱 MÓDULO TRANSVERSAL — Interfaz

### 🔹 US16 — Interfaz responsive `[v2]`

**As a** user on a 360 px phone, a 768 px tablet or a 1280 px laptop, **I want**
every screen to adapt to my viewport, **so that** I can consult and update my plan
from any device.

- **TC 16.1 — Móvil a 360 px**
  - **Given** abro la aplicación en un viewport de 360 × 640,
  - **When** recorro planner, kanban, calendario, hábitos y métricas,
  - **Then** **no hay scroll horizontal** en ninguna, la navegación se ve como barra inferior, y todo objetivo táctil mide al menos 44 × 44 px.

- **TC 16.2 — Escritorio a 1280 px**
  - **Given** abro la aplicación en 1280 × 800,
  - **When** entro al planner,
  - **Then** la barra lateral está fija y visible, el contenido no supera los 1200 px de ancho, y no aparecen líneas de texto de más de ~75 caracteres.

- **TC 16.3 — El Kanban en móvil**
  - **Given** estoy en 360 px con tareas en las cuatro columnas,
  - **When** abro `/kanban`,
  - **Then** las columnas se apilan verticalmente con su cabecera y contador — **no** se comprimen cuatro columnas ilegibles en la pantalla.

- **TC 16.4 — Contraste accesible**
  - **Given** cualquier pantalla de la aplicación,
  - **When** se mide el contraste del texto normal contra su fondo,
  - **Then** es de al menos **4.5:1** (WCAG AA), y ninguna información se comunica **solo** por color: toda insignia lleva también su texto.

---

## 📊 Trazabilidad Historia → Test → Riesgo

| Historia | Casos de prueba | Riesgo que mitiga |
|---|---|---|
| US5 Registro/Login | TC 5.1 – 5.5 | R2 (autenticación) |
| US6 Permisos agregativos | TC 6.1 – 6.4 | R2, R3 (escalada horizontal) |
| US7 Gestión de usuarios | TC 7.1 – 7.3 | R2 |
| US1 CRUD | TC 1.1 – 1.3 | R3, R4 (migración) |
| US2 Ranking | TC 2.1 – 2.2 | R6 (código IA) |
| US3 Estado/progreso | TC 3.1 – 3.2 | R4 |
| US4 Modal de puntaje | TC 4.1 – 4.2 | R3 |
| US8 Revisión del día | TC 8.1 – 8.3 | R5 (requisitos) |
| US9 Kanban | TC 9.1 – 9.3 | R6 |
| US10 Asignación | TC 10.1 – 10.3 | R3 |
| US11 Calendario | TC 11.1 – 11.4 | R3, R5 |
| US12 Invitaciones | TC 12.1 – 12.4 | R3 |
| US13 Hábitos | TC 13.1 – 13.4 | R5 |
| US14 Métricas propias | TC 14.1 – 14.3 | R5 |
| US15 Métricas del sistema | TC 15.1 – 15.3 | R2, R3 |
| US16 Responsive | TC 16.1 – 16.4 | R7 (alcance) |

**Total: 16 historias · 45 casos de prueba Given-When-Then.**
Los marcados ⚠️ *crítico* (TC 5.3, TC 6.4, TC 1.3) son bloqueantes del release:
si alguno falla, no se despliega.
