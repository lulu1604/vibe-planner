# P6 — Pruebas automáticas y auditoría de heurísticas

**Objetivo:** cerrar el Módulo A con evidencia repetible. Un `python test_v2.py`
que cualquiera del equipo pueda ejecutar, y una auditoría de las 10 heurísticas
sobre las pantallas que construiste.

**Archivos que salen de aquí:** `test_v2.py` · `AUDITORIA_UX.md` (tu evidencia)

**Tiempo estimado:** 2–3 horas.

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE.md` completo, y después esto:

---

Genera `test_v2.py`, la suite de verificación del Módulo A de VibePlanner v2.
Usa el cliente de pruebas de Flask sobre una **base de datos temporal** — nunca
`vibe_planner.db`, que tiene los datos con los que trabajo.

### Estructura

Antes de importar `app`, apunta `database.DB_PATH` a un archivo temporal y ejecuta
`seed.seed()`. Después importa `app` y ejecuta los casos.

Una función `check(nombre, condicion)` que hace `assert` e imprime `✅` o `❌`, y
un contador al final. Sin `pytest`: `requirements.txt` sigue teniendo una línea.

### Casos a cubrir, con el código del caso en el nombre

**Registro y login**

- `TC 5.1` — Registro válido: la cuenta queda `is_active = 1`, con **exactamente
  un** rol (`usuario`), y `password_hash` **no contiene** la contraseña en claro.
- `TC 5.2` — Usuario o correo duplicado → 409, sin fila nueva.
- `TC 5.3` ⚠️ — **Escalada bloqueada:** enviar el registro con
  `role=admin&roles=admin&is_admin=1` y comprobar que la cuenta queda igualmente
  con el único rol `usuario`.
- `TC 5.4` — Contraseña incorrecta → 401, y el mensaje es **idéntico** al de
  usuario inexistente. Compáralos como cadenas.
- `TC 5.5` — Cuenta desactivada → 403 al intentar entrar.

**Permisos agregativos**

- `TC 6.1` — La cuenta admin tiene los dos roles: sus permisos incluyen
  `planner.ver` (que aporta `usuario`) **y** `usuario.listar` (que aporta `admin`),
  y el conjunto no tiene duplicados.
- `TC 6.2` — Una cuenta solo con `usuario` recibe **403** en `/admin/usuarios`.
- `TC 6.3` — **Revocación inmediata:** con la sesión ya abierta, se le quita el rol
  `admin` y la siguiente petición a `/admin/usuarios` da 403 **sin cerrar sesión**.
  Es el caso que demuestra que los permisos no viven en la cookie.

**Gestión de usuarios**

- `TC 7.1` — Alta administrativa con dos roles: la cuenta creada los tiene ambos.
- `TC 7.2` — Desactivar conserva los datos: crea una cuenta, insértale filas
  relacionadas, desactívala y comprueba que las filas siguen ahí.
- `TC 7.3` — El último administrador no puede quitarse el rol ni desactivarse.

**Sesión**

- `/logout` por GET → **405**, por POST → 302.
- Una ruta protegida sin sesión redirige al login **y** guarda el destino en
  `next`.

### Detalles

- Cada caso independiente: usa `app.test_client()` en un `with` por bloque para no
  arrastrar cookies entre casos.
- Al final, borra el archivo temporal.
- Salida legible: un `✅` por comprobación y un resumen `N/N verificaciones en
  verde`.
- Deja un comentario indicando dónde añaden sus bloques Lucero, Jose y Ana, para
  que el archivo crezca con el mismo formato.

---

## 🎨 Segunda parte: la auditoría de heurísticas (a mano, sin IA)

Recorre `HEURISTICAS_UX.md` y aplica la lista de verificación a las **cinco
pantallas** que construiste: login, registro, home, listado de usuarios y el modal
de roles. Escribe el resultado en `AUDITORIA_UX.md`.

Formato por pantalla:

```markdown
## Pantalla: Listado de usuarios

| # | Heurística | ¿Cumple? | Observación |
|---|---|---|---|
| 1 | Visibilidad del estado | ✅ | El mensaje dice qué roles quedaron |
| 2 | Idioma del usuario | ⚠️ | La columna decía "is_active" — corregido a "Estado" |
| 5 | Prevención de errores | ✅ | Mi propia fila marcada con "(tú)" |
...

**Corregido tras la auditoría:** …
**Pendiente para v3:** …
```

Que aparezcan cosas en ⚠️ no es un problema: es el objetivo. Una auditoría donde
todo sale ✅ a la primera es una auditoría que no se hizo. **Anota lo que
corregiste** — eso es exactamente la evidencia que pide la rúbrica.

### Las cuatro comprobaciones que se hacen con herramientas, no a ojo

1. **Contraste.** DevTools → inspeccionar el texto → el panel de color muestra la
   razón de contraste. Todo texto normal ≥ 4.5:1. Revisa especialmente el texto
   secundario en `--taupe` y cualquier sitio donde se haya colado `--teal` o
   `--steel` como color de texto.
2. **Escala de grises.** DevTools → Rendering → Emulate vision deficiencies →
   Achromatopsia. Recorre el listado de usuarios: ¿se sigue distinguiendo una
   cuenta activa de una desactivada? Si no, falta el texto junto al color.
3. **Solo teclado.** Guarda el ratón. Recorre login → home → administración →
   crear cuenta → modal de roles → cerrar. ¿Ves siempre dónde está el foco?
   ¿Puedes cerrar el modal? ¿El foco vuelve al botón que lo abrió?
4. **Tres anchos.** 360, 768 y 1280 px en el modo responsive de DevTools. Sin
   scroll horizontal en ninguno; nada tapado por la barra inferior en móvil.

---

## ✅ Cierre del Módulo A

**Automático**
- [ ] `python test_v2.py` corre sobre una base temporal
- [ ] Todos los casos en verde
- [ ] `TC 5.3` (escalada bloqueada) verificado ⚠️
- [ ] `TC 6.3` (revocación inmediata) verificado
- [ ] `TC 7.3` (último admin protegido) verificado

**Manual**
- [ ] `AUDITORIA_UX.md` con las cinco pantallas
- [ ] Contraste medido, no estimado
- [ ] Recorrido en escala de grises hecho
- [ ] Recorrido solo con teclado hecho
- [ ] Las tres anchuras revisadas

**Entrega**
- [ ] Todo en `main`
- [ ] Prompts reales copiados a `docs/prompts/` con su resultado
- [ ] Al menos **un ejemplo de código que la IA generó mal** documentado, con la
      corrección — la rúbrica lo pide explícitamente y no se reconstruye de memoria
- [ ] Checklist de `modulos/MODULO_A_Nucleo.md` completo
- [ ] Avisado al equipo de que el núcleo está cerrado
