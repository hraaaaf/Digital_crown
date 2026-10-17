# SEC-P1.2d — Actual Station gate and PIN-authorized escape in a Nuitka lab

## Scope / hard evidence required

This experiment executes the **actual** `backend/routers/workstation_mode.py`
authorization through the real `backend.routers.auth.get_current_user`
dependency and exposes the actual `/api/workstation/station/escape` PIN
endpoint alongside the genuine Agenda Resources route.

Two independent fictitious SQLCipher cabinet files are created in temporary
directories: first the original `backend/core/key_material.py`, then a
byte-identical Nuitka-compiled extension. Real Alembic migrations, JWT,
workstation registry ORM tables, ownership, permission, revocation persistence,
PIN verification and cookie issuance run on each one.

The lab checks the following boundaries:
- 401 missing/bad/refresh/revoked/inactive auth token
- 403 employee without permission and invalid owner PIN
- 423 missing/forged/cross-tenant/revoked workstation cookie
- Valid cabinet-mode access scoped to the correct tenant
- Actual transition to Station mode requiring a 423 lock
- Forged escape cookie denied
- Escape granted by **real PIN endpoint**, not a fabricated valid cookie
- Escape limited to the owner, access session, tenant, and mode revision
- Station revocation invalidates access
- Encrypted SQLCipher DB denies the wrong key and survives a fresh process
- Source/native HTTP parity on Ubuntu and Windows at immutable GitHub SHA

## Strong safety limits

Only test data, test passwords, 32-byte synthetic hexadecimal keys, fresh
short-lived JWTs and synthetic workstation cookies are used. All files are
inside a temporary directory. The real clinical application `backend.main`
(and its additional middleware), frontend/mobile UI, transport/TLS, physical
workstations, real patient data, commercial licensing and installers are NOT
run or tested. The workstation mode endpoint is tested through TestClient
with the real backend router, not via a physical keyboard or browser.

The backend routers' eager package initializer is deliberately bypassed to
avoid importing unrelated clinical routers, but the specific Station and
authentication modules are NOT substituted.

**Passing this laboratory is not full product certification** and does not
prove an exe is uncrackable. The compiled unit is only the key-material
module, not the complete FastAPI backend.

## Execution / gates

Workflow: [SEC-P1.2d Windows/Linux CI](../../.github/workflows/sec-p1-2d-real-station-sqlcipher.yml).
Script: `scripts/security/sec_p1_2d_real_station_native_lab.py`.

**EXPERIMENTAL**: both jobs pass with real Station and SQLCipher evidence
under same SHA. **REQUIRED before commercial release**: whole
`backend.main` middleware, real endpoints and real Station UX/multi-device
permission matrix, SQLCipher recovery and update rollback, Windows installer
signing/AV, independent security review and explicit owner approval.

Draft stacked on SEC-P1.2c #936; no merge, deployment, packaging switch,
repository visibility change or production data access.
