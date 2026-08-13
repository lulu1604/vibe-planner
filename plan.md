# Project Blueprint: VibePlanner

## 1. Project Structure

- `app.py`
- `scoring.py`
- `database.py`
- `requirements.txt`
- `wsgi_pythonanywhere.py`
- `templates/`
  - `templates/base.html`
  - `templates/index.html`
  - `templates/score_modal.html`
- `static/`
  - `static/css/style.css`
  - `static/js/main.js`
- `docs/`
  - `docs/prompts/`

## 2. Implementation Checklist

- [ ] Set up project repository and Python virtual environment
- [ ] Implement SQLite schema initialization and CRUD helper contracts in `database.py`
- [ ] Implement deterministic scoring algorithm and itemized breakdown logic in `scoring.py`
- [ ] Implement Flask HTTP routes, payload validation, and REST API endpoints in `app.py`
- [ ] Create Jinja2 HTML layout templates for dashboard and modal dialog in `templates/`
- [ ] Style user interface with dark-mode Glassmorphism theme in `static/css/style.css`
- [ ] Add asynchronous Fetch API client-side interactions in `static/js/main.js`
- [ ] Execute unit test assertion suite for scoring and database modules
- [ ] Deploy web application to PythonAnywhere WSGI environment

## 3. User Story Mapping

- **Story 1 (Task CRUD):**
  - `database.py` (SQL insert, select, delete operations)
  - `app.py` (Form submission routes `/add` and `/delete/<id>`)
  - `templates/index.html` (Creation form and active task list UI)
- **Story 2 (Auto-Ranking):**
  - `scoring.py` (Priority, Urgency, and Time Fit scoring rules)
  - `app.py` (Sorts pending tasks before rendering dashboard)
  - `templates/index.html` (Displays ranked list descending by total score)
- **Story 3 (Status & Progress):**
  - `database.py` (SQL status update and completion progress metrics)
  - `app.py` (REST endpoint `/api/task/<id>/status`)
  - `static/js/main.js` (Asynchronous status toggle AJAX request)
  - `templates/index.html` (Progress bar and completion count badges)
- **Story 4 (Score Audit Breakdown):**
  - `scoring.py` (Itemized score breakdown dictionary generator)
  - `app.py` (REST endpoint `/api/task/<id>/score-breakdown`)
  - `static/js/main.js` (Fetch request and modal dialog handler)
  - `templates/score_modal.html` (Score explanation audit modal)

## 4. Development Phases

- **Phase 1: Environment & Persistence Setup (Milestone 1)**
  - Initialize project directory, virtual environment, and SQLite table schema in `database.py`.
- **Phase 2: Core Algorithm Engine (Milestone 2)**
  - Build deterministic scoring rules and breakdown generator in `scoring.py`.
- **Phase 3: Controller & REST Routing (Milestone 3)**
  - Wire Flask routes, payload validators, and JSON API endpoints in `app.py`.
- **Phase 4: View Layer & UI Design (Milestone 4)**
  - Build Jinja2 HTML templates, CSS Glassmorphism styling, and Vanilla JS Fetch handlers.
- **Phase 5: Verification & Production Deployment (Milestone 5)**
  - Run unit test assertion suite and deploy application to PythonAnywhere server.

## 5. Dependencies

1. **`database.py` (Persistence Layer)** — Must be built first to establish SQL schema and data contracts.
2. **`scoring.py` (Scoring Engine)** — Depends on task dictionary structures defined by database layer.
3. **`app.py` (Flask Controller)** — Depends on `database.py` and `scoring.py` to route requests.
4. **`templates/` & `static/` (View Layer)** — Depends on controller endpoints and JSON contracts.
5. **`wsgi_pythonanywhere.py` (Deployment)** — Depends on complete application structure.
