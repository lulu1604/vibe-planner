# 🚀 Transition Phase Document: VibePlanner

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Phase:** Transition Phase (Vibe Unified Process - VUP)  
**Deployment Target:** PythonAnywhere WSGI Free-Tier  
**Live URL:** `http://Josed.pythonanywhere.com` / `http://lulu1604.pythonanywhere.com`  

---

## 🌐 1. Deployment Platform

- **Platform Selected:** `PythonAnywhere` (WSGI Python Web Hosting)
- **Host Specifications:** Linux Free Tier, Python 3.10+, WSGI App Server, SQLite3 local storage.
- **Cost:** $0.00 / month (Zero external API dependencies, zero cloud database costs).

---

## 📚 2. Analyze the Generated Code (`codeAnalysis`)

### Code Architecture & Design Patterns:
- **Model-View-Controller (MVC) Pattern:**
  - `database.py` (Model): Handles SQLite schema, parameterized SQL queries, connection lifecycle (`flask.g`), and status updates.
  - `scoring.py` (Domain Engine): Implements a pure, deterministic scoring rule ($Total = P_{Priority} + P_{Urgency} + P_{TimeFit}$) with itemized breakdown dictionaries.
  - `app.py` (Controller): Flask web server routing HTTP endpoints, payload validations, and JSON REST responses.
  - `templates/` & `static/` (View): Jinja2 HTML layout with dark-mode Glassmorphism theme and Vanilla JS Fetch API handlers.
- **Key Code Insights Learned:**
  - **Determinism:** Separating algorithm logic (`scoring.py`) from HTTP handling makes the system 100% testable via standard `assert` statements.
  - **Defensive Timezone Handling:** Fixed Peru timezone using `ZoneInfo("America/Lima")` with an automatic fallback to `timezone(timedelta(hours=-5))` ensures cross-platform server compatibility without missing dependency crashes.
  - **SQL Injection Prevention:** 100% of database queries use parameterized tuple binding (`?`), eliminating injection vulnerabilities.

---

## 🧪 3. Execute the Test Plan (`testingNotes`)

### Summary of Test Results:
- **Unit Assertion Suite:** **10/10 Passed (100% Success Rate)**
  - `scoring.py`: 6 automated `assert` tests verifying overdue tasks (+40), due today (+40), time fit bonus (+15), time excess (0 pts), and deterministic tie-breaking by ID.
  - `database.py`: 4 automated `assert` tests verifying CRUD operations and zero-division protection on empty task tables.
- **Manual Test Execution (Construction III Plan):**
  - `TC-01 (Task Creation)`: **PASS** — Task saved to SQLite and rendered on UI.
  - `TC-02 (Invalid Form Input)`: **PASS** — Empty titles and negative durations rejected.
  - `TC-03 (Task Deletion)`: **PASS** — Task record removed from SQLite.
  - `TC-04 (Auto-Ranking & Tie-Breaker)`: **PASS** — Task B (90 pts) placed before Task A (85 pts).
  - `TC-05 (Status & Progress Bar)`: **PASS** — Completion count and progress bar update dynamically.
  - `TC-06 (Score Audit Modal)`: **PASS** — Modal displays "+50 Priority", "+40 Urgency", "+15 Time Fit".
  - `TC-07 (Available Time Slider)`: **PASS** — Re-evaluates time fit bonus dynamically.

---

## 🚀 4. Live Deployment URL (`deploymentUrl`)

```text
http://Josed.pythonanywhere.com
http://lulu1604.pythonanywhere.com
```

---

## ⚙️ 5. Deployment Configuration & Instructions (`deploymentInstructions`)

1. **Repository Setup in PythonAnywhere:**
   ```bash
   git clone https://github.com/lulu1604/vibe-planner.git
   cd ~/vibe-planner
   pip install --user Flask
   python3 -c "import database; database.init_db()"
   ```
2. **WSGI Configuration File (`/var/www/josed_pythonanywhere_com_wsgi.py`):**
   ```python
   import sys
   path = '/home/Josed/vibe-planner'
   if path not in sys.path:
       sys.path.append(path)

   from app import app as application
   ```
3. **Database & Environment Rules:**
   - Database `vibe_planner.db` is stored at the root directory (`/home/Josed/vibe-planner/vibe_planner.db`) outside `/static` to prevent unauthorized HTTP file downloads.
   - `database.init_db()` runs automatically on module load to guarantee table schema creation on cold WSGI starts.

---

## 💭 6. Reflect on What You Built (`reflection`)

### Process & Technical Reflections:
- **Importance of Specification:** Having a clear, frozen scoring formula ($50 / 30 / 10$ priority, $40 / 20 / 10 / 5$ urgency, $+15$ time fit) eliminated ambiguity. The AI coding assistant generated exact, bug-free implementation code matching the VUP blueprint on the first attempt.
- **Explainability vs. Black-Box AI:** Unlike commercial AI schedulers (e.g., Motion, Reclaim) that rank activities as black boxes, VibePlanner's transparent audit modal gives students 100% confidence in why a task was prioritized first.
- **Team Collaboration & Git Workflow:** Assigning clear module ownership (Lucero $\rightarrow$ Scoring, Jose $\rightarrow$ Database, Piero $\rightarrow$ View, Ana $\rightarrow$ Deployment) prevented merge conflicts and enabled parallel development with AI assistance.
- **Future Enhancements:** In future iterations, adding multi-user authentication (`user_id` column) and Google Calendar sync ($2/mo freemium) would expand the product into a commercial SaaS product.
