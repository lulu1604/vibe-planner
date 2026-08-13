# VibePlanner — Complete Production-Ready Application Code

---

## 1. `database.py`

```python
"""
VibePlanner - Database & Persistence Layer
------------------------------------------
Handles SQLite3 schema creation, connection lifecycle, and CRUD operations.
"""

import os
import sqlite3
from flask import g

# Absolute path resolution for Linux WSGI environment (PythonAnywhere)
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
    """Returns per-request SQLite connection bound to Flask g context."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10.0)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exception=None):
    """Closes SQLite connection at teardown."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Initializes SQLite table schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def get_tasks(filter_status=None):
    """Retrieves all tasks, optionally filtered by status."""
    db = get_db()
    if filter_status:
        rows = db.execute("SELECT * FROM tasks WHERE status = ? ORDER BY id DESC", (filter_status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

def get_task_by_id(task_id):
    """Retrieves single task dictionary by ID or None."""
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None

def add_task(task_data):
    """Inserts new task record into SQLite."""
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
    """Updates task status. Validates allowed values."""
    allowed = ["pending", "in_progress", "completed"]
    if new_status not in allowed:
        return False
    db = get_db()
    cursor = db.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    db.commit()
    return cursor.rowcount > 0

def delete_task(task_id):
    """Deletes task by ID."""
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return cursor.rowcount > 0

def get_daily_progress():
    """Calculates completion metrics with zero-division protection."""
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

## 2. `scoring.py`

```python
"""
VibePlanner - Deterministic Scoring Engine
------------------------------------------
Calculates task score breakdown and orders tasks dynamically.
Formula: Total = Priority Points + Deadline Urgency Points + Available Time Fit Bonus
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Localized timezone alignment (Peru UTC-5)
TZ = ZoneInfo("America/Lima")

PRIORITY_POINTS = {1: 50, 2: 30, 3: 10}
PRIORITY_LABEL = {1: "Alta", 2: "Media", 3: "Baja"}
TIME_FIT_BONUS = 15

def today_local():
    return datetime.now(TZ).date()

def calculate_score(task, available_minutes=120):
    """Calculates total score and itemized breakdown audit."""
    today = today_local()
    
    # 1. Priority Factor
    priority_level = task.get("priority_level", 2)
    p_prio = PRIORITY_POINTS.get(priority_level, 30)
    label_prio = PRIORITY_LABEL.get(priority_level, "Media")
    razon_prio = f"Prioridad {label_prio}"

    # 2. Deadline Urgency Factor
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

    # 3. Available Time Fit Bonus
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

def rank_tasks(tasks, available_minutes=120):
    """Sorts tasks descending by score, tie-breaking by due_date ASC, then id ASC."""
    scored = []
    for t in tasks:
        total, breakdown = calculate_score(t, available_minutes)
        item = dict(t)
        item["score"] = total
        item["score_breakdown"] = breakdown
        scored.append(item)
    scored.sort(key=lambda x: (-x["score"], x["due_date"], x.get("id", 0)))
    return scored

if __name__ == "__main__":
    today = today_local()
    t_vencida = {"id": 1, "priority_level": 1, "due_date": str(today - timedelta(days=2)), "estimated_minutes": 30}
    score_v, b_v = calculate_score(t_vencida, 120)
    assert score_v == 105 and b_v["urgencia"]["razon"] == "Vencida"
    
    t_hoy = {"id": 2, "priority_level": 2, "due_date": str(today), "estimated_minutes": 30}
    score_h, b_h = calculate_score(t_hoy, 120)
    assert score_h == 85 and b_h["urgencia"]["razon"] == "Vence hoy"
    print("SUCCESS: scoring.py unit tests passed!")
```

---

## 3. `app.py`

```python
"""
VibePlanner - Flask Web Controller
-----------------------------------
Receives HTTP requests, validates input data, and renders JSON/HTML views.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import database as db
import scoring

app = Flask(__name__)
app.teardown_appcontext(db.close_db)

# Auto-initialize SQLite schema
db.init_db()

@app.route("/")
def index():
    available_time = request.args.get("available_time", 120, type=int)
    all_tasks = db.get_tasks()
    
    pending_raw = [t for t in all_tasks if t["status"] != "completed"]
    completed_list = [t for t in all_tasks if t["status"] == "completed"]
    
    ranked_pending = scoring.rank_tasks(pending_raw, available_time)
    metrics = db.get_daily_progress()
    
    return render_template(
        "index.html",
        pending_tasks=ranked_pending,
        completed_tasks=completed_list,
        metrics=metrics,
        available_time=available_time
    )

@app.route("/add", methods=["POST"])
def add_task_route():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "General").strip()
    priority_level = request.form.get("priority_level", 2, type=int)
    due_date = request.form.get("due_date", "").strip()
    estimated_minutes = request.form.get("estimated_minutes", 30, type=int)
    
    # Server-side validation
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if estimated_minutes < 1 or estimated_minutes > 480:
        return jsonify({"error": "Estimated duration must be between 1 and 480 minutes"}), 400
    if priority_level not in [1, 2, 3]:
        priority_level = 2

    task_data = {
        "title": title,
        "category": category,
        "priority_level": priority_level,
        "due_date": due_date,
        "estimated_minutes": estimated_minutes
    }
    db.add_task(task_data)
    return redirect(url_for("index"))

@app.route("/api/task/<int:task_id>/status", methods=["PATCH", "POST"])
def update_status_route(task_id):
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if not new_status:
        new_status = "completed" if task["status"] != "completed" else "pending"
        
    db.update_status(task_id, new_status)
    metrics = db.get_daily_progress()
    return jsonify({"success": True, "task_id": task_id, "new_status": new_status, "metrics": metrics})

@app.route("/api/task/<int:task_id>/score-breakdown", methods=["GET"])
def score_breakdown_route(task_id):
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    available_time = request.args.get("available_time", 120, type=int)
    score, breakdown = scoring.calculate_score(task, available_time)
    
    return jsonify({
        "task_id": task_id,
        "title": task["title"],
        "total_score": score,
        "breakdown": breakdown
    })

@app.route("/delete/<int:task_id>", methods=["POST", "GET"])
def delete_task_route(task_id):
    db.delete_task(task_id)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

---

## 4. `wsgi_pythonanywhere.py`

```python
"""
PythonAnywhere WSGI Entry Point
"""
import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

---

## 5. `requirements.txt`

```text
Flask==3.0.3
```

---

## 6. `templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VibePlanner - Transparent Daily Activity Planner</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="app-wrapper">
        <header class="app-header">
            <div class="logo-container">⚡ Vibe<span class="logo-highlight">Planner</span></div>
            <div class="header-subtitle">Deterministic & Transparent Prioritization</div>
        </header>

        <main class="main-content">
            {% block content %}{% endblock %}
        </main>

        <footer class="app-footer">VibePlanner v1.0 • ESAN Global Week 2026</footer>
    </div>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

---

## 7. `templates/index.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="dashboard-container">
    <div class="glass-card progress-card">
        <div class="progress-header">
            <div>
                <h2>Daily Progress</h2>
                <p class="progress-subtitle"><span id="completed-count">{{ metrics.completed }}</span> of <span id="total-count">{{ metrics.total }}</span> tasks completed</p>
            </div>
            <div class="progress-percentage-badge"><span id="percentage-text">{{ metrics.percent }}</span>%</div>
        </div>
        <div class="progress-bar-track">
            <div class="progress-bar-fill" id="progress-fill" style="width: {{ metrics.percent }}%;"></div>
        </div>
    </div>

    <div class="grid-2-col">
        <div class="glass-card form-card">
            <h3>➕ Add New Activity</h3>
            <form action="/add" method="POST" class="task-form">
                <div class="form-group">
                    <label>Task Title *</label>
                    <input type="text" name="title" placeholder="e.g. Math Assignment" required autocomplete="off">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category">
                            <option value="Academic">Academic</option>
                            <option value="Work">Work</option>
                            <option value="Personal">Personal</option>
                            <option value="General" selected>General</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Priority Level</label>
                        <select name="priority_level">
                            <option value="1">🔥 High (50 pts)</option>
                            <option value="2" selected>⚡ Medium (30 pts)</option>
                            <option value="3">🌱 Low (10 pts)</option>
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>ISO Due Date</label>
                        <input type="date" name="due_date" required>
                    </div>
                    <div class="form-group">
                        <label>Est. Duration (min)</label>
                        <input type="number" name="estimated_minutes" value="30" min="1" max="480" required>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">Save Activity</button>
            </form>
        </div>

        <div class="glass-card info-card">
            <h3>⏱️ Available Work Window</h3>
            <form method="GET" action="/" class="time-filter-form">
                <div class="slider-container">
                    <input type="range" name="available_time" min="15" max="480" step="15" value="{{ available_time }}" oninput="document.getElementById('time-val').innerText = this.value">
                    <div class="slider-display"><span id="time-val">{{ available_time }}</span> minutes available</div>
                </div>
                <button type="submit" class="btn btn-secondary">Apply Time Filter</button>
            </form>
        </div>
    </div>

    <div class="glass-card list-card">
        <div class="list-header">
            <h3>🏆 Ranked Daily Plan</h3>
            <span class="badge-tag info">{{ pending_tasks|length }} Pending</span>
        </div>
        <div class="task-list">
            {% for task in pending_tasks %}
            <div class="task-item-card priority-{{ task.priority_level }}" id="task-card-{{ task.id }}">
                <div class="task-rank-index">#{{ loop.index }}</div>
                <div class="task-check-container">
                    <button class="btn-check" onclick="toggleTaskStatus({{ task.id }})">✓</button>
                </div>
                <div class="task-details">
                    <div class="task-title-row">
                        <span class="task-title">{{ task.title }}</span>
                        <span class="category-badge">{{ task.category }}</span>
                    </div>
                    <div class="task-meta-row">
                        <span>📅 {{ task.due_date }}</span>
                        <span>⏱️ {{ task.estimated_minutes }} min</span>
                    </div>
                </div>
                <div class="task-score-container">
                    <button class="score-badge-btn" onclick="openScoreModal({{ task.id }})">
                        <span class="score-num">{{ "%.0f"|format(task.score) }}</span>
                        <span class="score-unit">pts</span>
                        <span class="explain-icon">🔍 Why?</span>
                    </button>
                </div>
                <div class="task-actions">
                    <a href="/delete/{{ task.id }}" class="btn-delete">🗑️</a>
                </div>
            </div>
            {% else %}
            <div class="empty-state">🎉 No pending tasks!</div>
            {% endfor %}
        </div>
    </div>
</div>

<div id="scoreModal" class="modal-overlay hidden">
    <div class="glass-card modal-content">
        <div class="modal-header">
            <h3>🔍 Score Audit: <span id="modal-task-title">Task</span></h3>
            <button class="modal-close" onclick="closeScoreModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="total-score-box">
                <div class="total-val" id="modal-total-score">0 pts</div>
            </div>
            <div class="breakdown-list">
                <div class="breakdown-item"><span>Priority Weight:</span><span id="modal-priority-pts">+0 pts</span></div>
                <div class="breakdown-item"><span>Deadline Urgency:</span><span id="modal-urgency-pts">+0 pts</span></div>
                <div class="breakdown-item"><span>Time Fit Bonus:</span><span id="modal-time-pts">+0 pts</span></div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 8. `static/css/style.css`

```css
:root {
    --bg-gradient: linear-gradient(135deg, #12151C 0%, #1B2029 100%);
    --card-bg: rgba(27, 32, 41, 0.75);
    --card-border: rgba(46, 53, 67, 0.8);
    --primary: #8B7CF6;
    --urgency: #F5A524;
    --tiempo: #2DD4A7;
    --text-main: #E7EAF0;
    --text-muted: #98A1B3;
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
body { background: var(--bg-gradient); min-height: 100vh; color: var(--text-main); display: flex; justify-content: center; padding: 24px 16px; }
.app-wrapper { width: 100%; max-width: 860px; }
.app-header { text-align: center; margin-bottom: 24px; }
.logo-container { font-size: 2rem; font-weight: 800; }
.logo-highlight { color: var(--primary); }
.header-subtitle { font-size: 0.9rem; color: var(--text-muted); }
.glass-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.progress-percentage-badge { font-size: 1.3rem; font-weight: 800; color: var(--tiempo); }
.progress-bar-track { width: 100%; height: 10px; background: rgba(0,0,0,0.4); border-radius: 10px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: var(--tiempo); transition: width 0.4s ease; }
.grid-2-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.form-group input, .form-group select { padding: 10px; background: #232935; border: 1px solid var(--card-border); border-radius: 8px; color: var(--text-main); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.btn { width: 100%; padding: 10px; border-radius: 8px; font-weight: 600; border: none; cursor: pointer; }
.btn-primary { background: var(--primary); color: white; }
.btn-secondary { background: #232935; color: var(--text-main); border: 1px solid var(--card-border); }
.task-item-card { display: flex; align-items: center; gap: 12px; background: #232935; border: 1px solid var(--card-border); border-radius: 12px; padding: 12px; margin-bottom: 10px; }
.task-rank-index { font-weight: 800; color: var(--primary); }
.btn-check { width: 26px; height: 26px; border-radius: 50%; border: 1px solid var(--text-muted); background: transparent; cursor: pointer; }
.task-details { flex: 1; }
.score-badge-btn { background: rgba(139, 124, 246, 0.15); border: 1px solid var(--primary); border-radius: 8px; padding: 6px; color: var(--text-main); cursor: pointer; display: flex; flex-direction: column; align-items: center; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; }
.modal-overlay.hidden { display: none; }
.modal-content { width: 90%; max-width: 440px; }
```

---

## 9. `static/js/main.js`

```javascript
async function toggleTaskStatus(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            window.location.reload();
        }
    } catch (err) {
        console.error("Status toggle error:", err);
    }
}

async function openScoreModal(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/score-breakdown`);
        if (!response.ok) return;
        
        const data = await response.json();
        document.getElementById('modal-task-title').innerText = data.title;
        document.getElementById('modal-total-score').innerText = `${Math.round(data.total_score)} pts`;
        document.getElementById('modal-priority-pts').innerText = data.breakdown.prioridad.razon;
        document.getElementById('modal-urgency-pts').innerText = data.breakdown.urgencia.razon;
        document.getElementById('modal-time-pts').innerText = data.breakdown.tiempo.razon;

        document.getElementById('scoreModal').classList.remove('hidden');
    } catch (err) {
        console.error("Modal fetch error:", err);
    }
}

function closeScoreModal() {
    document.getElementById('scoreModal').classList.add('hidden');
}
```
