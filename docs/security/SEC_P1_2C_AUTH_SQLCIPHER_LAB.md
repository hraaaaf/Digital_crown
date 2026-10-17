# SEC-P1.2c — Real JWT/permission + SQLCipher native key lab (EXPERIMENTAL)

## Goal and evidence

Compare two clean, disposable Digital Crown cabinet instances: one initialized
with the actual Python `backend/core/key_material.py`, and one with a Nuitka
native extension compiled from a byte-identical copy of that file. In both
cases, the test imports the **real** `backend.database`, `backend.models`,
`backend.security`, `backend.routers.auth`, and the real Agenda Resources
route. It executes Alembic migrations to a file-backed SQLCipher database
and uses the actual JWT and permission dependencies through FastAPI/TestClient.

The tests include synthetic cabinet identities, roles, permission denied,
valid access, refresh token denied as access token, malformed JWT, persistent
revocation, tenant isolation, inactive account, plus an intentionally
**stubbed** workstation boundary. It must prove the SQLCipher file is not
plaintext, denies the wrong key, and survives a fresh Python process. The
production `DigitalCrown.spec` and code are not modified.

Success is identical source/native HTTP responses and explicit expected
statuses on Windows and Linux, exact immutable SHA checkout, two green jobs,
encrypted disk checks and fresh process reread.

## Strict isolation

- All cabinet paths, environment settings, JWT signing keys and file-backed
  SQLCipher databases are created inside a temporary directory. Every user,
  agenda resource, token and value is fictitious.
- The test does NOT import `backend.main` and does NOT execute production
  background synchronizations, side effects or an installer.
- It uses the real JWT decode, blacklist persistence and role-permission
  functions from `backend.routers.auth` and `backend.security`.
- The workstation authorization boundary is deliberately substituted by a
  fail-closed fixture gate to avoid touching real workstation records.
  **Actual Station, full API middleware, real user lifecycle and cabinet
  license enforcement are NOT certified.**
- Backend routers' eager package initializer is bypassed solely to avoid
  unrelated clinical subsystem imports; the individual auth/Agenda modules
  are loaded in their original form.
- The tests do not prove device-bound commercial licensing, that native
  binaries cannot be reverse-engineered, or that all clinical DB/routing
  paths work through Nuitka.

## Runtime tooling

Workflow: [SEC-P1.2c experimental Linux/Windows CI](../../.github/workflows/sec-p1-2c-real-auth-sqlcipher.yml).
Harness: `scripts/security/sec_p1_2c_real_auth_sqlcipher_lab.py`.

The real database dependency graph mirrors the existing FUE-G04 SQLCipher
regression workflow, including `sqlcipher3==0.6.2` and Alembic migrations.
Nuitka is pinned to `4.3`. Linux uses the distro libsqlcipher headers;
Windows uses the native SQLCipher extension. The native compiled .pyd is
imported only in a child process so that Windows unlocks the binary before
the parent removes the disposable files.

## Gates and non-claims

This is an **EXPERIMENTAL** gate. Failure blocks only claims about the lab,
not unrelated product PRs. Do not infer general production readiness from
these tests. **Required before replacing official Windows packaging:** full
real API middleware and Station behavior, actual clinical authorization
matrix, storage restore/recovery, imager integrations, antivirus/signing,
installer updates/rollback, owner release approval and independent security
review. Never merge or deploy the lab as a clinical change automatically.

Keep the repository PUBLIC as requested by the owner; no credential/private
license signer key may ever ship to a cabinet binary.
