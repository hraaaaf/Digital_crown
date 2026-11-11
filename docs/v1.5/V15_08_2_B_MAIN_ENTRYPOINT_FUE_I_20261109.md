# DIGITAL CROWN — LOT08.2-B / B-5a: real Desktop FastAPI entrypoint FUE-I (synthetic)

**Date:** 2026-11-09. **Decision:** continue B-5 on explicit owner "Green next"; verify the **real** `backend.main:app` composition, not merely the standalone synthetic FastAPI lab. **Baseline HEAD:** `3203eff850b081261ec7959cb81cc8f4a2bda782`, [PR #1239](https://github.com/hraaaaf/Digital_crown/pull/1239) OPEN/DRAFT, never merge/install/deploy without explicit separate approval.

## GOAL / perimeter

Demonstrate that the opt-in `backend.main` composition really mounts the B-2 authorized Queue Core transport, that actual middleware and routes permit only proper loopback human sessions, and that no clinical DB or patient record participates. This is an **in-process ASGI** / real backend-import FUE-I, not an installed executable, TCP port, clinic startup/lifespan or browser product acceptance.

The previous [B-5 report](V15_08_2_B_DESKTOP_LAB_FUE_G_20261109.md) proved a real standalone synthetic FastAPI/Vite browser FUE-G (19/19), not the whole `backend.main` route stack. This is the remaining software composition gap.

## TEST / actual reproducible command

```powershell
Set-Location C:\Users\lenovo\Documents\Codex\2026-11-09\DigitalCrown-08_2B
$env:DIGITALCROWN_QUEUE_MAIN_FUE_RUN='1'
py -3.12 -m queue_core.tests.desktop_main_lab_probe
```

The test harness `queue_core/tests/desktop_main_lab_probe.py` is a **one-shot standalone program**, not a pytest auto-discovered test. It requires the explicit synthetic flag, prepares a fresh `TemporaryDirectory(prefix='dc-queue-fue-main-')`, a valid LAB marker and two independent local SQLite identity/queue files with fake operators and visits. It sets **only process-local** `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=1`, `DATABASE_URL=sqlite:///:memory:`, a matching explicit DB fingerprint and synthetic cryptographic keys. No cabinet profile or patient DB path is supplied.

It imports actual `backend.main:app` only after the startup anti-accident isolation attestation; it **never enters FastAPI's clinical lifespan**, runs seeds, migrates clinical data or starts a network port. The in-memory clinical engine is disposed after the ASGI requests. The Queue Core SQLAlchemy engine is explicitly disposed to prevent Windows file-lock leakage.

## BEFORE / ACTION / AFTER / observed proof

- **BEFORE:** `backend.main` app import absent, Queue Core LAB root isolated, one fictitious `SYNTHETIC` tenant/Q1/V1 with a RECEPTION operator, visitor state `PLANNED`.
- **ACTION:** import `backend.main:app`, verify synthetic mount at `/api/queue-core-lab`, verify clinical DB URL contains `:memory:`. A default Starlette TestClient peer named `testclient` returns **403** (loopback guard). Real loopback peer **127.0.0.1** is then passed via `httpx.ASGITransport`, without a socket or lifespan.
- **AFTER:** `GET snapshot` anonymous **401**, `POST operator session` **200**, authorized `GET snapshot` **200** (only V1), `POST check-in` **200** (`WAITING`), `POST logout` **200**, old session `GET snapshot` **401**. Events/state written only to synthetic Queue Core SQLite. The program prints `ACTUAL_BACKEND_MAIN_ROUTING_AND_RBAC_PASS_NO_CLINICAL_LIFESPAN` and exits **0**. Temporary databases removed after disposing connections. Negative explicit-flag check was also executed without the flag: it fails closed with `MAIN_FUE_EXPLICIT_FLAG_REQUIRED` and expected process exit **1**, wrapped by an assertion runner exiting **0**; no temp workspace created.
- **Warnings (non-gating in isolated test):** no synthetic SUPERADMIN_EMAIL, Pydantic model namespace warnings and missing `srpose38` asset in this sparse checkout. The first test had `ModuleNotFoundError: relay` because local **sparse checkout** excluded the tracked `relay/` folder; fixed locally by `git sparse-checkout add relay` without changing code. Another failed on Windows cleanup before explicit Queue Core engine disposal; corrected in the harness and rerun to **exit 0**.
- **Regression evidence inherited from exact baseline code SHA:** prior Windows Queue Core **121/121 PASS**, TypeScript and `npm run build:test` PASS, Chromium LAB FUE-G **19/19 PASS** with 7 real screenshots and zero unexpected errors. This new harness itself must be run and recorded in the PR at its own final SHA; isolated GitHub Queue CI may not execute it because that CI installs only Queue Core's minimal dependencies.

## RISKS / gates and NEXT

The same source-level `backend.main` tests cannot certify clinical startup or an installed executable, because intentionally avoiding the lifespan also avoids genuine clinical DB creation/seeding and actual app runtime conditions. Desktop app auth via the legacy JWT and clinical appointments mapping are **not integrated**; the existing `WaitingRoomPage.tsx` and `/appointments` remain untouched. No real patients, hardware, multi-PC/TLS transport, physical LOT10 or human target-visual approval. The new test does NOT certify installer/Windows ACL physical enrollment.

**Decision:** B-5a **FUE-I REAL MAIN COMPOSITION PASS (synthetic)**. LOT08.2-B remains **OPEN**, [PR #1239](https://github.com/hraaaaf/Digital_crown/pull/1239) DRAFT/unmerged. **Next exact:** verify queued Queue Core GitHub run and Scope Gate on final HEAD; if green, define a distinct human authorization gate for clinical/runtime installable integration without silently mounting the test endpoint in cabinet. Notion and `STATE.md` remain canonical.
