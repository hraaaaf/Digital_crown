# SEC-P1.2b — Real Agenda Resources router native parity (EXPERIMENTAL)

## Goal and exact boundaries

Compile a byte-identical copy of the real Digital Crown module
`backend/routers/agenda_resources.py` as a native Nuitka extension
(PE/PYD on Windows, ELF on Linux). Load the unmodified real
`backend/schemas/agenda_resources.py` schema, and compare FastAPI/TestClient
HTTP responses from the source router against the compiled router on
17 ordered test scenarios.

The actual routes are mounted under their canonical
`/api/agenda/resources` prefix:
- GET list, including inactive resource filtering and tenant scoping;
- POST create, validation, duplicate 409, and unauthenticated denial;
- PATCH update, missing-resource and cross-tenant 404, validation 422,
  duplicate name conflict 409, and normalization.

## Strict synthetic isolation

**No actual backend application, DB engine, clinic database or auth system
is imported.** Tests replace the production database and permission modules
at import time, with explicit fail-closed synthetic fixtures.
The data model is a minimal in-memory SQLAlchemy mapping representing
the fields queried by this endpoint. TestClient handles the actual FastAPI
routing and Pydantic response/input validation from the original route.
A new temporary SQLite `:memory:` database is created independently for
source and native HTTP runs, with deterministic fictitious resources for
two cabinet IDs. A fake permission dependency checks a synthetic header,
not an actual user token. No clinical names, patient records, keys or
external services are used.

A child process loads the compiled module and exits before Windows needs to
delete the loaded .pyd. The parent cleans up all temporary compilation files.

## Proven scope and nonclaims

- Proof of *API behavior parity of this real agenda router* under a fake DB
  and fake auth, **not** proof of the real clinic auth/RBAC or true clinical
  tenant separation, SQLCipher, transactional concurrency, LAN/TLS, PWA/mobile
  integration or entire backend behavior.
- The temporary ORM substitute implements only fields used by this router;
  changes to the real SQLAlchemy model or true migrations remain out of scope.
- Nuitka compilation makes inspection harder but cannot prevent code
  reverse engineering or licence tampering by itself.
- No changes to `backend/routers/agenda_resources.py`, its schema,
  `backend.main`, `DigitalCrown.spec`, packaged app or patient data.
- This is an **EXPERIMENTAL** nonblocking test. Keep this PR in draft and
  stacked on SEC-P1.2 #931; no merge/release/deployment or repo visibility
  change without separate authorization.

## Evidence and later gates

[Experimental Windows/Linux CI workflow](../../.github/workflows/sec-p1-2b-real-agenda-router.yml).
Required evidence for this lab: actual PE/PYD and ELF extensions, same
17 statuses and response bodies, exact PR SHA checkout, both OS jobs SUCCESS.
Any failed job or unobserved run leaves this lab OPEN.

Before a commercial packaging switch, validate real production auth,
tenant/permissions, PostgreSQL and encrypted SQLCipher behavior, all
FastAPI endpoints, imaging, backup/export and patient continuity, signed
installer and rollback on supported Windows installations.
