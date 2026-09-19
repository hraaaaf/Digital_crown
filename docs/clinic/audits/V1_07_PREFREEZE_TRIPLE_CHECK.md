# V1-07 — Pre-freeze Triple-Check Audit

Status: **IN_PROGRESS — V1-08 FREEZE BLOCKED**

Date: 2026-09-19  
Audit base: `master@ceae1624c5f1311eb7ffcf512785b8a30fe438fc`

## Goal

Adversarially audit the complete V1 pre-freeze surface before selecting an immutable V1-08 candidate.

## Success

V1-07 can close only when:
- three audit passes are complete;
- every finding is classified BLOCKER / MUST-FIX / ACCEPTED-RISK / POST-V1;
- every V1 BLOCKER and MUST-FIX is remediated;
- exact-head targeted + global regression evidence is green;
- Pass 2 re-checks the remediation against code/tests/contracts;
- Pass 3 actively searches for residual/contradictory failure modes;
- canonical docs and Notion agree;
- no real cabinet mutation occurred.

## Pass 1 — broad audit findings

### BLOCKER — legacy media ownership can fail open

`backend/main.py::_assert_media_tenant` currently allows a file when no DB row can prove ownership. Legacy acte attachments behave similarly. Clinic branding routes require authentication but do not prove requested `public_id` belongs to the authenticated cabinet.

Risk: an authenticated user who can guess an orphan/legacy path may receive a file whose tenant cannot be proven.

Required remediation:
- unknown ownership => fail closed;
- foreign/ambiguous ownership => fail closed;
- clinic asset path must be bound to the authenticated cabinet public_id;
- adversarial tests for orphan and cross-tenant paths.

### BLOCKER — cabinet HTTP/LAN exposure with non-Secure cookies

Verified:
- `DigitalCrown.spec` packages `run.py`;
- `run.py` defaults cabinet host to `0.0.0.0` and starts uvicorn without TLS;
- first-boot cabinet env is HTTP;
- auth cookies are Secure only in `production`, not cabinet;
- controlled real launcher also defaults `BindHost=0.0.0.0` even when TLS is absent.

Required remediation:
- loopback-only default when TLS is absent;
- non-loopback cabinet binding allowed only with explicit HTTPS and cert/key;
- packaged runtime supports the explicit TLS contract;
- cabinet auth cookies Secure when HTTPS is enabled;
- regression tests.

### MUST-FIX — Google OAuth state/CSRF binding missing

`/api/auth/google/authorize` emits no OAuth `state`; callback performs no state validation.

Required remediation:
- cryptographically random state;
- short-lived HttpOnly state cookie;
- constant-time callback validation;
- one-shot deletion;
- mismatch/missing/success contract tests.

### MUST-FIX — cabinet certification dependency drift

Canonical runtime/CI pins:
- torch 2.10.0
- torchvision 0.25.0
- torchaudio 2.10.0

`cabinet-release-certification.yml` still installs torch 2.12.0 / torchvision 0.27.0 and then consumes torchaudio 2.10.0.

Required remediation:
- use the canonical pinned trio;
- exclude all three before installing the remainder;
- `pip check`.

### MUST-FIX — competing V1 objective documents

Both exist:
- `DIGITALCROWN_V1_OBJECTIVE.md`
- `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md`

The clinic document predates the root duplicate and is referenced by the V0→V1 handover as source of truth.

Required remediation:
- `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md` remains canonical;
- root file becomes a non-authoritative pointer or is removed;
- all roadmap references become explicit.

### MUST-FIX — implicit Sentry cloud observability

Sentry currently initializes whenever `SENTRY_DSN` exists, with traces/profiling at 100%, independent of the explicit telemetry opt-in.

Required remediation:
- cloud observability must require explicit opt-in;
- cabinet remains local-first by default.

### MUST-FIX (low) — raw health exception disclosure

Unauthenticated health endpoints return raw DB/storage exception strings.

Required remediation:
- generic external error state;
- detailed exception only in server logs.

### REVIEW — Firebase pending_clients onboarding

Signup writes cabinet-owner onboarding identity/contact fields to Firebase. This is not patient clinical data, but Pass 2 must explicitly reconcile it with the “identity/licensing only” cloud boundary.

## Existing positive controls

- ZERO-LLM runtime dependency/file scan found no OpenAI/Anthropic/Gemini/Ollama runtime package or legacy LLM gateway filename.
- patient/agenda/payment/act cloud sync facade is a fail-closed no-op.
- Alembic unique runtime head is `ojf20000008`.
- exact-release certification has SHA/content/runtime-asset/provenance checks.
- real V0 baseline is PostgreSQL and has a defined PREUPDATE/backup/rehearsal gate.

## Closeout supersession

PR #627 was closed without merge because this mandatory audit invalidated the prior V1-07 closeout assumption.

V1-08 remains blocked until this audit closes green.


### MUST-FIX — Firebase onboarding minimization

Pass 1 confirmed that `pending_clients` cloud writes were not consumed by the cabinet runtime but included phone, full address and the local DB user id.

Remediation applied on the audit branch:
- cloud payload restricted to onboarding identity/licensing metadata: email, display name, pending status, timestamp;
- phone/address remain local;
- local database identifiers are not exported.


## Pass 2 — evidence double-check findings

The remediation was re-read against current code rather than trusting green intent.

Additional findings:
- the first edit of `cabinet-release-certification.yml` corrupted the dependency-install block; repaired before closeout;
- clinic logo hardening did not initially cover letterhead uploads; letterheads are now always decoded and normalized to inert PNG;
- packaged install/update path could silently bootstrap a new cabinet environment and fall back to SQLite when the real V0 PostgreSQL env was not selected. The installer now copies files only and does not auto-start/register a startup task; frozen first boot requires an existing explicit env or the explicit `--initialize-new-cabinet` fresh-install intent;
- document download manually decoded access JWTs without consulting the revocation store; it now uses canonical `get_current_user`;
- token revocation lookup itself failed open on persistent-store errors; it now denies on unreadable revocation state and surfaces explicit revoke persistence failures.

Pass 2 result: remediation required additional corrections; prior state was not freeze-safe.

## Pass 3 — adversarial re-audit status

Completed adversarial checks so far:
- sensitive committed-file inventory: no committed .env / Firebase credentials / PEM / private-key / PFX/P12 artifact detected in the exact audited tree;
- ZERO-LLM filename/dependency surface remains absent for OpenAI/Anthropic/Gemini/Ollama legacy runtime components;
- critical router review found local guards where static heuristics initially reported false positives;
- mobile JWT decode paths reviewed retain token type/JTI/device/tenant revocation checks;
- document-download revoked-token bypass fixed;
- upload active-content paths reviewed for logo + letterhead;
- legacy-media unknown/ambiguous ownership now fails closed;
- cabinet plaintext non-loopback exposure now fails closed;
- Firebase onboarding egress minimized to identity/licensing metadata.

Repository hygiene note:
- `e2e/node_modules` remains versioned. It is excluded from the cabinet release payload and is classified **POST-V1 CLEANUP**, not a release blocker.

### Pass 3 — residual findings and remediation

The final router/auth/admin/mobile sweep found additional V1 issues after the initial Pass 3 notes. They are part of this audit and must not be hidden behind the earlier green runs.

- **MUST-FIX — public trial activation input bounds.** `TrialActivationRequest` now bounds activation code (128), full name (160) and cabinet name (160); oversized codes are rejected before the DB lookup. Remediation commits: `f8b6942a…`, `57c93713…`; regression contract: `cab63b95…`.
- **MUST-FIX — pre-parse body bound for small unauthenticated JSON routes.** Endpoint-level rate limits execute after FastAPI/Pydantic parsing. A targeted 64 KiB `Content-Length` gate now runs before parsing for signup/refresh/demo/activate-trial/mobile claim/mobile refresh; missing length is refused and multipart/upload plus larger authenticated business JSON paths are untouched. Remediation: `ac7f94e1…`; test: `2ad79f19…`.
- **MUST-FIX — unauthenticated signup abuse boundary.** `/api/auth/signup` previously wrote DB state, scheduled emails and attempted a Firebase onboarding write without a rate limit. It now uses the existing scoped/IP limiter. Signup and refresh payload fields are bounded. Remediation: `6d0eed47…`, `ad566062…`; tests: `9b72043…`.
- **MUST-FIX — legacy team approval parity across Google OAuth.** Local login and refresh rejected non-approved employee accounts; Google callback did not explicitly enforce the same invariant for legacy-inconsistent rows. The callback now rejects employee accounts whose `approval_status` is not `approved`. Remediation: `ad566062…`.
- **BLOCKER — admin document normalization was a cross-tenant GET mutation.** `GET /api/admin/normalize-docs` executed global `UPDATE document_archives` statements without cabinet scope. It is now POST-only, scoped through patients belonging to the authenticated employer, and no longer returns raw SQL exception strings. Remediation: `59e5105c…`; test: `898e1386…`.
- **MUST-FIX — backup download path confinement.** The admin backup download route only checked the `.enc` suffix. It now rejects both path separators, resolves the canonical path, requires the resolved parent to equal the dedicated backups directory and requires a regular file. Remediation: `6c30f2a5…`; test: `38b14211…`.
- **MUST-FIX — mobile legacy identity parity and unbounded auth inputs.** Pairing claim, active mobile identity and rotating refresh now explicitly enforce employee `approval_status=approved`. Pairing token/public-key and refresh-token inputs are bounded. Remediation: `b791f28c…`, `6a60047e…`; test: `8eb33d18…`.
- **NO FINDING — legacy HTTP mobile URL helper in the secure cabinet runtime.** The literal legacy helper remains HTTP, but the canonical secure runtime installs `mobile_mdns` overrides to `https://digitalcrown.local:8005`; this invariant is already locked by `test_mobile_https_runtime_contract.py`. It is therefore not treated as a runtime plaintext-LAN regression.
- **NO NEW BLOCKER — documents/media final sweep.** Canonical auth, document permission gates, patient/cabinet ownership checks and fail-closed media provenance remained present on the audited branch.

Code remediation through `2ad79f19057fd52e983f6479d9fd5921443e0f78` is complete for the findings above. This statement is not a certification: the documentation commit containing this section and any later remediation must pass the exact-head gate matrix below.

## Current freeze gate

V1-08 remains BLOCKED until the exact current remediation HEAD has:
1. targeted auth/media/upload/runtime tests green;
2. general CI green;
3. Windows dependency/runtime gates green;
4. PostgreSQL Alembic certification green;
5. no new BLOCKER/MUST-FIX from the final exact-head Pass 3 read;
6. canonical Notion/roadmap/audit synchronization.

No real cabinet mutation and no Vercel deployment are authorized.
