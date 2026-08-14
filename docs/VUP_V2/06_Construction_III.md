# 📋 VUP Phase 6: Construction Phase III Document

**Project Name:** VibePlanner — Multi-User Activity Planner with Transparent Prioritization
**Version:** 2.0 (Update — Multiusuario, Roles y Permisos)
**Phase:** Construction Phase III (Manual Test Plan & Verification)

---

## 🎯 Cómo se ejecuta este plan

**Entorno de pruebas:** base de datos recién creada + `python seed.py` + las
cuentas de prueba de la tabla siguiente. Se ejecuta **dos veces**: una en local y
otra sobre PythonAnywhere ya desplegado. Un caso que pasa en local y falla en
producción cuenta como fallado.

**Cuentas de prueba**

| Cuenta | Contraseña | Roles | Para qué sirve |
|---|---|---|---|
| `admin` | *(la del seed)* | `usuario` + `admin` | Demuestra los roles agregativos |
| `piero` | `Vibe2026!` | `usuario` | Usuario común |
| `ana` | `Vibe2026!` | `usuario` | Segunda cuenta: aislamiento e invitaciones |
| `lucero` | `Vibe2026!` | `usuario` + `lider` | Asignación de tareas |
| `jose` | `Vibe2026!` | `usuario` (se desactiva en TC-05) | Cuenta desactivada |

**Criterio de release:** los 45 casos ejecutados y los **3 críticos ⚠️
(TC-03, TC-08, TC-11) en verde**. Si alguno de esos tres falla, no se despliega —
son agujeros de seguridad, no defectos cosméticos.

**Leyenda:** ⬜ pendiente · ✅ pasa · ❌ falla · ⚠️ crítico bloqueante

---

## 🧱 BLOQUE A — Núcleo: cuentas, roles y permisos

### ⬜ TC-01: Registro público válido *(US5 · TC 5.1)*

- **Prerrequisitos:** base sembrada, sin cuenta `piero`, sesión cerrada.
- **Pasos:**
  1. Abrir `/register`.
  2. Usuario `piero`, correo `piero@esan.pe`, nombre `Piero Calderón`, contraseña `Vibe2026!`.
  3. Enviar.
- **Resultado esperado:** redirección al planner ya autenticado; en `sqlite3` la
  fila de `users` existe con `is_active = 1`, `user_roles` tiene **una** fila
  apuntando al rol `usuario`, y `password_hash` empieza por `scrypt:` o `pbkdf2:`
  y **no** contiene el texto `Vibe2026!`.
- **Criterio:** la cuenta funciona y la contraseña no es legible en la base.

### ⬜ TC-02: Duplicados rechazados *(US5 · TC 5.2)*

- **Prerrequisitos:** existe `piero` con correo `piero@esan.pe`.
- **Pasos:** intentar registrar (a) el mismo usuario con otro correo, (b) otro usuario con el mismo correo.
- **Resultado esperado:** ambos rechazados con "Ese usuario o correo ya está registrado"; `SELECT COUNT(*) FROM users` no cambia.
- **Criterio:** ninguna fila nueva y ningún error 500.

### ⚠️ ⬜ TC-03: Escalada de privilegios en el registro *(US5 · TC 5.3)* — **CRÍTICO**

- **Prerrequisitos:** sesión cerrada.
- **Pasos:**
  1. Desde una terminal:
     ```bash
     curl -X POST http://localhost:5000/register \
       -d "username=atacante&email=atacante@esan.pe&password=Hack2026!&role=admin&roles=admin&is_admin=1"
     ```
  2. Consultar los roles de la cuenta creada.
- **Resultado esperado:** la cuenta se crea con **exactamente un** rol: `usuario`.
  Ningún campo del formulario alteró los permisos.
- **Criterio:** `SELECT r.code FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE ur.user_id=<id>` devuelve una sola fila con `usuario`.
- **Si falla:** el release se detiene. Es el riesgo R2 de Inception materializado.

### ⬜ TC-04: Login incorrecto no filtra información *(US5 · TC 5.4)*

- **Pasos:** intentar entrar con (a) `piero` y contraseña errónea, (b) un usuario inexistente.
- **Resultado esperado:** el **mismo** mensaje en ambos casos — "Usuario o contraseña incorrectos" — y HTTP 401.
- **Criterio:** los dos mensajes son idénticos carácter por carácter. Si difieren, un atacante puede enumerar cuentas válidas.

### ⬜ TC-05: Cuenta desactivada *(US5 · TC 5.5 · US7 · TC 7.2)*

- **Prerrequisitos:** `jose` existe, activo, con 3 tareas y 1 evento.
- **Pasos:**
  1. Como `admin`, desactivar la cuenta `jose` desde `/admin/usuarios`.
  2. Cerrar sesión e intentar entrar como `jose` con su contraseña correcta.
  3. Consultar `SELECT COUNT(*) FROM tasks WHERE user_id = <id de jose>`.
- **Resultado esperado:** el acceso se rechaza con "Tu cuenta está desactivada";
  las 3 tareas y el evento **siguen existiendo**.
- **Criterio:** desactivar no es borrar.

### ⬜ TC-06: Permisos agregativos — la unión *(US6 · TC 6.1)*

- **Prerrequisitos:** la cuenta `admin` tiene los roles `usuario` y `admin`.
- **Pasos:**
  1. Entrar como `admin`.
  2. Abrir `/planner` y crear una actividad propia.
  3. **Sin cerrar sesión**, abrir `/admin/usuarios`.
- **Resultado esperado:** las dos pantallas funcionan en la misma sesión: el
  administrador planifica su día **y** administra el sistema.
- **Criterio:** ninguna de las dos rutas devuelve 403. Este caso es la
  demostración visible del requisito central de la v2.

### ⬜ TC-07: Permiso ausente bloquea la ruta *(US6 · TC 6.2)*

- **Prerrequisitos:** `piero` solo tiene el rol `usuario`.
- **Pasos:** con sesión de `piero`, escribir directamente `/admin/usuarios` y `/admin/metricas`.
- **Resultado esperado:** HTTP 403 en ambas, con la pantalla "No tienes permiso para esta sección". El menú lateral tampoco muestra esas entradas.
- **Criterio:** 403 real del servidor, no un simple ocultamiento del botón.

### ⚠️ ⬜ TC-08: Permiso ≠ propiedad *(US6 · TC 6.4)* — **CRÍTICO**

- **Prerrequisitos:** `jose` tiene la tarea `#42`; `ana` tiene `planner.editar` pero ninguna tarea con ese id.
- **Pasos:**
  1. Con sesión de `ana`, ejecutar:
     ```bash
     curl -X POST http://localhost:5000/tasks/42/edit -b cookies_ana.txt -d "title=Hackeada"
     curl -X POST http://localhost:5000/tasks/42/delete -b cookies_ana.txt
     curl http://localhost:5000/api/task/42/score-breakdown -b cookies_ana.txt
     ```
  2. Verificar la tarea `#42` en la base.
- **Resultado esperado:** las tres peticiones responden **404**; el título de la
  tarea sigue siendo el original y la tarea sigue existiendo.
- **Criterio:** 404, no 403. Un 403 confirmaría que ese id existe.
- **Si falla:** el release se detiene. Es el riesgo R3.

### ⬜ TC-09: Revocación inmediata de rol *(US6 · TC 6.3)*

- **Prerrequisitos:** `lucero` tiene `usuario` + `lider` y su sesión está abierta en otro navegador.
- **Pasos:**
  1. `lucero` abre `/equipo/tareas` correctamente.
  2. El `admin` le quita el rol `lider`.
  3. `lucero` **recarga** `/equipo/tareas` sin cerrar sesión.
- **Resultado esperado:** HTTP 403 inmediato.
- **Criterio:** los permisos se resuelven por petición; no viven cacheados en la cookie.

### ⬜ TC-10: Gestión de usuarios *(US7 · TC 7.1, TC 7.3)*

- **Pasos:**
  1. Como `admin`, crear la cuenta `lucero` marcando `usuario` y `lider`.
  2. Verificar que el listado muestra las dos etiquetas de rol.
  3. Entrar como `lucero` y abrir `/equipo/tareas`.
  4. Volver como `admin` e intentar **quitarse a sí mismo** el rol `admin` siendo el único administrador.
- **Resultado esperado:** (1–3) funcionan; (4) se rechaza con "No puedes dejar el sistema sin administradores" y el rol se conserva.
- **Criterio:** el sistema nunca queda sin administradores.

---

## 🗂️ BLOQUE B — Planner diario y Kanban

### ⚠️ ⬜ TC-11: Aislamiento de datos entre cuentas *(US1 · TC 1.3)* — **CRÍTICO**

- **Prerrequisitos:** `piero` tiene 3 tareas; `ana` tiene 2.
- **Pasos:**
  1. Entrar como `ana` y abrir `/planner`, `/kanban` y `/metricas`.
  2. Contar las tarjetas visibles en cada pantalla.
- **Resultado esperado:** exactamente **2** tareas en todas las pantallas; ninguna de `piero` en ninguna vista, ni en el conteo del progreso.
- **Criterio:** ninguna consulta devuelve filas de otra cuenta. Revisar además que
  cada `SELECT` de `repo_tasks.py` incluya `user_id` en el `WHERE`.
- **Si falla:** el release se detiene.

### ⬜ TC-12: Alta de actividad válida *(US1 · TC 1.1)*

- **Pasos:** crear "Math Assignment", categoría `Academic`, prioridad Alta, vence `2026-08-15`, 45 min, horario `10:00–10:45`, color `#567C8D`.
- **Resultado esperado:** aparece en la lista con `kanban_column = 'todo'`, `user_id` = la cuenta actual, y todos los campos correctos.
- **Criterio:** la tarjeta muestra título, categoría, insignia de prioridad, fecha, duración y su color en el borde.

### ⬜ TC-13: Validación de entrada *(US1 · TC 1.2)*

- **Pasos:** enviar el formulario con (a) título vacío, (b) `estimated_minutes = -10`, (c) `estimated_minutes = 999`, (d) `due_date = 15/08/2026` (formato incorrecto).
- **Resultado esperado:** los cuatro rechazados con mensaje en línea; ninguna fila creada.
- **Criterio:** la validación existe **en el servidor**, no solo el `required` del HTML. Verificar con `curl` saltándose el navegador.

### ⬜ TC-14: Ranking determinista y desempate *(US2 · TC 2.1)*

- **Prerrequisitos:** tres tareas — A (85 pts), B (90 pts), C (85 pts, creada después de A).
- **Pasos:** abrir `/planner` y anotar el orden. Recargar cinco veces.
- **Resultado esperado:** B → A → C, **idéntico** en las cinco recargas.
- **Criterio:** la misma entrada produce siempre la misma salida. El desempate es `due_date` ascendente y luego `id` ascendente.

### ⬜ TC-15: Modal de auditoría del puntaje *(US4 · TC 4.1)*

- **Prerrequisitos:** la tarea A está #1 con 90 pts (Prioridad 50, Urgencia 40, Tiempo 0).
- **Pasos:** clic en la insignia "90 pts"; leer el modal; cerrarlo con Escape.
- **Resultado esperado:** tres líneas — "+50 Prioridad Alta", "+40 Vence hoy", "+0 Supera tus minutos disponibles" — cuya suma es exactamente 90.
- **Criterio:** la suma del modal **coincide con la insignia**. Si difieren, el usuario deja de confiar en el ranking y se pierde el diferenciador del producto.

### ⬜ TC-16: Desglose de tarea ajena *(US4 · TC 4.2)*

- **Pasos:** como `ana`, pedir `GET /api/task/42/score-breakdown` (la tarea es de `jose`).
- **Resultado esperado:** HTTP 404 con cuerpo vacío o `{"error": "not found"}`; ningún dato de la tarea en la respuesta.
- **Criterio:** ni el título ni el puntaje se filtran.

### ⬜ TC-17: Revisión del día — solo hoy *(US8 · TC 8.1, 8.2)*

- **Prerrequisitos:** 3 actividades hoy, 2 mañana, 1 ayer.
- **Pasos:** abrir `/planner`.
- **Resultado esperado:** exactamente las 3 de hoy, ordenadas por hora de inicio; cada tarjeta muestra nombre, descripción, `HH:MM - HH:MM` y su color en el borde izquierdo.
- **Criterio:** ninguna actividad de otro día se cuela en la revisión diaria.

### ⬜ TC-18: Estado vacío útil *(US8 · TC 8.3)*

- **Prerrequisitos:** cuenta recién registrada, sin actividades.
- **Pasos:** abrir `/planner`, `/kanban`, `/calendario`, `/habitos` y `/metricas`.
- **Resultado esperado:** cada pantalla muestra un mensaje que invita a la acción y el botón de alta visible. Nunca una pantalla en blanco ni un error.
- **Criterio:** las cinco pantallas tienen estado vacío diseñado.

### ⬜ TC-19: Kanban — distribución y contadores *(US9 · TC 9.1)*

- **Prerrequisitos:** 8 tareas: 3 backlog, 2 todo, 2 ongoing, 1 done.
- **Pasos:** abrir `/kanban` y contar tarjetas y contadores por columna.
- **Resultado esperado:** `Backlog 3`, `Por hacer 2`, `En curso 2`, `Hecho 1`; total visible 8.
- **Criterio:** los contadores coinciden con las tarjetas realmente pintadas.

### ⬜ TC-20: Kanban — mover persiste *(US9 · TC 9.2)*

- **Pasos:** arrastrar "Informe IoT" de `todo` a `ongoing`; **recargar con F5**; comprobar en la base.
- **Resultado esperado:** sigue en `ongoing` tras la recarga y `kanban_column = 'ongoing'` en SQLite.
- **Criterio:** el cambio se guardó en el servidor, no solo en el DOM.

### ⬜ TC-21: Kanban — columna inválida *(US9 · TC 9.3)*

- **Pasos:** `curl -X POST /tasks/7/column -d "column=archivado"`.
- **Resultado esperado:** HTTP 400 y la tarea conserva su columna.
- **Criterio:** solo los cuatro valores permitidos llegan a la base. Verificar además que el `CHECK` del esquema los rechazaría igualmente.

### ⬜ TC-22: Progreso del día y backlog excluido *(US3 · TC 3.1, 3.2)*

- **Prerrequisitos:** 4 tareas de hoy (2 en `done`) más 3 en `backlog`.
- **Pasos:** leer el porcentaje; marcar una tercera como `done`; volver a leer.
- **Resultado esperado:** 50 % → 75 %. El denominador es **4**, no 7.
- **Criterio:** el backlog no entra en el cálculo del día.

### ⬜ TC-23: Asignación de tareas *(US10 · TC 10.1, 10.3)*

- **Prerrequisitos:** `lucero` tiene `usuario` + `lider`; `ana` está activa.
- **Pasos:**
  1. Como `lucero`, crear "Revisar maqueta" asignada a `ana`.
  2. Entrar como `ana` y abrir `/kanban`.
  3. Volver como `lucero` y abrir `/equipo/tareas`.
- **Resultado esperado:** la tarea aparece en el tablero de `ana` en `todo` con la etiqueta "Asignada por lucero"; `lucero` la ve en su vista de equipo con su columna actual.
- **Criterio:** `user_id` = id de `ana`, `assigned_by` = id de `lucero`.

### ⬜ TC-24: Asignación sin permiso *(US10 · TC 10.2)*

- **Pasos:** como `piero` (sin `tarea.asignar`), enviar el alta con `assigned_to=ana`.
- **Resultado esperado:** la tarea se crea **para `piero`**; el campo se ignora; el tablero de `ana` no cambia.
- **Criterio:** el dueño sale de la sesión salvo que exista el permiso de asignación.

---

## 📅 BLOQUE C — Calendario e invitaciones

### ⬜ TC-25: El evento cae en su día *(US11 · TC 11.1)*

- **Pasos:** en agosto de 2026, crear "Examen de IoT" el `2026-08-27` de `09:00` a `11:00`, color `#567C8D`. Recargar.
- **Resultado esperado:** aparece en la celda del 27 mostrando `09:00` y su color; sigue ahí tras recargar.
- **Criterio:** día correcto, hora correcta, color correcto, persistido.

### ⬜ TC-26: Navegación entre meses *(US11 · TC 11.2)*

- **Pasos:** desde agosto de 2026, avanzar a septiembre, octubre; retroceder a julio; y saltar a enero de 2027.
- **Resultado esperado:** la cabecera y la cuadrícula corresponden siempre al mes mostrado; los eventos de agosto no aparecen en los otros meses.
- **Criterio:** probar el cruce de año (diciembre → enero) y un mes de 28 días.

### ⬜ TC-27: Horario incoherente *(US11 · TC 11.3)*

- **Pasos:** crear un evento con inicio `15:00` y fin `14:00`; luego con fin igual al inicio.
- **Resultado esperado:** ambos rechazados con "La hora de fin debe ser posterior a la de inicio"; ninguna fila creada.
- **Criterio:** validado en el servidor. El `CHECK (end_at > start_at)` del esquema es la segunda barrera, no la primera.

### ⬜ TC-28: Calendario privado *(US11 · TC 11.4)*

- **Prerrequisitos:** `jose` tiene 5 eventos en septiembre.
- **Pasos:** como `ana`, abrir septiembre.
- **Resultado esperado:** 0 eventos.
- **Criterio:** solo se listan los propios y aquellos cuya invitación se aceptó.

### ⬜ TC-29: Invitación — generar y aceptar *(US12 · TC 12.1)*

- **Pasos:**
  1. Como `piero`, crear "Reunión VUP" el `2026-08-22` y generar el link.
  2. Copiar el link, abrirlo en otro navegador con sesión de `ana`, pulsar "Aceptar".
  3. Revisar el calendario de `ana` y el panel del evento en `piero`.
- **Resultado esperado:** el evento aparece en el calendario de `ana` con "Invitado por piero"; el panel de `piero` muestra "1 asistente confirmado".
- **Criterio:** fila en `event_invitations` con `status = accepted` e `invited_user_id` correcto.

### ⬜ TC-30: Token inválido no filtra nada *(US12 · TC 12.2)*

- **Pasos:** abrir `/invitacion/token-inventado-123`.
- **Resultado esperado:** "Esta invitación no es válida o fue cancelada".
- **Criterio:** la pantalla **no** revela el título, la fecha ni el anfitrión de ningún evento.

### ⬜ TC-31: La invitación exige sesión y devuelve al destino *(US12 · TC 12.3)*

- **Pasos:** en una ventana de incógnito, abrir un link de invitación válido; iniciar sesión como `ana` cuando lo pida.
- **Resultado esperado:** tras autenticarse, **vuelve sola** a la pantalla de aceptación del mismo evento, no al planner.
- **Criterio:** el destino se guardó antes de redirigir al login.

### ⬜ TC-32: Aceptar dos veces no duplica *(US12 · TC 12.4)*

- **Pasos:** como `ana`, abrir el mismo link ya aceptado y pulsar "Aceptar" otra vez.
- **Resultado esperado:** una sola fila en `event_invitations` para ella; el contador de asistentes sigue en 1.
- **Criterio:** la operación es idempotente; el índice único la respalda.

---

## 🌱 BLOQUE D — Hábitos y métricas

### ⬜ TC-33: Alta de hábito con meta *(US13 · TC 13.1)*

- **Pasos:** crear "Dormir 8 horas", tipo `sueño`, meta `8`, unidad `horas`.
- **Resultado esperado:** aparece en `/habitos` con la meta visible y el registro de hoy sin marcar.
- **Criterio:** los cuatro tipos (`dieta`, `ejercicio`, `relajacion`, `sueno`) se pueden crear.

### ⬜ TC-34: Registro diario idempotente *(US13 · TC 13.2)*

- **Pasos:** registrar `7` horas hoy; corregir a `8`; consultar `SELECT COUNT(*) FROM habit_logs WHERE habit_id=? AND log_date=?`.
- **Resultado esperado:** una sola fila, con valor `8`.
- **Criterio:** corregir no duplica. El `UNIQUE (habit_id, log_date)` lo garantiza.

### ⬜ TC-35: Racha correcta *(US13 · TC 13.3)*

- **Prerrequisitos:** "Ejercicio" cumplido los días 17, 18 y 19; hoy es 20.
- **Pasos:** leer la racha; marcar hoy; volver a leer.
- **Resultado esperado:** `3 días` → `4 días`.
- **Criterio:** la racha incluye hoy solo después de marcarlo.

### ⬜ TC-36: La racha se rompe con el hueco *(US13 · TC 13.4)*

- **Prerrequisitos:** cumplido el 17 y el 19, **no** el 18. Hoy es 19.
- **Pasos:** consultar la racha.
- **Resultado esperado:** `1 día`.
- **Criterio:** cuenta días consecutivos, no cumplimientos totales. Este es el error clásico que la IA genera.

### ⬜ TC-37: Métricas del día por sección *(US14 · TC 14.1)*

- **Prerrequisitos:** hoy completadas 3 de "Trabajo", 1 de "Personal", 2 de "Actividades"; 2 sin completar.
- **Pasos:** abrir `/metricas`.
- **Resultado esperado:** `Trabajo 3`, `Personal 1`, `Actividades 2`, total 6 de 8, `75 %`.
- **Criterio:** las secciones suman el total y el porcentaje corresponde.

### ⬜ TC-38: Día sin actividad — sin división entre cero *(US14 · TC 14.2)*

- **Prerrequisitos:** cuenta recién creada, sin tareas ni hábitos.
- **Pasos:** abrir `/metricas`.
- **Resultado esperado:** `0 %` con "Hoy no registraste actividad".
- **Criterio:** **ningún error 500**. Es el defecto más probable de todo el módulo.

### ⬜ TC-39: Los hábitos no distorsionan el porcentaje *(US14 · TC 14.3)*

- **Prerrequisitos:** 2 hábitos marcados de 3, y las tareas del TC-37.
- **Pasos:** abrir `/metricas`.
- **Resultado esperado:** la sección de hábitos muestra `2 / 3` y el porcentaje de tareas sigue siendo `75 %`.
- **Criterio:** son dos indicadores distintos y no se mezclan.

### ⬜ TC-40: Métricas del sistema *(US15 · TC 15.1)*

- **Prerrequisitos:** 12 cuentas (10 activas), 34 eventos, 7 usuarios con movimiento hoy.
- **Pasos:** como `admin`, abrir `/admin/metricas`; contrastar con consultas SQL directas.
- **Resultado esperado:** los cuatro números coinciden exactamente con el `SELECT COUNT(*)` correspondiente.
- **Criterio:** las métricas se calculan, no se estiman.

### ⬜ TC-41: Las métricas no exponen contenido privado *(US15 · TC 15.2)*

- **Pasos:** revisar cada tarjeta del panel y el HTML fuente de la página.
- **Resultado esperado:** solo números agregados. Ningún título de tarea, ningún nombre de evento, ningún dato de un usuario concreto — tampoco escondido en el HTML.
- **Criterio:** administrar el sistema no es leer la vida privada de las personas.

### ⬜ TC-42: Panel de métricas cerrado sin permiso *(US15 · TC 15.3)*

- **Pasos:** como `piero`, abrir `/admin/metricas`.
- **Resultado esperado:** HTTP 403.

---

## 📱 BLOQUE E — Interfaz responsive y accesibilidad

### ⬜ TC-43: Móvil a 360 px *(US16 · TC 16.1, 16.3)*

- **Prerrequisitos:** DevTools con viewport 360 × 640; tareas en las cuatro columnas.
- **Pasos:** recorrer `/planner`, `/kanban`, `/calendario`, `/habitos`, `/metricas`, `/admin/usuarios`, `/login`, `/register`.
- **Resultado esperado:** sin scroll horizontal en ninguna; la navegación aparece como barra inferior; el Kanban apila sus columnas verticalmente con su cabecera y contador; todo botón mide al menos 44 × 44 px.
- **Criterio:** las 8 pantallas se usan cómodamente con el pulgar.

### ⬜ TC-44: Tablet y escritorio *(US16 · TC 16.2)*

- **Pasos:** repetir el recorrido a 768 px y a 1280 px.
- **Resultado esperado:** a 768 px la barra lateral se muestra colapsada a iconos; a 1280 px está fija y etiquetada, el contenido no supera 1200 px de ancho y ninguna línea de texto pasa de ~75 caracteres.
- **Criterio:** no hay saltos rotos entre los tres tamaños.

### ⬜ TC-45: Contraste y color no exclusivo *(US16 · TC 16.4)*

- **Pasos:**
  1. Medir con DevTools el contraste del texto normal en tarjetas, insignias, barra lateral y estados vacíos.
  2. Aplicar el filtro de escala de grises del navegador y recorrer el planner y el Kanban.
- **Resultado esperado:** todo texto normal ≥ **4.5:1**; en escala de grises se sigue distinguiendo la prioridad, la urgencia y el estado, porque cada insignia lleva **también su texto**.
- **Criterio:** ninguna información depende solo del color. Aproximadamente 1 de cada 12 hombres tiene daltonismo rojo-verde, y las dos paletas del producto son azul y rosa.

---

## 📊 Resumen de ejecución

| Bloque | Casos | Pasan | Fallan | Pendientes |
|---|---|---|---|---|
| A — Núcleo | TC-01 … TC-10 | | | 10 |
| B — Planner y Kanban | TC-11 … TC-24 | | | 14 |
| C — Calendario | TC-25 … TC-32 | | | 8 |
| D — Hábitos y métricas | TC-33 … TC-42 | | | 10 |
| E — Responsive | TC-43 … TC-45 | | | 3 |
| **Total** | | | | **45** |

**Casos críticos bloqueantes:** TC-03 (escalada en el registro) · TC-08 (permiso ≠
propiedad) · TC-11 (aislamiento entre cuentas). Los tres son de seguridad y los
tres se ejecutan **también** contra el despliegue en PythonAnywhere antes de dar
el release por cerrado.

---

## 🐞 Registro de defectos encontrados

> Se llena durante la ejecución. La rúbrica pide el defecto más importante
> encontrado y reparado, con evidencia de que nada se rompió al arreglarlo.

| # | Caso | Defecto observado | Causa raíz | Corrección | Reejecutado |
|---|---|---|---|---|---|
| D-01 | | | | | ⬜ |
| D-02 | | | | | ⬜ |
| D-03 | | | | | ⬜ |

**Al reparar cualquier defecto** se vuelve a ejecutar el bloque completo al que
pertenece, no solo el caso que falló: la mitad de las regresiones aparecen en el
caso de al lado.
