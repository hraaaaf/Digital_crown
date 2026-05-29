# DigitalCrown - All Tests

Last updated: 2026-05-28

Attach this file first when the task involves testing, verification, or test debugging.

This is the fast operator guide for the testing surface:

- which runner to use
- what command to start with
- how to quickly debug common failures
- which deeper file to read next

---

## How This File Works

This is the `all-tests.md` entrypoint for the `tests/` context group. It follows the `all-*.md` routing convention:

1. Agents read `all-context.md` first and get routed here for testing tasks
2. This file gives quick decision rules and commands

---

## What This Covers

- test runner selection
- quick commands by package
- fast debugging procedures
- current testing gaps worth remembering

## Read This When

Use this file when you need to:

- run tests after implementation
- decide between test runners
- debug failing tests

---

## Quick Decision Guide

### Use `pytest` (Backend) when

- the changes are in Python modules (FastAPI routers, schemas, database models, or core services).
- you need to verify API outputs, license logic, scoring engine calculations, or PDF generator layouts.

### Use `vitest` (Frontend) when

- the changes are in React components, hooks, Zustand stores, or page-level features.
- unit tests are located under `frontend/src/` or `frontend/tests/`.

---

## Default Verification Order

Unless the task clearly needs a different path:

1. run the narrowest existing automated test
2. use unit/integration tests before browser tests

---

## Commands

| Directory | Runner | Command | Notes |
|---|---|---|---|
| `backend/` (root) | pytest | `$env:PYTHONPATH="."; venv/Scripts/pytest` | Requires venv activation and PYTHONPATH set |
| `frontend/` | vitest | `npm --prefix frontend run test` | Standard unit and hook tests |
| `frontend/` (watch) | vitest | `npm --prefix frontend run test:watch` | Watch mode for active development |

**Typecheck (TypeScript):**
```bash
npm --prefix frontend run build  # or npx tsc --noEmit in frontend/
```

**Lint:**
```bash
npm --prefix frontend run lint
```

---

## Debugging Quick Reference

- **Backend Module Import Error:** When running pytest, make sure to execute from the root directory with the Python path configured (`$env:PYTHONPATH="."`) or run `venv/Scripts/python -m pytest` to avoid `ModuleNotFoundError: No module named 'backend'` errors.
- **SQLite Database Conflicts:** Backend tests may write to temporary database files or utilize a mocked DB. Ensure a clean environment and stop any running uvicorn servers if locking issues arise on `clinical_vault.db` or `digital_crown.db`.
- **Zustand and React 19 Hydration:** Unit tests in Vitest that test client-side stores should clear state or mock context providers (e.g., custom Auth providers) as required.

---

## Known Gaps

- End-to-end user navigation flows are not yet fully covered by Playwright (manual checking on UI needed).
- AI Panoramic YOLOv11 ONNX and CephLD-CCA inference routines rely on external files (mocked or skipped during standard CI if models are not preloaded).
