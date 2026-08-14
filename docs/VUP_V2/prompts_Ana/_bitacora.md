# 📓 Bitácora — Módulo D (Ana)

> Una entrada por sesión de trabajo con la IA. **Esto es lo que después copias a
> `docs/prompts/04-ana-modulo-d.md`** como evidencia de la rúbrica: prompt real,
> respuesta, qué aceptaste, qué cambiaste, qué rechazaste y por qué.
>
> No se reconstruye de memoria el último día. Escríbelo el mismo día.

---

## Plantilla

```markdown
### [Fecha] · Paso Dn — <título>

**Prompt usado:** `Dn_xxx.md` (con o sin modificaciones: ...)

**Qué devolvió la IA:**
- ...

**✅ ACEPTADO**
- ... — porque ...

**🔄 CAMBIADO**
- ... — la IA hizo X, lo cambié a Y porque ...

**❌ RECHAZADO**
- ... — porque ...

**Código que generó mal** *(evidencia para la rúbrica)*
​```python
# lo que generó
​```
​```python
# la corrección
​```
**Por qué estaba mal:** ...

**Tiempo:** __ h
```

---

### [__/08/2026] · D1 — Esquema `habits` y `habit_logs`

**Prompt usado:**

**Qué devolvió la IA:**

**✅ ACEPTADO**

**🔄 CAMBIADO**

**❌ RECHAZADO**

**Código que generó mal:**

**Tiempo:**

---

### [__/08/2026] · D2 — `repo_habits.py`

---

### [__/08/2026] · D3 — `metrics.py`

---

### [__/08/2026] · D4 — Blueprint y pantalla de hábitos

---

### [__/08/2026] · D5 — `/metricas`

---

### [__/08/2026] · D6 — `/admin/metricas`

---

### [__/08/2026] · D7 — Design System y responsive

---

### [__/08/2026] · D8 — Pruebas TC-33 … TC-45

---

## 🎯 Patrones que voy notando en la IA

> Lo que se repite entre pasos. Sirve para afinar los prompts y es material
> excelente para la reflexión de la fase de Transition.

| Patrón observado | Cuántas veces | Cómo lo prevengo en el prompt |
|---|---|---|
| Cuenta la racha como cumplimientos totales, no días consecutivos | | |
| Escribe el registro diario como `SELECT` + `INSERT` en vez de `upsert` | | |
| Se olvida de proteger la división entre cero en las secciones | | |
| Mete los hábitos dentro del porcentaje de tareas | | |
| Usa `{% block contenido %}` en vez de `content` → página en blanco | | |
| Olvida el `<input name="_csrf">` y el POST da 400 | | |
| Propone Chart.js o un icono desde un CDN | | |
| Escribe el CSS de escritorio primero, no mobile-first | | |
| Usa `--teal` o `--rose` como color de texto (no cumplen contraste) | | |
| Quita el `outline` del foco | | |
| Propone enseñar "los usuarios más activos" en el panel de admin | | |
| Usa `datetime.now()` sin zona horaria | | |
