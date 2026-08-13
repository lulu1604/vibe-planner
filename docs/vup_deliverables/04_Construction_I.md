# 📋 VUP Phase 4: Construction Phase I Document

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Phase:** Construction Phase I (Project Blueprint & Task Mapping)  

---

## 🏗️ 1. Project Structure

- `app.py` — Main Flask Controller and REST endpoints.
- `scoring.py` — Deterministic scoring engine and score breakdown audit generator.
- `database.py` — SQLite table initialization and CRUD helper contracts.
- `requirements.txt` — Frozen dependencies (`Flask==3.0.3`).
- `wsgi_pythonanywhere.py` — Production WSGI server entry point.
- `templates/` — Jinja2 HTML layout templates (`base.html`, `index.html`, `score_modal.html`).
- `static/` — Static assets (`static/css/style.css`, `static/js/main.js`).
- `docs/` — VUP documentation and AI prompt evidence files.

---

## ✅ 2. Implementation Checklist

- [x] Set up project repository and Python virtual environment.
- [x] Implement SQLite schema initialization and CRUD helper contracts in `database.py`.
- [x] Implement deterministic scoring algorithm and itemized breakdown logic in `scoring.py`.
- [x] Implement Flask HTTP routes, payload validation, and REST API endpoints in `app.py`.
- [x] Create Jinja2 HTML layout templates for dashboard and modal dialog in `templates/`.
- [x] Style user interface with dark-mode Glassmorphism theme and official palette in `static/css/style.css`.
- [x] Add asynchronous Fetch API client-side interactions in `static/js/main.js`.
- [x] Execute unit test assertion suite for scoring and database modules (10/10 passed).
- [x] Deploy web application to PythonAnywhere WSGI environment (`http://Josed.pythonanywhere.com`).

---

## 🗺️ 3. User Story Mapping

| User Story | Responsible File / Module | Interface / Endpoint |
|---|---|---|
| **Story 1 (Task CRUD)** | `database.py`, `app.py`, `index.html` | `POST /tasks`, `POST /tasks/<id>/delete` |
| **Story 2 (Auto-Ranking)** | `scoring.py`, `app.py`, `index.html` | `GET /` (Sorts pending tasks by total score) |
| **Story 3 (Status & Progress)** | `database.py`, `app.py`, `main.js` | `POST /tasks/<id>/status` |
| **Story 4 (Score Breakdown)** | `scoring.py`, `app.py`, `score_modal.html` | `GET /api/task/<id>/score-breakdown` |

---

## 🗓️ 4. Development Phases & Milestones

- **Phase 1: Environment & Persistence Setup (Milestone 1)**  
  Initialize project directory, virtual environment, and SQLite table schema in `database.py`.
- **Phase 2: Core Algorithm Engine (Milestone 2)**  
  Build deterministic scoring rules and breakdown generator in `scoring.py`.
- **Phase 3: Controller & REST Routing (Milestone 3)**  
  Wire Flask routes, payload validators, and JSON API endpoints in `app.py`.
- **Phase 4: View Layer & UI Design (Milestone 4)**  
  Build Jinja2 HTML templates, CSS Glassmorphism styling, and Vanilla JS Fetch handlers.
- **Phase 5: Verification & Production Deployment (Milestone 5)**  
  Run unit test assertion suite and deploy application to PythonAnywhere server.

---

## 🔗 5. Module Dependency Order

1. **`database.py` (Persistence Layer)** — Built first to establish SQL schema and data contracts.
2. **`scoring.py` (Scoring Engine)** — Depends on task dictionary structures defined by database layer.
3. **`app.py` (Flask Controller)** — Depends on `database.py` and `scoring.py` to route requests.
4. **`templates/` & `static/` (View Layer)** — Depends on controller endpoints and JSON contracts.
5. **`wsgi_pythonanywhere.py` (Deployment)** — Depends on complete application structure.
