# 🎤 Official Final Presentation & Defense Guide: VibePlanner

**Course:** Fundamentals of Vibe Coding (ESAN Global Week 2026)  
**Project:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Framework:** Python + Flask + SQLite3  
**Target Duration:** 10 – 13 Minutes  
**Live Application URL:** `http://Josed.pythonanywhere.com`  
**GitHub Repository:** `https://github.com/lulu1604/vibe-planner.git`  

---

## ⏱️ Team Participation & Timing Breakdown (12 Minutes)

| Speaker | Section Covered | Slide # | Time |
|---|---|---|---|
| **Lucero Ayala** | Project Overview & Inception Phase | Slides 1 & 2 | 2.5 min |
| **Jose Cabrera** | Elaboration, Architecture & UML Diagrams | Slide 3 | 2.5 min |
| **Piero Calderon** | Construction & AI Prompt Engineering | Slide 4 | 2.5 min |
| **Ana Cusi** | Testing, Deployment & What We Learned | Slide 5 | 2.0 min |
| **All Team Members** | Live System Demonstration (Demo) | Live Browser | 2.5 min |

---

## 📊 Slide-by-Slide Content & Answers to Instructor Prompt

### 🔹 Slide 1: Project Overview (Speaker: Lucero Ayala)
- **Project Name:** VibePlanner
- **Team Members & Roles:**
  - Lucero Ayala (Scoring Engine Lead & Algorithm Logic)
  - Jose Cabrera (Database Lead, Persistence & Unit Asserts)
  - Piero Calderon (Frontend Lead, Glassmorphism CSS & Fetch API)
  - Ana Cusi (Flask Controller Lead & PythonAnywhere Deployment)
- **Problem Description:** University students lose time experiencing *analysis paralysis* when facing a long, unorganized list of pending daily activities.
- **Target Users:** University students and young professionals who want transparent daily guidance.

---

### 🔹 Slide 2: Inception Phase & User Stories (Speaker: Lucero Ayala)
- **Original Project Idea:** A transparent, explainable daily activity planner running locally with zero external API costs.
- **Problem Solved:** Turning a plain task list into a deterministic daily schedule ordered by priority, urgency, and available time.
- **The 4 Core User Stories:**
  1. *Task CRUD:* Create, edit, and delete activities with title, ISO deadline, category, priority (1-High, 2-Med, 3-Low), and duration.
  2. *Auto-Ranking:* Automatically calculate a deterministic score ($Total = Priority + Urgency + TimeFit$) ordering tasks from highest to lowest.
  3. *Status & Progress:* Toggle task status (`pending`, `in_progress`, `completed`) and display real-time daily completion percentage.
  4. *Explainable Score Audit:* Click any task score badge to open a modal detailing the exact mathematical point breakdown (+50 Priority, +40 Urgency, +15 Time).
- **Requirements Evolution:** We refined the scoring rule from an ambiguous "smart AI priority" to a deterministic point formula to guarantee 100% testability.

---

### 🔹 Slide 3: Elaboration & Architecture (Speaker: Jose Cabrera)
- **System Architecture (MVC Pattern):**
  - **Controller Layer:** `FlaskController` (`app.py`) handling HTTP routes and REST JSON endpoints.
  - **Model Layer:** `DatabaseManager` (`database.py`) providing parameterized SQL CRUD operations.
  - **Domain Engine:** `ScoringEngine` (`scoring.py`) executing scoring formulas and tie-breaking sorting.
  - **View Layer:** Jinja2 HTML templates + CSS Glassmorphism (`static/css/style.css`).
- **UML Class Diagram Highlights:** Demonstrating decoupled contracts between `Task`, `ScoringEngine`, `DatabaseManager`, and `FlaskController`.
- **UML Sequence Diagram Highlights:** Tracing the exact message flow from clicking a task badge $\rightarrow$ Fetch API call to `/api/task/<id>/score-breakdown` $\rightarrow$ JSON payload $\rightarrow$ Modal UI popup.

---

### 🔹 Slide 4: Construction & AI Prompt Engineering (Speaker: Piero Calderon)
- **How AI Was Used:**
  - Used ChatGPT / Gemini to accelerate Jinja2 HTML templating, Glassmorphism CSS design system, and SQLite helper drafts.
- **2 Key Prompts Used (Documented in `docs/prompts/`):**
  1. *Jose's Prompt:* Generating CRUD SQL queries and zero-division protection metrics for `database.py`.
  2. *Lucero's Prompt:* Implementing deterministic scoring formula and breakdown audit dictionaries in `scoring.py`.
- **What AI Generated That Required Human Fixes:**
  - **Issue 1 (Relative File Paths):** AI used `sqlite3.connect("vibe_planner.db")`. On PythonAnywhere WSGI, relative paths fail. Human fix: `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`.
  - **Issue 2 (Timezone Bug):** AI used `datetime.now()` in UTC, marking Peru tasks overdue at 7:00 PM. Human fix: `ZoneInfo("America/Lima")` with safe `timezone(timedelta(hours=-5))` fallback.

---

### 🔹 Slide 5: Testing, Deployment & Reflection (Speaker: Ana Cusi)
- **Testing Strategy:**
  - 10 Automated `assert` tests executed across `scoring.py` (6 tests) and `database.py` (4 tests) verifying overdue scores (+40), time fit (+15), zero division, and ID tie-breaking.
  - 7 Manual Acceptance Test Cases (`TC-01` to `TC-07`) verified.
- **Deployment Details:**
  - Live PythonAnywhere URL: `http://Josed.pythonanywhere.com`
  - GitHub Repository: `https://github.com/lulu1604/vibe-planner.git`
- **What We Learned:**
  - *Harder than expected:* Configuring WSGI server entry points and timezone fallbacks for Linux cloud hosting.
  - *What AI did well:* Rapid HTML/CSS Glassmorphism UI scaffolding and parameterized SQL boilerplate.
  - *What AI did poorly:* Multi-timezone handling and WSGI module entry initialization (`if __name__ == '__main__':` traps).
  - *What we figured out on our own:* Fixing top-level `database.init_db()` execution for cold-start WSGI web servers.

---

## 🖥️ Live Demonstration Script (3 Minutes — All Team Members)

1. **Step 1 (Ana):** Open live browser at `http://Josed.pythonanywhere.com`. Point out the dark-mode Glassmorphism design and empty progress bar (0%).
2. **Step 2 (Piero):** Create a new activity titled *"Exposición Final Vibe Coding"*, due today, Priority High (50 pts), estimated 45 min.
3. **Step 3 (Lucero):** Show that the task automatically moves to **Rank #1** at the top of the daily plan list with a total score badge.
4. **Step 4 (Jose):** Click the score badge **"💡 ¿Por qué este orden?"** to open the Explainable Audit Modal. Show the exact point breakdown: **+50 High Priority**, **+40 Due Today**, **+15 Time Fit**.
5. **Step 5 (Ana):** Mark the task as "Completada" and watch the visual progress bar smoothly update to **100%**.
