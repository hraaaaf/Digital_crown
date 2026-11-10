# DIGITAL CROWN V1.5 — LOT08.2-B / B-5b — Critical Linux CI dependency isolation

Date: 2026-11-09. **GO:** owner "Red" following B-5a. **Decision scope:** correct a demonstrable GitHub Linux Queue Core CI collection failure without relaxing any test, clinical privacy boundary or LAB gating. Branch `feat/v15-08-2-b-rbac-isolation-20261109`; PR #1239 remains OPEN/DRAFT, NOT MERGED. No clinic startup, migration, real patients or deployment.

## BEFORE — independent proof of failure

[Queue Core workflow #42634986803](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986803) on exact SHA `10ff5f55b4ec43709ad23e7f1b7a4e90f31283b9`: **COMPLETED / FAILURE**. Job `queue-domain-fue0` #129220666124 successfully installed its isolated pinned Python 3.11 dependency set; `pytest -q queue_core/tests` failed during test **collection** with **exit 2**, `1 error / 0 tests executed`. Its traceback is reproducible:
- `queue_core/tests/test_desktop_lab_bridge_08_2_b.py` imported `backend.queue_core_desktop_lab`.
- Python always imports `backend/__init__.py` first, which registers clinical models and runtime policy imports; `backend.schemas.patient` indirectly imported `pydantic.EmailStr`.
- Slim Queue Core CI intentionally does **not** install full clinical dependencies, and `email_validator` was absent. Result: `ModuleNotFoundError: No module named 'email_validator'`. **Not an RBAC/SQL domain logic failure.**
- Parallel exact-SHA [CI Scope Gate #42634986969](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986969) **SUCCESS**.

## ACTION — fix dependency boundary, keep tests strict

1. Move the unchanged standalone synthetic Desktop LAB mount implementation into `queue_core/service/desktop_lab_bridge.py`. This code depends only on Queue Core, FastAPI and SQLAlchemy.
2. Retain `backend/queue_core_desktop_lab.py` as a **thin compatibility re-export**, preserving the existing `backend.main` import path, API and opt-in `ENVIRONMENT=test` / marker / two separate synthetic SQLite DB safety checks.
3. Update the Queue Core integration tests to import the real implementation from `queue_core.service.desktop_lab_bridge`, **not** the clinical `backend` package. Add a fresh-interpreter subprocess regression oracle asserting `backend` never appears in `sys.modules` upon importing the bridge. A broad clinical dependency, fake `email_validator` module, test skip, monkeypatch to clinical `backend.__init__`, or CI exclusion would weaken isolation and is deliberately rejected.
4. No change to `backend/main.py`, clinical `/appointments`, runtime startup policy, production RBAC, real user database, migration or deployment. No change to the pinned dependency list is necessary if the isolation boundary holds.

## AFTER / FUE-I oracle

- Fresh Python 3.12 import of `queue_core.service.desktop_lab_bridge` on Windows observed `BACKEND_LOADED=False` / exit 0.
- Queue Core Desktop bridge standalone test: 8/8 PASS in 12.84s before additional fresh-interpreter regression.
- Exact real `backend.main` synthetic ASGI probe rerun after compatibility shim: `ACTUAL_BACKEND_MAIN_ROUTING_AND_RBAC_PASS_NO_CLINICAL_LIFESPAN` / exit 0; 403 fictitious client, 401 anonymous, 200 login/queue/check-in/logout, 401 post-logout, no clinical lifespan. No patient DB exposure.
- Full Windows Python 3.12 Queue Core regression after the fix: **122/122 PASSED in 82.28s**, exit 0. Python `compileall -q queue_core backend/queue_core_desktop_lab.py` and `git diff --check` completed with success. CI exact-head Linux still must be verified; never reinterpret the historically failed SHA as green.

**Limitations/next:** LAB-only proof, not installed Desktop clinical acceptance. B-5b targets the CI dependency boundary, not production release. B remains OPEN until separately authorized clinical integration/physical tests. New CI logs must be read, including Linux skipped counts; no fake 100% or false PASS.
