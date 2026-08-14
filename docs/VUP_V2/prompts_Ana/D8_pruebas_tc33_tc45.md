# D8 — `test_module_d.py` y el recorrido manual (TC-33 … TC-45)

**Objetivo:** convertir los 13 casos de prueba del módulo en algo que se ejecuta
con un comando, y dejar por escrito los tres que no se pueden automatizar.

**Archivos que salen de aquí:** `test_module_d.py` ·
`docs/VUP_V2/evidencia_modulo_d.md`

**Tiempo estimado:** 2–3 horas

**Depende de:** D1 … D7 terminados

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Genera `test_module_d.py`, la suite de verificación del Módulo D. Lee antes
`test_v2.py` (Módulo A) y `test_module_c.py` (Módulo C) y **copia su estructura
exacta**: base temporal con `tempfile`, `database.DB_PATH` redirigido, siembra con
`seed.py`, cliente de pruebas de Flask, y asserts con mensaje descriptivo del
tipo `"TC-34 Falló: corregir el registro duplicó la fila"`.

Sin pytest ni dependencias nuevas: se ejecuta con `python test_module_d.py`.

### 1. El detalle que rompe las pruebas de este proyecto

`security.init_app(app)` valida CSRF en **todo** POST. `test_v2.py` lo resuelve
replantando el token en la sesión **antes de cada petición**, porque al iniciar
sesión `auth.py` hace `session.clear()`. Copia ese helper `_post(...)` tal cual;
si no, todos tus POST devuelven 400 y parecerá que el módulo está roto.

### 2. Los casos que sí se automatizan

| Caso | Qué comprueba |
|---|---|
| **TC-33** | Se crean hábitos de los cuatro tipos con su meta y unidad; aparecen en `/habitos` |
| **TC-34** | Registrar 7 y corregir a 8 deja **una sola fila** con valor 8 |
| **TC-35** | Cumplidos 17, 18 y 19; hoy es 20 → racha **3**; al marcar hoy → **4** |
| **TC-36** | Cumplidos 17 y 19, no el 18; hoy es 19 → racha **1** |
| **TC-37** | 3 Trabajo + 1 Personal + 2 Actividades de 8 → **75 %** y las secciones suman el total |
| **TC-38** | Cuenta recién creada abre `/metricas` → **200**, no 500, y muestra 0 % |
| **TC-39** | 2 hábitos de 3 marcados no alteran el 75 % de tareas |
| **TC-40** | Cada cifra de `system_metrics()` coincide con su `SELECT COUNT(*)` |
| **TC-41** | El HTML de `/admin/metricas` **no contiene** ningún título de tarea, nombre de evento ni correo sembrados |
| **TC-42** | Un usuario sin `metrica.sistema.ver` recibe **403** en `/admin/metricas` |

**Para el TC-41, la prueba se escribe así:** siembra datos con marcadores
reconocibles (una tarea "MARCADOR_SECRETO_TAREA", un evento
"MARCADOR_SECRETO_EVENTO", un usuario "marcador_secreto@test.local"), pide
`/admin/metricas` como admin y comprueba que **ninguno** de los marcadores
aparece en `response.data`. Es la única forma de probar de verdad que no se filtra
nada, incluido lo escondido en el HTML.

**Para TC-35 y TC-36 no uses la fecha real de hoy:** pásale a `habit_streak` un
`today_iso` fijo y siembra los `habit_logs` con fechas relativas a él. Una prueba
que depende del día en que se ejecuta falla sola algún lunes y nadie sabe por qué.

**Para TC-37, si `tasks` aún no tiene `user_id`**, el test debe **saltarse con un
mensaje explícito** (`print("TC-37 OMITIDO: el Modulo B aun no ha migrado tasks")`)
en vez de fallar o, peor, pasar sin comprobar nada.

### 3. Los tres que NO se automatizan

TC-43 (móvil 360 px), TC-44 (tablet y escritorio) y TC-45 (contraste y escala de
grises) necesitan ojos y DevTools. Genera para ellos
`docs/VUP_V2/evidencia_modulo_d.md` con:

- La lista de las 8 pantallas × 3 anchos como casillas para marcar.
- Qué mirar exactamente en cada una (scroll horizontal, barra inferior, Kanban
  apilado, tamaño de los botones).
- Un hueco para pegar las capturas: 360 px, 768 px, 1280 px y una en escala de
  grises.
- Una tabla de ratios de contraste medidos en DevTools, con columna de "medido"
  para rellenar a mano.

### 4. Salida del script

Al final, un resumen legible:

```
TC-33 OK · TC-34 OK · TC-35 OK · TC-36 OK · TC-37 OMITIDO (Modulo B) ...
SUCCESS: 9 de 10 casos automatizados del Modulo D pasaron (1 omitido).
```

Y código de salida distinto de 0 si algo falla, para que se note.

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Corre contra `vibe_planner.db`?** Debe usar una base temporal. Una suite
   que borra la base de demostración el día de la presentación es una anécdota
   que no quieres protagonizar.
2. **¿Los POST fallan con 400?** Falta el helper de CSRF de `test_v2.py`.
3. **¿Las pruebas de racha usan `date.today()`?** Deben usar una fecha fija.
4. **¿El TC-41 comprueba solo que la respuesta es 200?** Eso no prueba nada: hay
   que buscar los marcadores sembrados en el HTML.
5. **¿Algún assert no tiene mensaje?** `assert x == y` a secas no dice qué falló
   cuando lo lea otra persona a las once de la noche.
6. **¿Se saltó los casos difíciles con un `pass` o un `TODO`?** Un test que no
   comprueba nada es peor que no tenerlo: da confianza falsa.
7. **¿Importó pytest o unittest con dependencias nuevas?** `python
   test_module_d.py` y asserts, como el resto del proyecto.

---

## ✅ Verificación del paso

```bash
python test_module_d.py
python test_v2.py          # el nucleo sigue en verde
python app.py test         # los 11 asserts de la v1 siguen en verde
python database.py         # los 4 de Jose
python repo_habits.py      # los 5 tuyos del paso D2
python metrics.py          # los 6 tuyos del paso D3
```

- [ ] Los 10 casos automatizados pasan (o los 9 + TC-37 omitido con mensaje)
- [ ] Ninguna suite anterior se rompió
- [ ] `vibe_planner.db` **no** cambió al ejecutar las pruebas
      (`git status` no la marca como modificada)
- [ ] `evidencia_modulo_d.md` está creado y con las capturas pegadas
- [ ] Las tres casillas manuales (TC-43, TC-44, TC-45) están marcadas y firmadas

---

## 🎁 Para la rúbrica

Este paso es el que más material de evidencia produce. Antes de cerrarlo, asegúrate
de tener en `docs/prompts/04-ana-modulo-d.md`:

- Los 8 prompts reales que usaste (los de esta carpeta, con tus modificaciones).
- Al menos **un ejemplo de código mal generado** con su corrección y el porqué.
  Los candidatos más probables de este módulo, por orden: la racha contando
  cumplimientos totales en vez de días consecutivos, el `upsert` escrito como
  `SELECT` + `INSERT`, y algún porcentaje de sección sin proteger la división
  entre cero.
- Qué aceptaste, qué cambiaste y qué rechazaste, con el motivo en una línea.
