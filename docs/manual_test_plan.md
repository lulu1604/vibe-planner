# Manual Test Plan: VibePlanner

## 1. Manual Test Cases Checklist

- [ ] **TC-01: Successful Task Creation**
  - **Prerequisites:** Navigate to the VibePlanner main dashboard with zero active tasks.
  - **Steps:**
    1. Fill out the "Add New Activity" form.
    2. Enter Title: "Math Assignment".
    3. Select Category: "Academic".
    4. Select Priority Level: "High (50 pts)".
    5. Enter ISO Due Date: "2026-08-15".
    6. Enter Est. Duration: "45".
    7. Click the "Save Activity" button.
  - **Expected:** The form submits successfully, the record is stored in SQLite, and "Math Assignment" appears in the active task list with status "pending".
  - **Criteria:** Task card is rendered with correct badges, duration, and priority level without errors.

- [ ] **TC-02: Invalid Form Input Rejection**
  - **Prerequisites:** Open the main dashboard task creation form.
  - **Steps:**
    1. Leave the Task Title field completely empty.
    2. Enter Est. Duration: "-10".
    3. Click the "Save Activity" button.
  - **Expected:** Form submission is rejected by browser/server validation, no record is created in SQLite, and an error message is displayed.
  - **Criteria:** No database entry is inserted, and an inline error alert or browser validation prompt highlights the invalid input fields.

- [ ] **TC-03: Task Deletion**
  - **Prerequisites:** An existing task titled "Old Task" is displayed in the active task list.
  - **Steps:**
    1. Locate the "Old Task" card in the ranked plan list.
    2. Click the trash icon ("Delete") button on the card.
    3. Confirm deletion if prompted.
  - **Expected:** The task record is removed from SQLite and disappears from the UI dashboard list.
  - **Criteria:** Refreshing the page verifies that "Old Task" no longer exists in the database.

- [ ] **TC-04: Deterministic Auto-Ranking and Tie-Breaking**
  - **Prerequisites:** Create 3 pending tasks with known parameters: Task A (Score 85), Task B (Score 90), and Task C (Score 85, created after Task A).
  - **Steps:**
    1. Observe the ordered position of Task A, Task B, and Task C on the main dashboard.
    2. Verify the descending order of calculated total points.
  - **Expected:** Task B (90 pts) is placed 1st. Task A (85 pts) is placed 2nd. Task C (85 pts) is placed 3rd due to oldest-creation tie-breaking.
  - **Criteria:** The task list orders strictly as Task B $\rightarrow$ Task A $\rightarrow$ Task C without manual sorting.

- [ ] **TC-05: Dynamic Status Toggle and Progress Bar Recalculation**
  - **Prerequisites:** Have 4 total tasks on the dashboard with 2 marked as "completed" (50% progress bar display).
  - **Steps:**
    1. Locate 1 active pending task card.
    2. Click the checkmark status button on the card.
  - **Expected:** The task status updates to "completed" in SQLite, the completion count updates to 3 of 4, and the progress bar smoothly updates to 75%.
  - **Criteria:** The progress bar element width updates to 75% and completed task count shows 3/4.

- [ ] **TC-06: Score Audit Modal Inspection**
  - **Prerequisites:** Task A is ranked #1 on the list with a total calculated score of 90 points (Priority: 50, Urgency: 40, Time Fit: 0).
  - **Steps:**
    1. Click the "90 pts / Why?" score badge button on Task A's card.
    2. Inspect the contents of the opened modal window.
    3. Click the "Close" button or press the Escape key.
  - **Expected:** A score explanation modal dialog opens displaying the itemized breakdown: "+50 High Priority", "+40 Due Today/Overdue", and "+0 Time Fit".
  - **Criteria:** The sum of modal breakdown points matches 90 pts, and closing the modal returns focus to the dashboard.

- [ ] **TC-07: Available Time Window Filter Re-scoring**
  - **Prerequisites:** A task with estimated duration of 60 minutes exists on the dashboard.
  - **Steps:**
    1. Adjust the Available Work Window slider from 30 minutes to 120 minutes.
    2. Click "Apply Time Filter".
  - **Expected:** The system recalculates total scores, awarding the +15 Time Fit bonus to the 60-minute task.
  - **Criteria:** Total score for the task increases by 15 points and its rank updates accordingly.
