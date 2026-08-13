# 📋 VUP Phase 7: Transition Phase Document

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Phase:** Transition Phase (Deployment, Verification & Hand-off)  
**Deployment Platform:** PythonAnywhere (WSGI Linux Hosting)  
**Live URL:** `http://Josed.pythonanywhere.com` / `http://lulu1604.pythonanywhere.com`  

---

## 🌐 1. Deployment Platform Selection

- **Hosting Provider:** `PythonAnywhere` (WSGI Python Web Hosting)
- **Host Environment:** Linux Free Tier, Python 3.10+, WSGI App Server, SQLite3 local storage.
- **Cost Structure:** $0.00 / month (Zero external API dependencies, zero cloud database costs).

---

## 📚 2. Analyze the Generated Code (`codeAnalysis`)

### Key Architecture & Code Learnings:
1. **Model-View-Controller (MVC) Separation:**
   * `database.py`: Encapsulates schema creation, parameterized SQL queries, connection lifecycle (`flask.g`), and status updates.
   * `scoring.py`: Implements a pure, deterministic scoring rule ($Total = P_{Priority} + P_{Urgency} + P_{TimeFit}$) with itemized breakdown dictionaries.
   * `app.py`: Flask web controller routing HTTP endpoints, payload validations, and JSON REST responses.
2. **Defensive Timezone Handling:**
   * Fixed Peru timezone using `ZoneInfo("America/Lima")` with an automatic fallback to `timezone(timedelta(hours=-5))` ensures cross-platform server compatibility without missing dependency crashes.
3. **Security Baseline:**
   * 100% of database queries use parameterized tuple binding (`?`), eliminating SQL Injection vulnerabilities.

---

## 🧪 3. Execute the Test Plan (`testingNotes`)

### Summary of Verification Results:
- **Automated Unit Assertions:** **10/10 Passed (100% Success Rate)**
  * `scoring.py`: 6 automated `assert` tests verifying overdue tasks (+40), due today (+40), time fit bonus (+15), time excess (0 pts), and deterministic tie-breaking by ID.
  * `database.py`: 4 automated `assert` tests verifying CRUD operations and zero-division protection on empty task tables.
- **Manual Test Plan Results:** All 7 test cases from Construction III (`TC-01` through `TC-07`) passed without defects.

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
   * Database `vibe_planner.db` is stored at the root directory (`/home/Josed/vibe-planner/vibe_planner.db`) outside `/static` to prevent unauthorized HTTP file downloads.
   * `database.init_db()` runs automatically on module load to guarantee table schema creation on cold WSGI starts.

---

## 💭 6. Reflection Notes (`reflection`)

### Lessons Learned:
- **Importance of Specification:** Having a precise, frozen numerical scoring formula (Priority: 50/30/10, Urgency: 40/20/10/5, Time Fit: 15) allowed the AI coding assistant to generate clean, bug-free code on the first attempt.
- **Explainability Advantage:** Unlike black-box commercial AI schedulers (e.g., Motion or Reclaim), VibePlanner's audit modal transparently explains why a task was prioritized, building user trust.
- **Modular Team Workflow:** Assigning clear file ownership (Lucero $\rightarrow$ `scoring.py`, Jose $\rightarrow$ `database.py`, Piero/Ana $\rightarrow$ frontend & deployment) eliminated merge conflicts.
