# DigitalCrown - All Context

Last updated: 2026-05-28

This file is the root context entrypoint for the repo.

Use it for two things:

1. quick routing to the right context pack or root file
2. broad architecture and repository understanding

Start here before loading deeper context files.

---

## How This File Works (the `all-*.md` Convention)

Every `process/context/` directory has one `all-*.md` entrypoint that acts as an attachable quick router for that domain. This root file (`all-context.md`) is the top-level router. Context groups each have their own `all-{group}.md` entrypoint.

**The pattern:**

```
process/context/
  all-context.md                      <-- THIS FILE: root router
  planning/
    all-planning.md                   <-- group router for planning
    example-simple-prd.md             <-- deep doc within the group
    example-complex-prd.md            <-- deep doc within the group
  tests/
    all-tests.md                      <-- group router for tests
  database/
    all-database.md                   <-- group router for database
  auth/
    all-auth.md                       <-- group router for auth
  uxui/
    all-uxui.md                       <-- group router for uxui
  ia-vision/
    all-ia-vision.md                  <-- group router for ia-vision
```

**How agents use it:**

1. Agent reads `all-context.md` first (this file)
2. Finds the relevant context group from the routing tables below
3. Reads that group's `all-{group}.md` entrypoint
4. Only then loads the specific deep doc needed

This layered routing keeps context windows small. Never load the whole `process/context/` tree.

---

## Quick Start

For most substantial tasks:

1. read this file first
2. choose the smallest relevant root file or context group from the tables below
3. only then load deeper files

---

## Current Root Entry Points

| File | Read when |
|---|---|
| `process/context/all-context.md` | any substantial planning, research, review, or implementation task |
| `process/context/tests/all-tests.md` | testing, verification, debugging test failures, execution planning |
| `process/context/planning/all-planning.md` | plan-shape calibration, planning examples, SIMPLE vs COMPLEX reference docs |
| `process/context/database/all-database.md` | database schema modification, SQLAlchemy/Alembic changes, database design queries |
| `process/context/auth/all-auth.md` | JWT authentication logic, Supabase credentials syncing, route guards |
| `process/context/uxui/all-uxui.md` | UI/UX component modifications, custom Tailwind v4 designs, Ghost Elite style edits |
| `process/context/ia-vision/all-ia-vision.md` | Panoramic/Cephalometric vision engines, PyTorch/ONNX models pipelines |

---

## Current Context Groups

| Group | Entry point | Scope |
|---|---|---|
| `planning/` | `process/context/planning/all-planning.md` | plan-shape calibration, planning examples, SIMPLE vs COMPLEX reference docs |
| `tests/` | `process/context/tests/all-tests.md` | test runners, commands, debugging, gaps |
| `database/` | `process/context/database/all-database.md` | SQLite DB schema, SQLAlchemy models.py, migrations (Alembic) |
| `auth/` | `process/context/auth/all-auth.md` | JWT Auth schemas, tokens rotation, Supabase Sync |
| `uxui/` | `process/context/uxui/all-uxui.md` | React 19 + Tailwind v4 Design System and Ghost Elite conventions |
| `ia-vision/` | `process/context/ia-vision/all-ia-vision.md` | Landmark calibrations, CephLD-CCA, YOLOv11 panoramic integration |

---

## Task Routing Table

| If the task involves... | Start with | Then load |
|---|---|---|
| general repo research | `all-context.md` | domain file named by task |
| implementation planning | `all-context.md`, `planning/all-planning.md` | the relevant grouped PRD example plus active plan |
| test planning or verification | `all-context.md`, `tests/all-tests.md` | the specific detailed testing file |
| debugging | `all-context.md`, `tests/all-tests.md` | the domain-specific doc for the bug area |
| UI/UX work | `all-context.md`, `uxui/all-uxui.md` | `uxui/all-uxui.md` and related component/feature guide |
| database work | `all-context.md`, `database/all-database.md` | SQLAlchemy models/schemas guide |
| auth work | `all-context.md`, `auth/all-auth.md` | backend routers/auth.py or security.py |
| vision IA models | `all-context.md`, `ia-vision/all-ia-vision.md` | U-Net / YOLO coordinates references |
| context maintenance | `all-context.md` | run `vc-audit-context` |

---

## Context Group Lifecycle

Context groups are durable knowledge domains, not feature folders.

Create a group when:

- a topic has 3+ durable docs
- a single doc exceeds roughly 800 lines with separable subtopics
- multiple agents repeatedly need only one slice of a large context file
- the topic maps to a stable operational domain (tests, database, auth, UI, workflows, etc.)

Do not create a group when:

- the content is a temporary report
- the content is a plan or execution artifact
- the topic is feature-specific and belongs in `process/features/...`

Move or split one group at a time. Use `all-{group}.md` entrypoints. Run the `audit-context` skill after every context organization change.

---

## Naming Convention

There are no `README.md` files inside `process/context/`.

Canonical entrypoints use `all-*.md`:

- root: `process/context/all-context.md`
- group: `process/context/{group}/all-{group}.md`

Each `all-{group}.md` file should act as the attachable quick router for that domain:

- tell the agent what the group covers
- give quick procedures and decision rules
- route to smaller deeper files

---

## Context Update Protocol

When durable project knowledge changes:

1. update the smallest relevant context file
2. update this file if routing, ownership, naming, or groups changed
3. update the owning `all-{group}.md` entrypoint when a group exists
4. run `audit-context`

---

## Repository Structure

```
DigitalCrown/
  backend/            -- Python FastAPI Backend
    ai_models/        -- AI vision pipelines (CephLD-CCA, dentex, ONNX helpers)
    core/             -- Configuration and central settings
    deprecated/       -- Archived tests/flows
    models/           -- Database models/SQLAlchemy configuration
    routers/          -- API endpoints modules
    schemas/          -- Pydantic validation models
    services/         -- Business logic engines (accounting, habits, DailyScheduler)
    utils/            -- Helper utilities
    main.py           -- FastAPI entrypoint
    models.py         -- Global SQLAlchemy models
  frontend/           -- React 19 TypeScript Frontend (Vite)
    src/
      components/     -- Reusable widgets
      features/       -- Page features modules (patients, agenda, clinical, ortho)
      pages/          -- Top-level routes views
      services/       -- API requests layers
      index.css       -- Tailwind CSS v4 design variables
  process/            -- This context system
    context/          -- Architectural contexts
    general-plans/    -- Implementation plans, reports, references
    features/         -- Feature-specific directories
    development-protocols/  -- Orchestration and standards references
```

---

## Technology Stack

- **Framework:** React 19 (Frontend), FastAPI 0.115 (Backend)
- **Language:** TypeScript 5.9 (Frontend), Python 3.12+ (Backend)
- **Runtime:** Node.js v24.x, Python venv
- **Database:** SQLite (digital_crown.db, clinical_vault.db) via SQLAlchemy ORM & Alembic migrations
- **Auth:** FastAPI JWT tokens rotation + Supabase Auth sync
- **UI:** Tailwind CSS v4 + Framer Motion (Ghost Elite Glassmorphism standard)
- **State:** Zustand for client stores
- **Package manager:** npm
- **AI Models:** PyTorch U-Net CephLD-CCA (Cephalometric), YOLOv11 ONNX (Panoramic)

---

## Key Patterns and Conventions

**Multi-Tenant Isolation:**
Every database query and model must enforce the `employer_id` context derived from authenticated JWT sessions to prevent data leakage between clinics.

**LAN-First & Sync:**
Application operates locally using the local SQLite databases. Offline grace periods are handled locally; synchronization to Supabase is performed asynchronously.

**Clinical Validation (Deterministic Fallback):**
Critical medical alerts (pregnancy NSAID block, penicillin allergies, gastroprotection) must use deterministic safety rules in the backend rather than relying solely on LLMs.

**Error Handling:**
FastAPI endpoints handle exceptions and raise HTTP Exceptions (e.g., 403 for license expiration, 409 for duplicate patients), UI catches and renders standard warning toast notifications.

---

## Environment and Configuration

**Config files:** `package.json`, `requirements.txt`, `pytest.ini`, `alembic.ini`, `vite.config.ts`, `tsconfig.json`

**Env var groups (names only, never values):**
- Auth & Database: `DATABASE_URL`, `JWT_SECRET`, `SUPABASE_URL`, `SUPABASE_KEY`
- Firebase/FCM: `FCM_CREDENTIALS`
- Frontend: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

---

## Scan Metadata

- Generated: 2026-05-28T16:25:00Z
- HEAD: 3bedb3c
- Mode: merge
- Package manager: npm
