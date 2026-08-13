"""
VibePlanner - Controlador Flask
--------------------------------------------------
DUEÑO DE ESTE ARCHIVO: Ana (rutas y despliegue)

REGLA CRÍTICA: la instancia de Flask se llama EXACTAMENTE `app` y está definida
a nivel de módulo. PythonAnywhere hace `from app import app`. No usar
application factory, no renombrar a `application`.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify

import database
import scoring

app = Flask(__name__)          # <-- NO TOCAR ESTA LÍNEA

# Inicializar esquema SQLite automáticamente al cargar el módulo WSGI
database.init_db()

# Tiempo disponible por defecto (minutos). US2/US4 lo usan para el bono de tiempo.
DEFAULT_AVAILABLE_MINUTES = 120


@app.teardown_appcontext
def _close_db(exception=None):
    database.close_db(exception)


# --------------------------------------------------------------------------
# US2 - Ver el plan del día ordenado
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# US1 - Crear / editar / eliminar actividades
# --------------------------------------------------------------------------
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


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])   # POST, nunca GET
def delete_task_route(task_id):
    database.delete_task(task_id)
    return redirect(url_for("index_route"))


# --------------------------------------------------------------------------
# US3 - Cambiar estado y ver progreso
# --------------------------------------------------------------------------
@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_status_route(task_id):
    new_status = request.form.get("status", "pending")
    database.update_status(task_id, new_status)
    return redirect(url_for("index_route"))


# --------------------------------------------------------------------------
# US4 - Explicabilidad: desglose del puntaje
# --------------------------------------------------------------------------
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
