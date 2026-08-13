# 📋 VUP Phase 2: Elaboration Phase I Document

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Phase:** Elaboration Phase I (SMART User Stories & Acceptance Criteria)  

---

## 🎯 SMART User Stories & Given-When-Then Test Cases

### 🔹 SMART User Story 1 (Task Lifecycle Management)
**As a** student, **I want to** create, edit, and delete activities with a valid title, ISO deadline date, category, priority level (1-High, 2-Medium, 3-Low), and estimated duration (1-480 min), **so that** I can maintain an accurate list of all my pending commitments in one self-contained interface.

#### Acceptance Test Cases (Given-When-Then):
- **Test Case 1.1 (Valid Task Creation):**
  - **Given** I am on the main dashboard and have zero tasks,
  - **When** I submit a task with title "Math Assignment", due_date "2026-08-15", priority 1, category "Academic", and estimated_minutes 45,
  - **Then** the task is saved to SQLite, assigned status "pending", and displayed in the active list.
- **Test Case 1.2 (Invalid Input Rejection):**
  - **Given** I am filling out the new task form,
  - **When** I submit the form with an empty title OR estimated_minutes = -10,
  - **Then** the form submission is rejected, no SQLite record is created, and an inline error message is displayed.
- **Test Case 1.3 (Task Deletion):**
  - **Given** a task with title "Old Task" exists in the database,
  - **When** I click the "Delete" button and confirm,
  - **Then** the record is removed from SQLite and smoothly animated off the UI list.

---

### 🔹 SMART User Story 2 (Deterministic Auto-Ranking)
**As a** student, **I want** the system to calculate a deterministic total score for each active task based on deadline urgency, priority level, and available time fit, **so that** my daily tasks are automatically ordered from highest to lowest priority without manual sorting.

#### Acceptance Test Cases (Given-When-Then):
- **Test Case 2.1 (Deterministic Sorting & Tie-Breaking):**
  - **Given** I have 3 pending tasks: Task A (Score: 85), Task B (Score: 90), and Task C (Score: 85, created after Task A),
  - **When** the daily planner list renders,
  - **Then** Task B is placed 1st (90 pts), Task A is placed 2nd (85 pts, tie-breaker: oldest creation ID first), and Task C is placed 3rd.

---

### 🔹 SMART User Story 3 (Status & Progress Metrics)
**As a** student, **I want to** toggle task status between "pending", "in_progress", and "completed", **so that** the dashboard recalculates and displays my daily completion percentage in real time.

#### Acceptance Test Cases (Given-When-Then):
- **Test Case 3.1 (Dynamic Completion Progress):**
  - **Given** I have 4 total tasks for today with 2 marked as "completed" (50% progress),
  - **When** I mark 1 additional task as "completed",
  - **Then** the task status updates in SQLite, and the progress bar smoothly updates to 75%.

---

### 🔹 SMART User Story 4 (Transparent Score Audit Modal)
**As a** student, **I want to** click any task's score badge to open a modal detailing the exact mathematical point breakdown (Priority + Urgency + Time Fit), **so that** I can inspect and verify the reasoning behind its position in the list.

#### Acceptance Test Cases (Given-When-Then):
- **Test Case 4.1 (Score Breakdown Audit Inspection):**
  - **Given** Task A is ranked #1 with a total score of 90 points (Priority: 50, Urgency: 40, Time Fit: 0),
  - **When** I click the "90 pts" badge on Task A,
  - **Then** an explainability modal opens showing the itemized breakdown: "+50 High Priority", "+40 Due Today/Overdue", and "+0 Time Fit".
