# 📓 Bitácora — Módulo A

> Rellena una entrada por sesión de trabajo con la IA. **Esto es lo que después
> copias a `docs/prompts/`** como evidencia de la rúbrica: prompt real, respuesta,
> qué aceptaste, qué rechazaste y por qué.
>
> No se reconstruye de memoria el último día. Escríbelo el mismo día.

---

## Plantilla

```markdown
### [Fecha] · Paso Pn — <título>

**Prompt usado:** `Pn_xxx.md` (con o sin modificaciones: ...)

**Qué devolvió la IA:**
- ...

**✅ ACEPTADO**
- ... — porque ...

**🔄 CAMBIADO**
- ... — la IA hizo X, lo cambié a Y porque ...

**❌ RECHAZADO**
- ... — porque ...

**Código que generó mal** *(evidencia para la rúbrica)*
```python
# lo que generó
```
```python
# la corrección
```
**Por qué estaba mal:** ...

**Tiempo:** __ h
```

---

### [__/08/2026] · P1 — Modelo de identidad

**Prompt usado:**

**Qué devolvió la IA:**

**✅ ACEPTADO**

**🔄 CAMBIADO**

**❌ RECHAZADO**

**Código que generó mal:**

**Tiempo:**

---

### [__/08/2026] · P2 — `security.py`

---

### [__/08/2026] · P3 — Login y registro

---

### [__/08/2026] · P4 — Home y menú

---

### [__/08/2026] · P5 — Gestión de usuarios

---

### [__/08/2026] · P6 — Pruebas y heurísticas

---

## 🎯 Patrones que voy notando en la IA

> Lo que se repite entre pasos. Sirve para afinar los prompts y es material
> excelente para la reflexión de la fase de Transition.

| Patrón observado | Cuántas veces | Cómo lo prevengo en el prompt |
|---|---|---|
| Propone SQLAlchemy aunque el contexto dice "sin ORM" | | |
| Mete una columna `role` de texto en `users` | | |
| Genera `@admin_required` en vez de comprobar permisos | | |
| Olvida `PRAGMA foreign_keys = ON` en cada conexión | | |
| Escribe el CSS de escritorio primero, no mobile-first | | |
| Usa colores que no cumplen contraste | | |
| Quita el `outline` del foco | | |
