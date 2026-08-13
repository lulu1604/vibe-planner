# 📋 VUP Phase 1: Inception Document

**Project Name:** VibePlanner — Daily Activity Planner with Transparent Prioritization  
**Framework:** Python + Flask  
**Storage:** SQLite3  
**Target Audience:** University students and young professionals  

---

## 🎯 1. Vision Statement (Geoffrey Moore Template)

**FOR** university students and young professionals,  
**WHO** lose time deciding which task to start when facing a long list of pending activities,  
**THE** VibePlanner is a self-contained web-based daily activity planner,  
**THAT** automatically orders each day's activities by deadline, priority, and available time, and shows the user the reasoning behind the suggested order,  
**UNLIKE** static task managers such as Todoist, Notion, or Google Tasks (which only store what the user types) and AI schedulers such as Motion or Reclaim (which rank tasks as black boxes without explaining why),  
**OUR PRODUCT** turns a plain list into a ranked daily plan using a transparent, explainable scoring rule that the user can inspect, running entirely on our own server with no external services and no account required.

---

## 🚫 2. Out of Scope

This initial project release will **NOT** include:
1. User accounts, login, and authentication — single-user session design.
2. Dependence on external API services (e.g., OpenAI, Gemini, cloud LLMs) for core functionality.
3. Native mobile applications for iOS or Android.
4. Google Calendar, Outlook, or external calendar synchronization.
5. Push, email, or SMS notifications and reminders.
6. Team collaboration, shared boards, or task assignment between users.
7. Recurring activities and automatic repetition rules.
8. Payment processing, subscriptions, or billing.

---

## 💰 3. Financial & Economic Justification

Development cost for this release is **effectively zero ($0.00)**. The project is built by 4 students using AI coding assistants during a one-week university course, running on free-tier Python, Flask, SQLite, and PythonAnywhere hosting. 

Because the core planner makes zero external API calls, operating expense is zero. Revenue for future releases would follow a freemium model ($2.00/month for calendar sync and long-term history). The primary return of this MVP is educational and methodology validation.

---

## 📝 4. User Stories (Mike Cohn Template)

1. **User Story 1 (Task CRUD):**
   * *As a* student, *I want to* create, edit, and delete activities with a title, deadline, category, and priority *so that* I can see everything I have pending in one place.
2. **User Story 2 (Auto-Ranking):**
   * *As a* student, *I want* the planner to order today's activities automatically by deadline, priority, and available time *so that* I do not waste time deciding what to start.
3. **User Story 3 (Status & Progress Metrics):**
   * *As a* student, *I want to* change each activity's status to pending, in progress, or completed and see my daily completion percentage *so that* I can tell whether I am on track.
4. **User Story 4 (Explainable Score Breakdown):**
   * *As a* student, *I want to* see the score breakdown that placed an activity first *so that* I can trust the suggested order instead of ignoring it.

---

## ⚠️ 5. Project Development Risks

| Risk Category | Identified Risk Description | Mitigation Strategy |
|---|---|---|
| **Technology Constraint** | Free-tier hosting restrictions on PythonAnywhere. | Core planner has zero external network dependencies. |
| **Requirements Risk** | "Prioritise intelligently" ambiguity. | Numerical scoring rule defined with clear acceptance criteria. |
| **AI-Generated Code Risk** | Code produced by AI assistants containing hallucinations. | Manual and automated test suite required for every user story. |
| **Architecture Risk** | SQLite schema sync across team members. | One team member (Jose) owns and freezes the database schema file. |

---

## 🔗 6. Market References
- [Todoist](https://todoist.com) — Static task management benchmark.
- [Sunsama](https://www.sunsama.com) — Daily guided planning benchmark.
