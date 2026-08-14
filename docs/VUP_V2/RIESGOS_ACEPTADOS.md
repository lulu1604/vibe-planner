# ⚠️ Riesgos aceptados — lo que sabemos que falla y decidimos no arreglar

**Fecha:** 14/08/2026 · **Contexto:** auditoría de preentrega, con los cuatro módulos integrados

De los 31 defectos que encontró la auditoría, **29 están corregidos**. Estos dos
no, y no por descuido: el arreglo correcto choca con una restricción de la
plataforma o con el alcance acordado de la entrega.

Se escriben aquí porque un riesgo conocido y documentado es una decisión de
ingeniería; el mismo riesgo sin documentar es un descuido que alguien descubre
en la demo.

---

## R-A1 · El registro público permite averiguar si un correo está registrado

**Qué pasa.** `POST /register` con un usuario inventado y un correo que ya
existe responde **409**. Con un correo que no existe, crea la cuenta. Repitiendo
la petición se puede comprobar, correo a correo, quién tiene cuenta en el
sistema.

**Por qué no se arregla.** La solución canónica es no confirmar nada en el
registro y mandar la verificación por correo. **PythonAnywhere free tier no
tiene SMTP saliente** (Riesgo #1 de Inception), así que esa vía está cerrada por
la plataforma, no por falta de tiempo.

La alternativa —responder siempre 200 y no decir nada— dejaría a una persona con
un correo ya registrado sin entender por qué no puede entrar, y sin forma de
recuperar su cuenta. Cambiaríamos un problema de privacidad por uno de usabilidad
que afecta a todo el mundo.

**Qué sí está protegido.** El **login** no filtra: `/login` responde exactamente
el mismo mensaje exista o no la cuenta, y `repo_users` compara contra un hash
señuelo para que tampoco se distinga por el tiempo de respuesta. Eso está
probado en TC-04 y en TC-5.4.

**Mitigación barata si el equipo la quiere:** un contador por IP en memoria en
`auth.py` que frene a partir de N registros seguidos. No cierra el agujero, lo
encarece.

---

## R-A2 · El link de invitación no caduca y sirve para varias personas

**Qué pasa.** El token de `/invitacion/<token>` es válido para siempre y lo puede
usar cualquiera que lo reciba, no solo la persona a la que se le mandó. Además,
`accept_invitation` inserta una fila nueva cada vez que alguien distinto lo
acepta, y cada una trae su propio token: los links válidos se multiplican solos.
El estado `revoked` existe en el esquema y **no lo escribe nadie**.

**Por qué no se arregla del todo.** El arreglo completo es una pantalla de
gestión de invitaciones —ver quién aceptó, revocar, caducar— y eso es una
historia de usuario que no está en el alcance de la v2.1.

**Qué sí se hizo.** Que aceptar deje de acuñar tokens nuevos: la fila de
asistencia se inserta sin token propio. El número de links válidos ya no crece.

**Lo que queda vivo:** un link filtrado sigue dando acceso a ver y aceptar ese
evento. El daño está acotado —un evento concreto, no la cuenta— y el contenido
que expone es el título, la fecha y el anfitrión de ese evento.

**Para v3:** revocación desde la pantalla del evento, y caducidad por fecha.

---

## Lo que NO es un riesgo aceptado

Conviene decirlo, porque en la auditoría salieron y se descartaron:

- **La tabla `tasks` de la v1 sigue existiendo.** Es deliberado y no es deuda:
  `test_v2.py` la puebla a propósito en TC-05 y en el TC-08 bloqueante, para
  impedir que vuelva el respaldo que filtraba tareas ajenas. Es un banco de
  pruebas, no código muerto.
- **`SESSION_COOKIE_SECURE` es `False` en local.** También deliberado: con
  `True` sobre `http://127.0.0.1` nadie podría iniciar sesión en desarrollo. Se
  enciende solo cuando existe `VIBEPLANNER_SECRET`, que solo existe en
  producción. Ver `docs/despliegue.md`.
