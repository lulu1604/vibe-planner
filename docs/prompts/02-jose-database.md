# 📝 Evidencia de Prompt — Módulo de Persistencia (`database.py`)

**Integrante:** Jose Cabrera (Dueño de Persistencia / Esquema SQL)  
**Fecha:** 12 de Agosto de 2026  
**Proyecto:** VibePlanner  

---

## 💬 Prompt Utilizado con la IA

> *"Actúa como un desarrollador backend sénior. Implementa en Python puro con SQLite3 las funciones `update_status(task_id, new_status)`, `delete_task(task_id)` y `get_daily_progress()` para la capa de persistencia `database.py`. Valida que `new_status` pertenezca a `['pending', 'in_progress', 'completed']`, evita caídas por división entre cero en `get_daily_progress()` devolviendo `{"total": n, "completed": n, "percent": n}`, y asegura que la ruta de la base de datos sea absoluta para que funcione en PythonAnywhere."*

---

## ⚠️ Código Generado Erróneamente por la IA y Corrección Humana (Evidencia para Rúbrica)

### 1. Error de la IA: Ruta Relativa en la Base de Datos
* **Código de la IA:**  
  `DB_PATH = "vibe_planner.db"`
* **Problema:** En PythonAnywhere o servidores WSGI, las rutas relativas se resuelven respecto al directorio de ejecución del proceso web (`/var/www/`), lo que causa un error de `sqlite3.OperationalError: unable to open database file`.
* **Corrección aplicada por Jose:**  
  `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`  
  `DB_PATH = os.path.join(BASE_DIR, "vibe_planner.db")`

### 2. Error de la IA: ZeroDivisionError en el Cálculo de Progreso
* **Código de la IA:**  
  `percent = (completed / total) * 100`
* **Problema:** Si la base de datos inicia vacía (`total = 0`), la aplicación lanza una excepción no controlada `ZeroDivisionError: division by zero` tumbando la página.
* **Corrección aplicada por Jose:**  
  `percent = round((completed / total) * 100, 1) if total > 0 else 0.0`

---

## 🧪 Pruebas Unitarias Directas
Se incorporaron 4 pruebas con `assert` al final de `database.py` para verificar inserción, lectura, actualización de estado y borrado de tareas.
