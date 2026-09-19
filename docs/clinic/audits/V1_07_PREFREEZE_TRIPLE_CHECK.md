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
