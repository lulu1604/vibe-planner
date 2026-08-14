# 📋 VUP Phase 1: Inception Document

**Project Name:** VibePlanner — Multi-User Activity Planner with Transparent Prioritization
**Version:** 2.0 (Update — Multiusuario, Roles y Permisos)
**Framework:** Python 3 + Flask
**Storage:** SQLite3
**Deployment:** PythonAnywhere (free tier, WSGI) + venv
**Target Audience:** University students, young professionals and small work teams

> **Qué cambia respecto a v1.0.** La v1 fue un planificador de un solo usuario, sin
> cuentas, cuyo diferenciador era el puntaje explicable. La v2 conserva ese motor
> intacto y lo convierte en una plataforma con cuentas, **roles agregativos**
> gobernados por una tabla de permisos, calendario, tablero Kanban, gestión de
> hábitos y métricas. Las secciones marcadas con **`[v2]`** son nuevas o
> reescritas; el resto se mantiene deliberadamente.

---

## 🎯 1. Vision Statement (Geoffrey Moore Template) `[v2]`

**FOR** university students, young professionals and small work teams,
**WHO** lose time deciding what to do next, juggle personal life and work in
different tools, and cannot see whether their day actually went as planned,
**THE** VibePlanner is a self-contained multi-user web platform for daily
planning,
**THAT** lets each person register an account, plan their day, month and habits,
organise work on a Kanban board, invite others to their events through a link,
and see the reasoning behind every suggested order — while an administrator
manages accounts, roles and system-wide metrics,
**UNLIKE** static task managers such as Todoist, Notion or Google Tasks (which
only store what the user types), AI schedulers such as Motion or Reclaim (which
rank tasks as black boxes) and enterprise suites such as Jira or Asana (which are
heavy, paid, and built for companies rather than for a student's actual day),
**OUR PRODUCT** combines a transparent, inspectable scoring rule with an
aggregative permission model, running entirely on our own server with zero
external services and zero operating cost.

### 1.1 What "aggregative roles" means in this product `[v2]`

The decision that shapes the whole architecture: **a role is not a category the
user belongs to, it is a bag of permissions the user carries.** A person can hold
several roles at once, and their effective permissions are the **union** of the
permissions of all their roles.

The practical consequence is that **the administrator is also a user.** They do
not live in a parallel admin universe: they have their own planner, their own
habits and their own calendar, plus the administration permissions on top.

```
permisos_efectivos(usuario) = ⋃ permisos(rol)  para cada rol asignado al usuario
```

This is why the model needs a real `permissions` table joined to `roles` instead
of a single `role` column on `users`. A hard-coded `if user.role == "admin"`
scattered across the controllers is exactly what this design rejects.

### 1.2 Account creation policy `[v2]`

| Path | Who can use it | Roles granted |
|---|---|---|
| **Public registration** (`/register`) | Anyone visiting the site | `usuario` only — always, with no exception |
| **Administrative creation** (`/admin/usuarios`) | A user holding `usuario.crear` | Any combination of roles the administrator chooses |
| **Bootstrap seed** (`seed.py`) | Run once at deployment | The initial administrator account (`usuario` + `admin`) |

**There is no public administrator registration and no "request admin access"
flow.** The first administrator exists because the seed created it; every other
privileged account exists because an administrator granted the role. This closes
the most common privilege-escalation hole in student projects, where the
registration form trusts a `role` field coming from the browser.

---

## 🚫 2. Out of Scope `[v2]`

This release will **NOT** include:

1. **Dependence on external API services** (OpenAI, Gemini, cloud LLMs) for core
   functionality — the platform must plan, rank and explain with no network access.
2. **Real email or SMS delivery.** Invitations travel as an in-app link that the
   host copies and shares by whatever channel they want. No SMTP, no Twilio.
3. **Google Calendar, Outlook or external calendar synchronisation.**
4. **Native mobile applications** for iOS or Android — the web interface must be
   responsive instead.
5. **Push notifications** and background reminders.
6. **Payment processing, subscriptions or billing.**
7. **Password recovery by email.** A user who loses their password asks an
   administrator to reset it from the user management panel.
8. **Third-party identity providers** (Google, Microsoft, OAuth of any kind).
9. **Recurring events with repetition rules** (RRULE). Habits cover the daily
   repetition need; the calendar stays on discrete events.
10. **File attachments, avatars uploaded by users, or any binary storage.**
11. **Real-time collaboration** (websockets, live cursors, simultaneous editing).
12. **Multi-tenant isolation between organisations.** One deployment is one
    community of users.

> ⚠️ **Rule for the whole team:** this list is frozen. Anything not in the
> functional requirements of § 4 and not forbidden here goes to the **v3 backlog**
> (`docs/v2/BACKLOG_v3.md`), never straight into the code.

---

## 💰 3. Financial & Economic Justification `[v2]`

**Development cost: $0.00.** Four students, one week, AI coding assistants, and a
stack that is free at every layer — Python, Flask, SQLite, venv and the
PythonAnywhere free tier.

**Operating cost: $0.00 and, more importantly, flat.** Because the platform makes
zero outbound API calls, cost does not grow with the number of users. Adding
authentication and multiple accounts changes the storage footprint (a few KB per
user in a SQLite file) but not the cost structure. This is the economic advantage
over any competitor that resells an LLM or a bank connection: their marginal cost
per active user is positive, ours is zero.

**Market.** The personal-productivity software market is measured in billions of
dollars, but that figure is directional only and is not verified research. The
serviceable segment is much narrower and much more honest: Spanish-speaking
university students and small teams in Latin America who need one place for
personal life and work, and who will not pay for Asana. A realistic obtainable
target for a first release is a few hundred accounts through university channels.

**Revenue model (hypothetical, not part of this release).** Freemium: the personal
planner stays free; a paid tier around $2.00/month would add long-term history,
data export and external calendar sync. Because fixed costs are near zero, a very
small conversion would cover hosting long before any headcount cost appears.

**The real return of this project is educational:** a multi-user, permission-
governed, deployed and tested product built in one week with disciplined
AI-assisted engineering, from inception through transition.

---

## 📝 4. User Stories (Mike Cohn Template)

### 4.1 Inherited from v1.0 — still valid, now scoped per account

1. **US1 — Task CRUD:** *As a* user, *I want to* create, edit and delete
   activities with a title, deadline, category and priority *so that* I can see
   everything I have pending in one place.
2. **US2 — Auto-Ranking:** *As a* user, *I want* the planner to order today's
   activities automatically by deadline, priority and available time *so that* I
   do not waste time deciding what to start.
3. **US3 — Status & Progress Metrics:** *As a* user, *I want to* change each
   activity's status and see my daily completion percentage *so that* I can tell
   whether I am on track.
4. **US4 — Explainable Score Breakdown:** *As a* user, *I want to* see the score
   breakdown that placed an activity first *so that* I can trust the suggested
   order instead of ignoring it.

> **Migration note:** every task now belongs to an owner. What was "the task list"
> in v1 is "*my* task list" in v2, and no user can ever read another user's tasks
> unless a permission explicitly allows it.

### 4.2 New in v2.0 `[v2]`

**Módulo A — Núcleo: cuentas, roles y permisos**

5. **US5 — Registration and login:** *As a* visitor, *I want to* create an account
   with username, email and password and then log in *so that* my plan is private
   and persists between sessions.
6. **US6 — Aggregative permissions:** *As the* system, *I want* each user's
   effective permissions to be the union of the permissions of all their roles
   *so that* an administrator can also be an ordinary user without duplicated
   accounts.
7. **US7 — User management:** *As an* administrator, *I want to* list, create,
   edit, deactivate and assign roles to accounts *so that* I control who enters
   the platform and what each person can do.

**Módulo B — Planner diario y Kanban**

8. **US8 — Daily review board:** *As a* user, *I want* a single screen with only
   today's activities, their schedule and their state *so that* I do not have to
   open the full calendar to know what my day looks like.
9. **US9 — Kanban board:** *As a* user, *I want to* move my activities across
   Backlog, To do, Ongoing and Done *so that* I can see the state of my work at a
   glance.
10. **US10 — Team task assignment:** *As a* user holding `tarea.asignar`, *I want to*
    create tasks assigned to another user and follow the column they are in *so
    that* I can coordinate a small team without leaving the planner.

**Módulo C — Calendario e invitaciones**

11. **US11 — Monthly schedule:** *As a* user, *I want to* create events with name,
    description, date, time and colour and see them on a monthly calendar *so that*
    I can plan the current month and the ones ahead.
12. **US12 — Invitation by link:** *As a* host, *I want to* generate a link for an
    event and share it *so that* another registered user can accept and see the
    event in their own calendar.

**Módulo D — Hábitos y métricas**

13. **US13 — Habit tracking:** *As a* user, *I want to* define habits (diet,
    exercise, relaxation, sleep hours) and tick them off daily *so that* I can
    sustain routines and not just isolated tasks.
14. **US14 — Daily achievement metrics:** *As a* user, *I want to* see what I did
    and achieved today split into Work, Personal and Activities *so that* I can
    close my day with an honest picture of it.
15. **US15 — System metrics:** *As an* administrator, *I want to* see how many
    accounts, events and active daily lists the platform has *so that* I can tell
    whether the product is actually being used.

**Módulo transversal — Interfaz**

16. **US16 — Responsive interface:** *As a* user on a phone, tablet or laptop, *I
    want* every screen to adapt to my screen size *so that* I can check and update
    my plan wherever I am.

---

## ⚠️ 5. Project Development Risks `[v2]`

| # | Risk Category | Identified Risk Description | Mitigation Strategy |
|---|---|---|---|
| R1 | **Technology constraint** | PythonAnywhere free tier restricts outbound network access to an allowlist, so anything depending on an external service works locally and fails in production. | The core platform has zero outbound dependencies. Fonts and CSS are self-hosted in `static/`, never loaded from a CDN. |
| R2 | **Security — authentication** | This is the team's first application with real accounts. Storing passwords in plain text or trusting a `role` field sent by the browser would be a fatal defect in the rubric. | Passwords hashed with `werkzeug.security` (never stored or logged in clear). `/register` grants the `usuario` role **server-side**, ignoring any role field in the payload. |
| R3 | **Security — horizontal escalation** | A logged-in user changing an `id` in the URL to read or edit somebody else's task or event. | Every route enforces **two** checks: the required permission *and* ownership of the record. Documented as a mandatory test case (TC-12). |
| R4 | **Schema migration** | v1 databases already exist on team laptops and on the deployed server; adding `users` and a `user_id` column breaks them silently. | `schema_v2.sql` is the single source of truth, `migrate_v1_to_v2.py` is provided, and everyone deletes their local `vibe_planner.db` on the agreed day. Jose remains the sole schema owner. |
| R5 | **Requirements risk** | "Manage habits and metrics" is not testable as written. | Every metric is specified numerically with acceptance criteria before coding (see Elaboration I). |
| R6 | **AI-generated code risk** | AI assistants produce plausible code with untested paths, especially in permission checks and date arithmetic. | Manual test plan plus automated asserts for every user story; permission decisions concentrated in one auditable module (`security.py`). |
| R7 | **Scope risk** | The v2 requirement list is large for four people in one week; a half-finished module is worth less than a complete smaller one. | Modules are strictly ordered: the Núcleo is built first because everything else depends on it. Anything unfinished moves to the v3 backlog rather than being merged incomplete. |
| R8 | **Concurrency** | SQLite locks the whole file on write; several simultaneous users can produce `database is locked`. | One connection per request, short transactions, `PRAGMA journal_mode=WAL` and a connection `timeout`. Acceptable for the expected scale, documented as a known limit. |
| R9 | **Team coordination** | Four people touching the same repository during one week, with modules that depend on the Núcleo. | Ownership of files is exclusive per module, contracts are frozen in writing before coding, and everyone merges to `main` daily. |
| R10 | **Session secret** | A `SECRET_KEY` hard-coded in the repository invalidates every session's security and is visible in the public GitHub history. | `SECRET_KEY` read from an environment variable with a local-development fallback; the production value is set only in the PythonAnywhere panel. |

---

## 🔗 6. Market References

- [Todoist](https://todoist.com) — static task management benchmark.
- [Sunsama](https://www.sunsama.com) — daily guided planning benchmark.
- [Trello](https://trello.com) — Kanban interaction benchmark for US9.
- [Habitica](https://habitica.com) — habit-tracking benchmark for US13.
- [Motion](https://www.usemotion.com) — the black-box AI scheduler VibePlanner is defined against.

---

## ✅ 7. Definition of Done for the v2 release `[v2]`

The release is done when, on the deployed PythonAnywhere instance:

1. A visitor can register, log in and log out, and their data is private.
2. The seeded administrator can create a user, assign roles and deactivate an account.
3. A user with two roles demonstrably holds the union of both permission sets.
4. The four v1 stories still work, now scoped to the logged-in account.
5. The daily planner, the Kanban board, the monthly calendar, the habits module
   and the metrics screens each satisfy their acceptance test.
6. An event invitation link is accepted by a second account.
7. Every screen is usable at 360 px, 768 px and 1280 px wide.
8. The manual test plan (Construction III) passes with no open defects.
