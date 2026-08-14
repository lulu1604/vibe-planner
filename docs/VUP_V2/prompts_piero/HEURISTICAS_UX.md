# 🎯 Las 10 heurísticas de Nielsen aplicadas a VibePlanner

**Para qué sirve este documento:** las heurísticas en abstracto no ayudan a nadie.
Aquí cada una está traducida a decisiones concretas de **este** producto, con lo
que hay que hacer y lo que no. Úsalo mientras maquetas (P3, P4, P5) y como
checklist de auditoría al final (P6).

---

## 1. Visibilidad del estado del sistema

*El usuario siempre debe saber qué está pasando.*

| Hacer | No hacer |
|---|---|
| Marcar en el menú la sección activa con fondo `--sky` y `aria-current="page"` | Un menú donde no se distingue dónde estás |
| Mostrar el usuario y sus roles en la barra superior: `piero · Usuario · Admin` | Que el usuario tenga que adivinar con qué cuenta entró |
| Deshabilitar el botón y cambiar el texto a "Guardando…" al enviar un formulario | Dejar el botón activo y permitir doble envío |
| Mensaje de confirmación tras crear, editar o desactivar una cuenta | Redirigir en silencio y que el admin no sepa si funcionó |
| Barra de progreso del día con su número: `3 de 8 · 37 %` | Solo la barra, sin el número |

**En el panel de admin:** después de asignar roles, el mensaje dice **qué** quedó:
"Roles de `ana` actualizados: Usuario, Administrador". No un "Guardado" genérico.

---

## 2. Correspondencia entre el sistema y el mundo real

*Habla el idioma del usuario, no el de la base de datos.*

| Base de datos | Pantalla |
|---|---|
| `usuario` / `admin` | "Usuario" / "Administrador" |
| `is_active = 0` | "Cuenta desactivada" |
| `kanban_column = 'ongoing'` | "En curso" |
| `2026-08-27` | "Vence el 27 de agosto" · "Vence hoy" · "Vence mañana" |
| `priority_level = 1` | "Prioridad alta" |
| `403 Forbidden` | "No tienes permiso para esta sección" |

**Nunca en pantalla:** `user_id`, `kanban_column`, `permission.code`, `NULL`,
`IntegrityError`. El formato ISO es para la base de datos; las personas leen
fechas en su idioma.

---

## 3. Control y libertad del usuario

*Toda acción necesita una salida clara.*

- **Cancelar visible** en todo formulario, al lado de guardar — no solo el
  botón "atrás" del navegador.
- **Confirmación en lo destructivo**, y que la confirmación diga qué pasa:
  "¿Desactivar la cuenta de `ana`? Podrá reactivarse después y **no se borrará
  ninguno de sus datos**."
- **Desactivar en vez de borrar.** Es la salida de emergencia del administrador:
  todo error es reversible.
- **Modal cerrable de tres formas:** botón ×, tecla `Escape` y clic fuera.
- **Volver al destino tras el login.** Si alguien abrió un link de invitación sin
  sesión, después de entrar regresa ahí, no al inicio.

---

## 4. Consistencia y estándares

*Lo mismo se ve igual y se llama igual en todas partes.*

- **Un solo botón primario por pantalla.** Si hay dos igual de llamativos, no hay
  ninguno.
- **Los mismos verbos siempre:** "Guardar", "Cancelar", "Agregar", "Desactivar".
  Nunca mezclar "Enviar" / "Aceptar" / "OK" para la misma acción.
- **Ningún hex suelto.** Todo color sale de `tokens.css`. Es lo que hace que ocho
  pantallas hechas por cuatro personas parezcan una sola aplicación.
- **Formularios siempre igual:** etiqueta encima, campo, ayuda debajo, error
  debajo del todo.
- **Convenciones del navegador:** el logo lleva al inicio, los enlaces se ven como
  enlaces, `Enter` envía el formulario.

---

## 5. Prevención de errores

*Mejor que no pueda equivocarse a explicarle el error.*

| Riesgo | Prevención |
|---|---|
| Contraseña demasiado corta | Requisito visible **antes** de escribir: "Mínimo 8 caracteres" |
| Usuario o correo duplicado | Validación al salir del campo, no al enviar todo |
| Fecha inválida | `<input type="date">`, no texto libre |
| Duración fuera de rango | `<input type="number" min="1" max="480">` |
| Quedarse sin administradores | El sistema lo **impide** y explica por qué |
| Doble envío del formulario | Botón deshabilitado al enviar |
| Desactivar la cuenta equivocada | La confirmación repite el nombre de usuario |

**La validación de cliente no sustituye a la de servidor.** Los `min`, `max` y
`required` del HTML son prevención; la validación real vive en Flask y se prueba
con `curl` saltándose el navegador.

---

## 6. Reconocer antes que recordar

*Que la información esté a la vista, no en la memoria del usuario.*

- **El menú muestra todos los módulos**, no un buscador donde adivinar.
- **Roles como casillas con su descripción**, no un campo de texto donde escribir
  el código del rol:
  > ☑ **Usuario** — usa la aplicación: su planner, calendario y hábitos
  > ☐ **Administrador** — gestiona cuentas y ve las métricas del sistema
- **Los requisitos de la contraseña se ven siempre**, no solo cuando fallan.
- **El listado de usuarios muestra los roles como etiquetas**, no como códigos.
- **Etiqueta encima del campo, nunca solo `placeholder`:** el placeholder
  desaparece al escribir y el usuario ya no sabe qué campo es.

---

## 7. Flexibilidad y eficiencia de uso

*Rápido para el que ya sabe, sin estorbar al que no.*

- **Orden de tabulación lógico** y `Enter` envía el formulario.
- **Autofoco en el primer campo** de login y registro.
- **`autocomplete` correcto:** `username`, `current-password`, `new-password`,
  `email`. Le ahorra al usuario escribir y a ti soporte.
- **Buscador en el listado de usuarios** cuando pase de ~20 cuentas.
- **Accesos directos en el home** a lo que se usa a diario, sin obligar a navegar.

---

## 8. Diseño estético y minimalista

*Cada elemento de más le resta peso a los importantes.*

- **Una idea por pantalla.** El login es un formulario, no un formulario más
  publicidad del producto.
- **Jerarquía por tamaño y peso, no por color.** Si todo está en negrita, nada
  destaca.
- **El rosa solo cuando significa algo.** Si se usa para adornar un encabezado,
  deja de leerse como señal de importancia y el usuario lo ignora.
- **Espacio en blanco generoso:** `--space-6` entre bloques, `--space-4` dentro.
- **Máximo ~75 caracteres por línea.** Por eso el contenido se limita a 1200 px
  aunque la pantalla sea más ancha.

---

## 9. Ayudar a reconocer, diagnosticar y recuperarse de errores

*El error dice qué pasó, por qué y cómo se arregla.*

| ❌ Malo | ✅ Bueno |
|---|---|
| "Error" | "La contraseña debe tener al menos 8 caracteres" |
| "Datos inválidos" | "Ese correo ya está registrado. ¿Quieres iniciar sesión?" |
| "403 Forbidden" | "No tienes permiso para esta sección. Si crees que deberías, pídeselo a un administrador." |
| "404 Not Found" | "No encontramos esa página. Volver al inicio." |
| Traza de Python en pantalla | Pantalla de error propia, con el detalle solo en el log |

**El error va debajo de su campo**, en `--rose-700`, con un icono además del
color. El campo se marca con `aria-invalid="true"` para los lectores de pantalla.

⚠️ **La excepción deliberada:** el login fallido dice "Usuario o contraseña
incorrectos" **sin precisar cuál**. Es peor UX a propósito: si dijera "ese usuario
no existe", cualquiera podría enumerar las cuentas válidas del sistema. Es el
único sitio donde la seguridad gana a la claridad, y conviene tenerlo consciente.

---

## 10. Ayuda y documentación

*Que casi no haga falta, y que cuando haga falta esté al lado.*

- **Texto de ayuda debajo del campo**, no en un tooltip que hay que descubrir:
  *"Mínimo 8 caracteres. Se guarda cifrada."*
- **Cada rol explica lo que hace** en el formulario de asignación, no en un manual
  aparte.
- **Estados vacíos que enseñan a usar la pantalla:** "Aún no hay cuentas además de
  la tuya. Crea la primera con el botón de arriba."
- **El modal del puntaje es documentación viva:** explica el criterio del sistema
  en el momento exacto en que el usuario se lo pregunta.

---

## ♿ Accesibilidad — no es una heurística aparte, es parte de todas

- **Contraste ≥ 4.5:1** en todo texto normal. Medido en DevTools, no a ojo.
- **El color nunca es la única señal.** Toda insignia lleva **también su texto**.
  Compruébalo con el filtro de escala de grises: alrededor de 1 de cada 12 hombres
  tiene daltonismo rojo-verde, y nuestras dos paletas son azul y rosa.
- **Foco de teclado siempre visible.** `:focus-visible` con `outline: 3px solid
  var(--focus-ring)`. **Nunca `outline: none` sin sustituto.**
- **Toda la aplicación se recorre con `Tab`**, sin ratón.
- **HTML semántico:** `<nav>`, `<main>`, `<button>` para acciones y `<a>` para
  navegar. Un `<div onclick>` no lo alcanza el teclado.
- **Toda imagen con `alt`**; decorativa → `alt=""`.
- **Todo campo con su `<label for="...">`.**

---

## ✅ Auditoría — una pasada por pantalla

Para cada pantalla que entregues, responde sí o no:

- [ ] ¿Se ve dónde estoy y con qué cuenta? *(H1)*
- [ ] ¿Todos los textos están en idioma de persona, no de base de datos? *(H2)*
- [ ] ¿Puedo cancelar o volver desde cualquier punto? *(H3)*
- [ ] ¿Los botones se llaman y se ven igual que en el resto? *(H4)*
- [ ] ¿Es difícil equivocarse, y lo destructivo pide confirmación? *(H5)*
- [ ] ¿Está la información a la vista o hay que recordarla? *(H6)*
- [ ] ¿Se puede usar entera con el teclado? *(H7)*
- [ ] ¿Sobra algo? *(H8)*
- [ ] ¿Los errores dicen qué pasó y cómo se arregla? *(H9)*
- [ ] ¿La ayuda está al lado del campo que la necesita? *(H10)*
- [ ] ¿Contraste ≥ 4.5:1 y foco visible? *(accesibilidad)*
- [ ] ¿Se ve bien a 360, 768 y 1280 px? *(responsive)*
