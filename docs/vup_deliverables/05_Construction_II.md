# 📋 VUP Phase 5: Construction Phase II Document

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Phase:** Construction Phase II (Code Base & Technical Specification)  

---

## 💻 1. Production Source Code

### 1.1 `database.py` (Persistence & Database Layer)
```python
"""
VibePlanner - Database & Persistence Layer
------------------------------------------
DUEÑO DE ESTE ARCHIVO: Jose Cabrera
"""

import os
import sqlite3
from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vibe_planner.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    NOT NULL,
    category          TEXT    DEFAULT 'General',
    priority_level    INTEGER NOT NULL DEFAULT 2,   -- 1: High, 2: Medium, 3: Low
    due_date          TEXT    NOT NULL,             -- ISO Date YYYY-MM-DD
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    status            TEXT    DEFAULT 'pending',    -- pending | in_progress | completed
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10.0)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def get_tasks(filter_status=None):
    db = get_db()
    if filter_status:
        rows = db.execute("SELECT * FROM tasks WHERE status = ? ORDER BY id DESC", (filter_status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

def get_task_by_id(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None

def add_task(task_data):
    db = get_db()
    cursor = db.execute(
        """INSERT INTO tasks (title, category, priority_level, due_date, estimated_minutes, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            task_data["title"],
            task_data.get("category", "General"),
            task_data.get("priority_level", 2),
            task_data["due_date"],
            task_data.get("estimated_minutes", 30),
            task_data.get("status", "pending")
        ),
    )
    db.commit()
    return cursor.lastrowid if cursor.lastrowid else True

def update_status(task_id, new_status):
    allowed = ["pending", "in_progress", "completed"]
    if new_status not in allowed:
        return False
    db = get_db()
    cursor = db.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    db.commit()
    return cursor.rowcount > 0

def delete_task(task_id):
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return cursor.rowcount > 0

def get_daily_progress():
    db = get_db()
    total_row = db.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()
    completed_row = db.execute("SELECT COUNT(*) AS completed FROM tasks WHERE status = 'completed'").fetchone()
    
    total = total_row["total"] if total_row else 0
    completed = completed_row["completed"] if completed_row else 0
    percent = round((completed / total) * 100, 1) if total > 0 else 0.0
    
    return {"total": total, "completed": completed, "percent": percent}

if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("INSERT INTO tasks (title, category, priority_level, due_date, estimated_minutes) VALUES (?, ?, ?, ?, ?)", ("Test", "Academic", 1, "2026-08-15", 45))
    conn.commit()
    test_id = cursor.lastrowid
    assert test_id is not None, "Assert 1 Failed"
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (test_id,)).fetchone()
    assert row["title"] == "Test", "Assert 2 Failed"
    conn.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (test_id,))
    conn.commit()
    conn.execute("DELETE FROM tasks WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()
    print("SUCCESS: database.py unit tests passed!")
```

---

### 1.2 `scoring.py` (Algorithm Scoring Engine)
```python
"""
VibePlanner - Motor de puntuación transparente
-------------------------------------------------
DUEÑA DE ESTE ARCHIVO: Lucero Ayala
"""

from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Lima")
except Exception:
    TZ = timezone(timedelta(hours=-5))

PRIORITY_POINTS = {1: 50, 2: 30, 3: 10}
PRIORITY_LABEL = {1: "Alta", 2: "Media", 3: "Baja"}
TIME_FIT_BONUS = 15

def today_local():
    return datetime.now(TZ).date()

def calculate_score(task, available_minutes):
    today = today_local()
    
    priority_level = task.get("priority_level", 2)
    p_prio = PRIORITY_POINTS.get(priority_level, 30)
    label_prio = PRIORITY_LABEL.get(priority_level, "Media")
    razon_prio = f"Prioridad {label_prio}"

    due_date_str = task.get("due_date", str(today))
    if isinstance(due_date_str, str):
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    else:
        due_date = due_date_str

    delta_days = (due_date - today).days

    if delta_days < 0:
        p_urg = 40
        razon_urg = "Vencida"
    elif delta_days == 0:
        p_urg = 40
        razon_urg = "Vence hoy"
    elif delta_days == 1:
        p_urg = 20
        razon_urg = "Vence mañana"
    elif 2 <= delta_days <= 3:
        p_urg = 10
        razon_urg = "Vence en 2-3 días"
    else:
        p_urg = 5
        razon_urg = "Vence en +3 días"

    estimated_minutes = task.get("estimated_minutes", 30)
    if estimated_minutes <= available_minutes:
        p_tiempo = TIME_FIT_BONUS
        razon_tiempo = f"Entra en tus {available_minutes} min disponibles"
    else:
        p_tiempo = 0
        razon_tiempo = f"Supera tus {available_minutes} min disponibles"

    total = p_prio + p_urg + p_tiempo

    breakdown = {
        "prioridad": {"puntos": p_prio, "razon": razon_prio},
        "urgencia": {"puntos": p_urg, "razon": razon_urg},
        "tiempo": {"puntos": p_tiempo, "razon": razon_tiempo},
    }

    return total, breakdown

def rank_tasks(tasks, available_minutes):
    scored = []
    for t in tasks:
        total, breakdown = calculate_score(t, available_minutes)
        item = dict(t)
        item["score"] = total
        item["score_breakdown"] = breakdown
        scored.append(item)
    scored.sort(key=lambda x: (-x["score"], str(x["due_date"]), x.get("id", 0)))
    return scored
```

---

### 1.3 `app.py` (Flask Controller)
```python
"""
VibePlanner - Controlador Flask
--------------------------------------------------
DUEÑA DE ESTE ARCHIVO: Ana Cusi
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
import database
import scoring

app = Flask(__name__)
database.init_db()

DEFAULT_AVAILABLE_MINUTES = 120

@app.teardown_appcontext
def _close_db(exception=None):
    database.close_db(exception)

@app.route("/")
def index_route():
    available = request.args.get("available", DEFAULT_AVAILABLE_MINUTES, type=int)
    tasks = database.get_tasks()
    ranked = scoring.rank_tasks(tasks, available)
    progress = database.get_daily_progress()
    return render_template(
        "index.html",
        tasks=ranked,
        available_minutes=available,
        progress=progress,
    )

@app.route("/tasks", methods=["POST"])
def add_task_route():
    data = {
        "title": request.form.get("title", "").strip(),
        "category": request.form.get("category", "General"),
        "priority_level": request.form.get("priority_level", 2, type=int),
        "due_date": request.form.get("due_date", ""),
        "estimated_minutes": request.form.get("estimated_minutes", 30, type=int),
    }
    database.add_task(data)
    return redirect(url_for("index_route"))

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task_route(task_id):
    database.delete_task(task_id)
    return redirect(url_for("index_route"))

@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_status_route(task_id):
    new_status = request.form.get("status", "pending")
    database.update_status(task_id, new_status)
    return redirect(url_for("index_route"))

@app.route("/api/task/<int:task_id>/score-breakdown")
def score_breakdown_route(task_id):
    available = request.args.get("available", DEFAULT_AVAILABLE_MINUTES, type=int)
    task = database.get_task_by_id(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404
    total, breakdown = scoring.calculate_score(task, available)
    return jsonify({"id": task_id, "total": total, "breakdown": breakdown})

if __name__ == "__main__":
    app.run(debug=True)
```
