# 📝 Registro de Prompts de IA — Módulo de Persistencia (`database.py`)

**Integrante:** Jose Cabrera (Dueño de Persistencia / Esquema SQL)  
**Fecha:** 12 de Agosto de 2026  
**Proyecto:** VibePlanner  

---

## 💬 Prompt Utilizado

> *"Implementa en Python puro con SQLite3 las funciones `update_status(task_id, new_status)`, `delete_task(task_id)` y `get_daily_progress()` para el archivo `database.py`. Debe validar que `new_status` pertenezca a `['pending', 'in_progress', 'completed']`, manejar prevención de división entre cero en `get_daily_progress()` devolviendo `{"total": n, "completed": n, "percent": n}`, y usar `g.db` de Flask con rutas absolutas."*

---

## ⚠️ Ejemplo de Código Inicial que la IA Generó Mal y se Corrigió

### ❌ Código generado erróneamente por la IA:
```python
# La IA sugirió usar una ruta relativa simple:
DB_PATH = "vibe_planner.db"

# La IA no previno división por cero en el cálculo del porcentaje:
def get_daily_progress():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    completed = db.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
    return {
        "total": total,
        "completed": completed,
        "percent": (completed / total) * 100  # 💥 ZeroDivisionError cuando total = 0
    }
```

### ✅ Corrección Aplicada (Evidencia de Ingeniería Humana):
1. **Ruta Absoluta:** Se calculó la ruta a partir de `__file__` (`BASE_DIR = os.path.dirname(os.path.abspath(__file__))`) para garantizar que la app funcione sin errores de ruta al desplegar en **PythonAnywhere**.
2. **Prevención de ZeroDivisionError:** Se validó la condición `total > 0` antes de calcular el porcentaje para evitar caídas del servidor cuando no existen tareas registradas.
3. **Validación estricta de estado:** Se restringió `new_status` a los valores permitidos (`pending`, `in_progress`, `completed`).
