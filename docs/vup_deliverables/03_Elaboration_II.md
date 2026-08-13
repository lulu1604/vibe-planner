# 📋 VUP Phase 3: Elaboration Phase II Document

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Phase:** Elaboration Phase II (Architecture, Playbook & UML Diagrams)  

---

## 🏛️ 1. System Architecture Components

- **Controller Layer:** `FlaskController` (`app.py`) — Receives HTTP requests, validates payload parameters, enforces single-user session boundaries, and routes JSON/HTML responses.
- **View Layer:** `Jinja2 View Layer` (`templates/` & `static/`) — Renders responsive dark-mode HTML templates with CSS Glassmorphism cards, SVG badges, and score breakdown modal dialogs.
- **Security:** `Local Single-User Guard` — Restricts data manipulation strictly to the local SQLite session without requiring external OAuth/Auth0 providers.
- **Data Storage:** `DatabaseManager` (`database.py`) — Handles SQLite3 schema creation, sanitized SQL queries, transaction management, and status persistence.
- **Communications:** `Internal Fetch API` — Asynchronous client-side AJAX requests between `main.js` and Flask REST API endpoints.
- **Algorithms:** `ScoringEngine` (`scoring.py`) — Executes deterministic scoring formula: $Total Score = Priority Weight (10-50) + Urgency Weight (5-40) + Time Fit Bonus (0-15)$.

---

## 🎭 2. Collaboration Plays & Playbook Scenarios

1. **Play 1: Task Creation & Deterministic Ranking Play:**
   * When a student submits a new task form, `FlaskController` validates inputs, `DatabaseManager` inserts the record into SQLite, `ScoringEngine` recalculates total scores for all pending tasks, and the View updates the sorted task list.
2. **Play 2: Explainable Score Inspection Play:**
   * When a student clicks the score badge on a ranked task, Vanilla JS requests `/api/task/<id>/score-breakdown`, `FlaskController` retrieves the task from `DatabaseManager`, `ScoringEngine` builds the itemized point audit, and View opens the explanation modal showing exact point contributions.
3. **Play 3: Status Toggle & Progress Bar Sync Play:**
   * When a student clicks the status checkmark, Fetch API sends a `POST`/`PATCH` request to `/tasks/<id>/status`, `DatabaseManager` updates status in SQLite, and JS recalculates the daily completion percentage, updating the UI progress bar without a full page refresh.

---

## 📊 3. UML Diagrams (Mermaid GFM)

### 3.1 System Class Diagram
```mermaid
classDiagram
    class Task {
        +int id
        +string title
        +string due_date
        +string category
        +int priority_level
        +int estimated_minutes
        +string status
        +float total_score
        +dict score_breakdown
        +to_dict() dict
    }

    class ScoringEngine {
        +dict priority_weights
        +dict urgency_weights
        +calculate_score(Task task, int available_minutes) tuple
        +rank_tasks(Task[] tasks, int available_minutes) Task[]
    }

    class DatabaseManager {
        +string db_path
        +init_db() void
        +get_all_tasks(string status) Task[]
        +get_task_by_id(int id) Task
        +add_task(dict task_data) int
        +update_status(int id, string new_status) bool
        +delete_task(int id) bool
    }

    class FlaskController {
        +index_route() Response
        +add_task_route() Response
        +update_status_route(int id) Response
        +score_breakdown_route(int id) Response
        +delete_task_route(int id) Response
    }

    class ViewLayer {
        +render_dashboard(Task[] ranked_tasks, float progress_pct) HTML
        +render_score_modal(dict breakdown) JSON/HTML
    }

    FlaskController --> DatabaseManager : queries & persists
    FlaskController --> ScoringEngine : invokes for ranking
    FlaskController --> ViewLayer : renders responses
    ScoringEngine --> Task : evaluates & assigns score
    DatabaseManager --> Task : instantiates & stores
```

---

### 3.2 Sequence Diagram 1: Score Audit Modal Inspection
```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Browser)
    participant JS as Vanilla JS (main.js)
    participant FC as FlaskController (app.py)
    participant DB as DatabaseManager (database.py)
    participant SE as ScoringEngine (scoring.py)
    participant View as Score Breakdown Modal

    Student->>JS: Click "Why is this first?" / Score Badge (Task #12)
    JS->>FC: GET /api/task/12/score-breakdown
    FC->>DB: get_task_by_id(12)
    DB-->>FC: Task instance (#12)
    FC->>SE: calculate_score(Task #12, available_minutes)
    SE-->>FC: Total Score (85 pts) & Breakdown (Priority: 50, Urgency: 35, Time Fit: 0)
    FC-->>JS: HTTP 200 OK (JSON Score Breakdown Payload)
    JS->>View: Populate & open Glassmorphism Modal
    View-->>Student: Display itemized point breakdown explaining ranking position
```

---

### 3.3 Sequence Diagram 2: Status Toggle & Progress Bar Sync
```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Browser)
    participant JS as Vanilla JS (main.js)
    participant FC as FlaskController (app.py)
    participant DB as DatabaseManager (database.py)

    Student->>JS: Click Status Checkmark (Mark Task #12 as 'completed')
    JS->>FC: POST /tasks/12/status (status='completed')
    FC->>DB: update_status(12, 'completed')
    DB-->>FC: Success (True)
    FC->>DB: get_daily_progress()
    DB-->>FC: Total Tasks: 4, Completed: 3 (75% Completion Rate)
    FC->>JS: HTTP 200 OK { status: 'completed', completion_pct: 75.0 }
    JS->>JS: Update task card UI & smooth-animate progress bar to 75%
    JS-->>Student: Display updated progress bar without full page reload
```

---

## 🤖 4. AI Critique & Rejected Suggestions

1. **Rejected Suggestion 1: LLM-Based Task Prioritization API Call:**
   - *Reason for Rejection:* AI suggested sending user activity titles to an external Gemini/OpenAI API to generate priority ranks using natural language. This was rejected because it violates the zero-dependency offline requirement and introduces non-deterministic ranking latency.
2. **Rejected Suggestion 2: Complex Client-Side State Management (React/Redux):**
   - *Reason for Rejection:* AI suggested building a single-page app in React. This was rejected to keep the codebase simple and lightweight, using Jinja2 templates and Vanilla JS.
