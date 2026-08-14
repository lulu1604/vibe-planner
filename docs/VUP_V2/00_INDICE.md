# 📚 VibePlanner v2.0 — Documentación del Update

**Curso:** Fundamentals of Vibe Coding — ESAN Global Week 2026
**Metodología:** VUP (Vibe Unified Process)
**Equipo:** Lucero Ayala · Jose Cabrera · Piero Calderón · Ana Cusi

> **Empieza por aquí.** Este documento dice qué leer, en qué orden y qué te toca.

---

## ⚠️ Lo primero: la v1 no se toca

Toda esta carpeta es **nueva**. Los siete documentos originales siguen intactos en
`docs/vup_deliverables/` y son la evidencia de la versión 1.0 entregada. Esta
carpeta documenta el **update**, y ambas versiones conviven:

```
docs/
├── vup_deliverables/     ← v1.0 ENTREGADA. No se modifica.
└── VUP_V2/               ← esta carpeta: el update
```

---

## 🎯 Qué es la v2 en un párrafo

La v1 fue un planificador de **un solo usuario, sin cuentas**, cuyo diferenciador
era el puntaje explicable. La v2 conserva ese motor **intacto** y lo convierte en
una plataforma multiusuario con **roles agregativos** gobernados por una tabla de
permisos, calendario mensual con invitaciones por link, tablero Kanban, gestión de
hábitos, métricas y una interfaz responsive.

**La decisión que gobierna toda la arquitectura:**

> El rol no es una categoría a la que perteneces, es una **bolsa de permisos que
> cargas**. Un usuario puede llevar varios roles a la vez y sus permisos son la
> **unión** de todos ellos. Por eso el administrador es también un usuario normal:
> planifica su día y administra el sistema con la misma cuenta.

Y la política de cuentas que se deriva de ello:

| Vía | Quién | Roles que otorga |
|---|---|---|
| Registro público `/register` | Cualquier visitante | `usuario` — **siempre, sin excepción** |
| Alta administrativa `/admin/usuarios` | Quien tenga `usuario.crear` | Cualquier combinación |
| Semilla `seed.py` | Una vez, al desplegar | El administrador inicial (`usuario` + `admin`) |

> 🔻 **Alcance v2.1 acordado:** solo **dos roles**, `usuario` y `admin`. El rol
> `lider` y la historia US10 (asignar tareas a otros) pasan al backlog v3 por
> tiempo. La arquitectura no cambia: volver a añadirlos mañana es una entrada en
> `seed.py`. El plan manual pasa de 45 a **43 casos**.

**No hay registro público de administrador.** El primero nace de la semilla; todos
los demás los crea él.

---

## 📖 Orden de lectura

### Todos, sin excepción — 20 minutos

1. **Este índice.**
2. **`01_Inception.md`** § 1 (visión y roles agregativos) y § 2 (fuera de alcance).
3. **`04_Construction_I.md`** § 8 — **Reglas que no se rompen**. Trece reglas.
   Léelas antes de escribir una línea.
4. **Tu documento de módulo** en `modulos/`.

### Antes de tocar el esquema

4b. **`REVISION_BD_ESCALABILIDAD.md`** — ocho hallazgos sobre la base de datos.
    Cuatro se aplican **antes** de crear el esquema, cuando todavía no hay datos
    de nadie: después cuestan una migración coordinada con todo el equipo.

### Antes de programar tu parte

5. **`02_Elaboration_I.md`** — las historias con sus criterios Given-When-Then.
   Solo las tuyas.
6. **`03_Elaboration_II.md`** § 1 (arquitectura) y § 5 (mapa de módulos).
7. **`05_Construction_II.md`** — el código del núcleo y los contratos congelados.

### Antes de maquetar cualquier pantalla

8. **`00_Design_System.md`** — completo. Tokens, paletas, tipografía, responsive.

### Antes de dar tu parte por terminada

9. **`06_Construction_III.md`** — tus casos del plan manual.
10. **`07_Transition.md`** § 2 — despliegue.

---

## 📂 Contenido de la carpeta

| Archivo | Qué contiene |
|---|---|
| `00_INDICE.md` | Este documento |
| `00_Design_System.md` | Paletas, tipografía, tokens CSS, componentes, responsive |
| `01_Inception.md` | Visión, alcance, historias, riesgos, definición de terminado |
| `02_Elaboration_I.md` | 16 historias SMART · 45 casos Given-When-Then |
| `03_Elaboration_II.md` | Arquitectura, 5 plays, diagramas UML, crítica a la IA |
| `04_Construction_I.md` | Stack, estructura de archivos, checklist, hitos, reglas |
| `05_Construction_II.md` | Código del núcleo + contratos de B, C y D |
| `06_Construction_III.md` | Plan de pruebas manual, 45 casos |
| `07_Transition.md` | Despliegue, análisis del código, reflexión |
| `BACKLOG_v3.md` | Lo que queda fuera y por qué |
| `modulos/MODULO_A_Nucleo.md` | Cuentas, roles, permisos, semilla |
| `modulos/MODULO_B_Planner_Kanban.md` | Planner diario, Kanban, asignación |
| `modulos/MODULO_C_Calendario.md` | Calendario mensual e invitaciones |
| `modulos/MODULO_D_Habitos_Metricas.md` | Hábitos, métricas y design system |
| `REVISION_BD_ESCALABILIDAD.md` | Auditoría del esquema: 8 hallazgos, 4 a aplicar antes de programar |
| `prompts_piero/` | Plan paso a paso y prompts del Módulo A *(personal, en `.gitignore`)* |

---

## 👥 Reparto por módulos

| Módulo | Dueño | Historias | Arranca |
|---|---|---|---|
| **A — Núcleo** | **Piero Calderón** | US5, US6, US7 | 🔴 Inmediato — bloquea a todos |
| **B — Planner y Kanban** | Lucero Ayala | US1–US4, US8, US9 | Tras el hito H2 |
| **C — Calendario** | Jose Cabrera *(+ dueño del esquema)* | US11, US12 | Tras el hito H2 |
| **D — Hábitos, métricas y Design System** | Ana Cusi | US13, US14, US15, US16 | Diseño desde el día 1; métricas al final |

### 🚩 Dos cosas que hay que confirmar en la reunión de arranque

1. **El reparto de v1 se contradecía a sí mismo.** En `tareas/reparto.md`, la tabla
   resumen decía "Piero → `app.py` + despliegue, Ana → frontend", pero los títulos
   de las secciones decían justo lo contrario. Esta propuesta resuelve la
   ambigüedad hacia **Piero = backend/núcleo** (que es lo que él pidió) y
   **Ana = design system**. Confírmenlo antes de empezar.
2. **El Módulo D lleva la carga más desigual:** un módulo funcional mediano **más**
   el design system transversal. Si al arrancar no entra, el diseño puede pasar a
   quien cierre antes su módulo. Decidirlo el primer día, no el jueves.

---

## 🗓️ Orden de trabajo

```
DÍA 1  ├─ Reunión: confirmar reparto y congelar el alcance
       ├─ Piero: schema_v2.sql + database.py + repo_users.py
       └─ Ana: tokens.css + base.html (puede avanzar con datos falsos)

DÍA 2  ├─ Piero: security.py + auth.py + seed.py
       └─ 🔒 HITO H2: contrato de security.py publicado en main y ANUNCIADO
                     ← aquí arrancan de verdad B, C y D

DÍA 3-4├─ Lucero: repo_tasks + planner + kanban
       ├─ Jose:   repo_events + calendario + invitaciones
       ├─ Ana:    repo_habits + metrics + componentes
       └─ Piero:  admin.py + migración + revisión de PRs

DÍA 5  ├─ Integración: todos los módulos en main
       ├─ Design system aplicado a las 8 pantallas
       └─ test_v2.py completo

DÍA 6  ├─ Plan manual: 45 casos en local
       ├─ Despliegue en PythonAnywhere + variables de entorno + seed
       └─ Plan manual: los 3 críticos contra producción

DÍA 7  └─ Datos de demostración + ensayo de la presentación
```

**H2 es el cuello de botella de la semana.** Mientras el núcleo no esté en `main`,
los otros tres módulos maquetan a ciegas. Es la misma lección que dejó escrita el
reparto de v1: los módulos base primero.

---

## 🔒 Las reglas que no se rompen (versión corta)

Las trece completas están en `04_Construction_I.md` § 8. Las cinco que más
duelen si se olvidan:

1. La instancia de Flask se llama **exactamente `app`** a nivel de módulo. Sin
   application factory: PythonAnywhere hace `from app import app`.
2. **Toda** consulta que devuelva datos de un usuario lleva `user_id` **dentro del
   `WHERE`**. Filtrar en Python después no cuenta.
3. Los decoradores comprueban **permisos**, nunca nombres de rol.
4. El `user_id` sale **siempre** de la sesión, jamás del formulario.
5. Sin APIs externas, sin CDN, sin dependencias nuevas. `requirements.txt` tiene
   una sola línea.

---

## ⚠️ Los tres casos que bloquean el release

Si alguno falla, **no se despliega**. Son agujeros de seguridad, no defectos
cosméticos.

| Caso | Qué prueba |
|---|---|
| **TC-03** | Un `role=admin` enviado en el formulario de registro no otorga nada |
| **TC-08** | Tener `planner.editar` no permite editar la tarea de otro (responde 404) |
| **TC-11** | Cada cuenta ve exactamente sus datos y ninguno ajeno |

---

## 📝 Evidencia para la rúbrica

Cada prompt que uses con la IA va a `docs/prompts/` **el mismo día**, con: el
prompt literal, lo que devolvió, qué aceptaste o rechazaste **y por qué**, y al
menos un ejemplo real de código que la IA generó mal y cómo se corrigió.

Eso no se reconstruye de memoria el último día, y la rúbrica lo pide
explícitamente.
