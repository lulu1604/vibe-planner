# 🌱 Prompts de Ana — Módulo D (Hábitos, Métricas y Design System)

**Carpeta de trabajo de Ana Cusi.** Mismo formato que `prompts_piero/`: un
archivo por paso, listos para pegar en Claude Code sin tener que explicar nada
más.

> ⚠️ **Ojo con la rúbrica.** Esta carpeta es el banco de trabajo. La **evidencia**
> que pide el curso (prompt literal + qué devolvió la IA + qué aceptaste,
> cambiaste o rechazaste y por qué + un ejemplo de código mal generado) va en
> `docs/prompts/`, que **sí** se versiona. Al cerrar cada paso, copia el prompt
> real que usaste con su resultado a `docs/prompts/04-ana-modulo-d.md`.

---

## 🎯 Qué se construye aquí

Tres cosas que se apoyan entre sí:

| Parte | Historias | Qué responde |
|---|---|---|
| **Hábitos** | US13 | "¿Cuántos días llevo seguidos?" |
| **Métricas** | US14 (propias) · US15 (sistema) | "¿Cómo me fue hoy?" / "¿cómo va el sistema?" |
| **Design System** | US16 | Que las 8 pantallas parezcan **una sola** aplicación |

Casos de prueba que cierra este módulo: **TC-33 … TC-45** (13 casos, el bloque
más grande del plan de pruebas).

---

## 🗺️ El plan, en orden

**No saltes pasos.** Cada prompt asume que el anterior está terminado y probado.

| Paso | Qué construyes | Archivo | Listo cuando |
|---|---|---|---|
| **D0** | Leer contexto y hallazgos *(15 min, sin IA)* | `00_CONTEXTO_BASE_ANA.md` · `00_HALLAZGOS_Y_RIESGOS.md` | Sabes qué contratos NO puedes tocar |
| **D1** | Esquema: `habits` + `habit_logs` | `D1_esquema_habitos.md` | `python seed.py` corre y las dos tablas existen |
| **D2** | `repo_habits.py` — el único que toca esas tablas | `D2_repo_habits.md` | El `upsert` no duplica la fila de hoy (TC-34) |
| **D3** | `metrics.py` — rachas, resumen del día, agregados | `D3_metrics.md` | La racha da 3 → 4 (TC-35) y se rompe con un hueco (TC-36) |
| **D4** | Blueprint `habitos` + pantalla de hábitos | `D4_blueprint_habitos_ui.md` | Creo un hábito, lo marco y veo la racha (TC-33) |
| **D5** | Pantalla `/metricas` (las tuyas) | `D5_metricas_ui.md` | 75 % por sección (TC-37) y cuenta vacía sin 500 (TC-38) |
| **D6** | Panel `/admin/metricas` (del sistema) | `D6_metricas_sistema.md` | Los números cuadran con `COUNT(*)` (TC-40) y sin permiso da 403 (TC-42) |
| **D7** | Design System transversal | `D7_design_system_responsive.md` | Las 8 pantallas a 360/768/1280 px (TC-43, TC-44, TC-45) |
| **D8** | `test_module_d.py` + recorrido manual | `D8_pruebas_tc33_tc45.md` | Los 13 asserts en verde |

**Hito D3 (avisa al grupo):** cuando `metrics.py` esté en `main`, dilo — es lo
que Piero necesita para llenar las cifras del home, que hoy muestran `—`.

---

## ▶️ Cómo se usa un prompt en Claude Code

1. Abre una sesión nueva de Claude Code en la raíz del proyecto.
2. Pega **`00_CONTEXTO_BASE_ANA.md` completo** y después el prompt del paso.
   *(Sin el contexto la IA inventa otra arquitectura: propone SQLAlchemy, mete
   una columna `role` de texto, o escribe el CSS de escritorio primero.)*
3. **Lee lo que devuelve ANTES de aceptarlo.** Cada prompt termina con una lista
   de trampas: son exactamente las que la IA falla en este módulo.
4. Ejecuta la verificación del paso.
5. Anota en `_bitacora.md` qué aceptaste, qué cambiaste y qué rechazaste.
6. Copia el prompt real y su resultado a `docs/prompts/`.

> 💡 **Atajo válido:** si trabajas con Claude Code con acceso al repo, puedes
> decirle: *"Lee `docs/VUP_V2/prompts_Ana/00_CONTEXTO_BASE_ANA.md` y después
> ejecuta `docs/VUP_V2/prompts_Ana/D2_repo_habits.md`"*. El resultado es el
> mismo y se equivoca menos, porque lee los archivos reales en vez de fiarse de
> lo que le cuentes.

---

## 📂 Archivos de esta carpeta

| Archivo | Para qué |
|---|---|
| `README.md` | Este plan |
| `00_CONTEXTO_BASE_ANA.md` | **El bloque que se pega al inicio de CADA prompt** |
| `00_HALLAZGOS_Y_RIESGOS.md` | Lo que encontré revisando el repo y que te va a morder si no lo sabes |
| `D1…D8_*.md` | Un prompt por paso |
| `_bitacora.md` | Tu registro para la rúbrica |

---

## 🚦 Dependencias reales (revisadas en el repo, no supuestas)

| Necesitas… | ¿Está listo? | Si no lo está |
|---|---|---|
| `security.py` (H2) | ✅ **Sí**, en `main` | — |
| `base.html` + `tokens.css` + `components.css` | ✅ **Sí** | — |
| Permisos `habito.*` y `metrica.*` sembrados | ✅ **Sí**, ya están en `seed.py` | — |
| Entradas del menú `habitos.lista` y `habitos.metricas` | ✅ **Sí**, ya reservadas en `home.py` | — |
| Tablas `habits` y `habit_logs` | ❌ **No existen** | Las creas tú en **D1** |
| Tabla `tasks` con `user_id` (Módulo B) | ❌ **No**, sigue en la versión v1 | **D3** lo resuelve con degradación honesta — lee `00_HALLAZGOS_Y_RIESGOS.md` §2 |
| Eventos (Módulo C) | ✅ **Sí**, `events` existe | — |

---

## ✅ Seguimiento

- [ ] **D0** Contexto leído
- [ ] **D1** Esquema `habits` + `habit_logs` (coordinado con Jose)
- [ ] **D2** `repo_habits.py`
- [ ] **D3** `metrics.py` → 🔔 **avisar al grupo**
- [ ] **D4** Blueprint y pantalla de hábitos
- [ ] **D5** `/metricas`
- [ ] **D6** `/admin/metricas`
- [ ] **D7** Design System y responsive
- [ ] **D8** Pruebas TC-33 … TC-45
- [ ] Prompts copiados a `docs/prompts/` para la rúbrica
