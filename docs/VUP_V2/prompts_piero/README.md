# 🧑‍💻 Prompts de Piero — Módulo A (Núcleo)

**Carpeta personal. Está en `.gitignore` — no se sube al repo.**

> ⚠️ **Ojo con la rúbrica.** Esta carpeta es tu banco de trabajo: prompts
> reutilizables, ordenados por paso. La **evidencia** que pide el curso (prompt
> literal + qué devolvió la IA + qué aceptaste/rechazaste y por qué + un ejemplo
> de código mal generado) va en `docs/prompts/`, que **sí** se versiona.
> Trabaja aquí, y al terminar cada paso copia el prompt real que usaste a
> `docs/prompts/` con su resultado.

---

## 🔄 Cambio de alcance acordado

**Solo dos roles: `usuario` y `admin`.** El rol `lider` y la historia US10
(asignar tareas a otros) pasan al backlog v3. Menos superficie, misma
arquitectura: el modelo de permisos sigue siendo agregativo y basado en tablas,
así que añadir `lider` mañana es **una entrada en `seed.py`**, no un refactor.

Y sigue siendo cierto lo importante: **el administrador es también un usuario
normal**. Tiene los dos roles a la vez y sus permisos son la unión de ambos.

```
permisos_efectivos(usuario) = ⋃ permisos(rol)   para cada rol asignado
```

| Rol | Cómo se obtiene | Qué aporta |
|---|---|---|
| `usuario` | Automático al registrarse. **Todos lo tienen** | Su planner, kanban, calendario, hábitos, sus métricas |
| `admin` | Solo por semilla o por otro admin | Gestión de cuentas + métricas del sistema |

---

## 🗺️ El plan, en orden

Cada paso tiene su prompt. **No saltes pasos**: cada uno asume que el anterior
está terminado y probado.

| Paso | Qué construyes | Prompt | Listo cuando |
|---|---|---|---|
| **P0** | Preparación: venv, estructura, `tokens.css`, fuentes | *(manual, ver abajo)* | `flask --version` responde y la estructura existe |
| **P1** | Modelo de identidad: esquema + `database.py` + `repo_users.py` + `seed.py` | `P1_modelo_identidad.md` | `python seed.py` crea 24 permisos, 2 roles y el admin |
| **P2** | La guardia: `security.py` | `P2_guardia_security.md` | Un usuario con 2 roles devuelve la unión de permisos |
| **P3** | Login, registro y logout **con su UI** | `P3_auth_login_registro.md` | Me registro, entro, salgo y vuelvo a entrar |
| **P4** | Home con menú de módulos (shell responsive) | `P4_home_menu.md` | El menú muestra solo lo que mis permisos permiten |
| **P5** | Gestión de usuarios (panel de admin) | `P5_gestion_usuarios.md` | Creo cuentas, asigno roles y desactivo |
| **P6** | Pruebas + auditoría de heurísticas | `P6_pruebas_y_heuristicas.md` | `test_v2.py` en verde y las 10 heurísticas revisadas |

**Entre P2 y P3 está el hito H2:** en cuanto `security.py` esté en `main`,
avísale al grupo. Lucero, Jose y Ana están esperando ese contrato para arrancar
de verdad.

---

## 📂 Archivos de esta carpeta

| Archivo | Para qué |
|---|---|
| `README.md` | Este plan |
| `00_CONTEXTO_BASE.md` | **El bloque que pegas al inicio de CADA prompt.** Sin él la IA inventa arquitectura |
| `HEURISTICAS_UX.md` | Las 10 heurísticas de Nielsen aplicadas a VibePlanner, con ejemplos concretos |
| `P1…P6_*.md` | Un prompt por paso |
| `_bitacora.md` | Tu registro: qué pediste, qué salió mal, qué corregiste |

---

## ▶️ Cómo se usa un prompt

1. Abre el archivo del paso.
2. Pega **`00_CONTEXTO_BASE.md` completo** y después el prompt del paso.
3. Revisa lo que devuelve **antes** de pegarlo al proyecto. Busca específicamente
   las trampas listadas al final de cada prompt: son las que la IA falla.
4. Ejecuta la verificación del paso.
5. Anota en `_bitacora.md` qué aceptaste, qué rechazaste y por qué.
6. Copia el prompt real y su resultado a `docs/prompts/` (evidencia de la rúbrica).

---

## 🔧 P0 — Preparación (manual, 15 minutos)

No necesita IA. Hazlo antes de lanzar el P1.

```bash
cd D:\VibeCoding\proyect_final
python -m venv venv
venv\Scripts\activate
pip install Flask==3.0.3
pip freeze > requirements.txt
```

Crea la estructura vacía:

```
templates/auth/    templates/admin/    templates/errors/    templates/components/
static/css/        static/js/          static/fonts/
```

Y trae dos cosas del design system:

1. **`static/css/tokens.css`** — cópialo entero de
   `docs/VUP_V2/00_Design_System.md` § 4. Es la base de todo lo visual y lo vas a
   necesitar desde el P3.
2. **Las fuentes** — descarga `Inter-Variable.woff2` y `JetBrainsMono-Medium.woff2`
   y ponlas en `static/fonts/`. Auto-alojadas, sin CDN: la demo tiene que
   funcionar aunque el aula se quede sin internet.

**Verifica:** `python -c "import flask; print(flask.__version__)"` → `3.0.3`.

---

## ✅ Seguimiento

- [ ] **P0** Preparación
- [ ] **P1** Modelo de identidad
- [ ] **P2** `security.py`
- [ ] 🔒 **H2** — contrato publicado en `main` y **anunciado al grupo**
- [ ] **P3** Login y registro
- [ ] **P4** Home con menú
- [ ] **P5** Gestión de usuarios
- [ ] **P6** Pruebas y heurísticas
- [ ] Prompts copiados a `docs/prompts/` para la rúbrica
