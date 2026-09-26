# V1-07 — Pre-freeze Triple-Check Audit

Status: **READY FOR MERGE — EXACT-HEAD CERTIFIED / POST-MERGE PENDING**

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

Original finding: media paths could fail open when DB provenance was absent/ambiguous; legacy acte attachments and clinic branding needed the same tenant proof.

Current remediation re-check:
- `_assert_media_tenant` returns 404 when provenance is missing and 403 when ownership is foreign/ambiguous;
- legacy acte attachments require an owning `Acte → Patient → employer_id` chain and fail closed when absent;
- clinic branding resolves the authenticated employer's `CabinetConfig` and requires the requested first path segment to equal that cabinet's `public_id`;
- orphan panoramic/acte, document preview-token and clinic-source contracts exist in `backend/tests/test_media_security.py`.

Status: **REMEDIATED IN CODE/TEST — EXACT-HEAD CERTIFICATION PENDING**.

### BLOCKER — cabinet HTTP/LAN exposure with non-Secure cookies

Original finding: packaged/controlled cabinet runtime could expose plain HTTP on LAN and cabinet cookies were not guaranteed Secure.

Current remediation re-check:
- packaged first boot writes `CABINET_HOST=127.0.0.1`;
- cabinet/production non-loopback bind is refused unless HTTPS is explicitly enabled;
- HTTPS requires an existing cert/key pair and is wired into uvicorn;
- controlled real launcher binds `0.0.0.0` only when the HTTPS contract is enabled, otherwise loopback;
- cabinet auth cookies become Secure when cabinet HTTPS is enabled;
- `test_mobile_https_runtime_contract.py` locks the runtime/LAN contract.

Status: **REMEDIATED IN CODE/TEST — EXACT-HEAD CERTIFICATION PENDING**.

### MUST-FIX — Google OAuth state/CSRF binding missing

Original finding: Google authorize/callback lacked state binding.

Current remediation re-check:
- authorize emits a cryptographically random `secrets.token_urlsafe(32)` state;
- state is bound to a 300-second HttpOnly, SameSite=Lax cookie;
- callback requires cookie + query state and compares them with `hmac.compare_digest` before token exchange;
- every failure branch and the successful callback clear the state cookie;
- `test_google_oauth_https_runtime_contract.py` now covers authorize binding, mismatch, missing state and successful one-shot consumption.

Status: **REMEDIATED IN CODE/TEST — EXACT-HEAD CERTIFICATION PENDING**.

### MUST-FIX — cabinet certification dependency drift

Original finding: cabinet certification mixed incompatible torch/vision/audio pins.

Current remediation re-check:
- `cabinet-release-certification.yml` installs torch 2.10.0 / torchvision 0.25.0 / torchaudio 2.10.0 together;
- all three are excluded before installing the remaining requirements;
- `python -m pip check` is mandatory.

Status: **REMEDIATED IN WORKFLOW — FINAL CABINET CERTIFICATION PENDING**.

### MUST-FIX — competing V1 objective documents

Original finding: root and clinic objective files could compete for V1 authority.

Current remediation re-check:
- `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md` is the sole canonical objective;
- root `DIGITALCROWN_V1_OBJECTIVE.md` explicitly declares itself a **NON-AUTHORITATIVE POINTER**;
- it points to the canonical objective and the consolidated execution roadmap and carries no independent candidate/gate state.

Status: **REMEDIATED IN DOCUMENT CONTRACT — FINAL DOC COHERENCE CHECK PENDING**.

### MUST-FIX — implicit Sentry cloud observability

Original finding: frontend Sentry initialized whenever `VITE_SENTRY_DSN` existed, independent of the explicit telemetry opt-in. Backend Sentry was already guarded by `TELEMETRY_ENABLED`.

Remediation on PR #633:
- frontend Sentry now requires both exact `VITE_TELEMETRY_ENABLED=true` and a non-empty `VITE_SENTRY_DSN`;
- DSN-only configuration fails closed;
- preview and Patient Companion exclusions remain intact;
- `frontend/src/telemetryPolicy.g8Interactive.test.ts` locks the fail-closed matrix;
- `frontend/.env.example` documents telemetry OFF by default.

Status: **REMEDIATED IN CODE/TEST — EXACT-HEAD CERTIFICATION PENDING**.

### MUST-FIX (low) — raw health exception disclosure

Original finding: unauthenticated health failures could expose raw DB/storage exception strings.

Current remediation re-check:
- `/api/health/db` and `/api/health/storage` already returned generic external errors and logged details server-side;
- residual `/health` leakage was found during this triple-check and fixed on PR #633;
- `/health` now logs the exception server-side and returns only `{"status":"degraded","db":"error"}`;
- `test_root_health_error_does_not_expose_exception_detail` injects a credential-bearing connection string and proves it is absent from the response.

Status: **REMEDIATED IN CODE/TEST — EXACT-HEAD CERTIFICATION PENDING**.

### REVIEW — Firebase pending_clients onboarding

Re-check result: cloud onboarding is restricted to identity/licensing metadata only: email, display name, pending status and timestamp. Phone, full address, local DB id and password material remain local. `test_signup_pending_clients_cloud_payload_is_minimized` now locks this allow-list/deny-list contract.

Status: **REVIEW RESOLVED / REMEDIATED — EXACT-HEAD CERTIFICATION PENDING**.

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

`2ad79f19057fd52e983f6479d9fd5921443e0f78` is a **historical remediation checkpoint only**. Later adversarial findings/remediations (including frontend telemetry opt-in, root health redaction, OAuth one-shot proof and Firebase payload contract) supersede it. No SHA is certified by this paragraph; only the final exact-head gate matrix below can certify the candidate.

## Current freeze gate

V1-08 remains BLOCKED until the exact current remediation HEAD has:
1. targeted auth/media/upload/runtime tests green;
2. general CI green;
3. Windows dependency/runtime gates green;
4. PostgreSQL Alembic certification green;
5. no new BLOCKER/MUST-FIX from the final exact-head Pass 3 read;
6. canonical Notion/roadmap/audit synchronization.

No real cabinet mutation and no Vercel deployment are authorized.


### Pass 3 — V1-05 Ortho Journey re-audit residual

A dedicated V1-05 double/triple check found one additional pre-freeze MUST-FIX in F5: the backend engineering-preview gate previously trusted only `DIGITAL_CROWN_F5_ENGINEERING_PREVIEW=1` and did not enforce that the runtime itself was an engineering environment. The service wording already said engineering-only, so cabinet/production exposure through accidental configuration was inconsistent with the intended fail-closed boundary.

Remediation on branch `audit/v1-05-ortho-triple-check-f5-gate`:
- F5 preview now requires `ENVIRONMENT` in `development | local | test` plus the explicit preview flag;
- cabinet, production, and missing environment deny the preview even when the flag is set;
- regression coverage locks this behavior.

Canonical dedicated audit: `docs/clinic/audits/V1_05_ORTHO_JOURNEY_DOUBLE_TRIPLE_CHECK_2026-09-19.md`.

The F5 gate is now present on the synchronized audit branch: `engineering_preview_enabled()` requires `ENVIRONMENT` in `development | local | test` plus the explicit preview flag. It remains uncertified until the final exact-head gates are green.


## Final pre-merge certification — 2026-09-26

Exact-head certification on `0354bf6828e98ec50ec7afdef95941f621eb335b`:
- GitHub Actions matrix: **28 SUCCESS / 2 SKIPPED / 0 FAILURE / 0 active**.
- Patient P7 Final Certification `36205720352` — **SUCCESS**.
- V1-07 G3 Browser Action Certification `36205720410` — **SUCCESS**.
- V1-07 G1 Browser Action Certification `36205720287` — **SUCCESS**.
- CI `36205720407` — **SUCCESS**.
- T2 Runtime Browser Certification `36205720468` — **SUCCESS**.
- Catalog Connected Truth Certification `36205720217` — **SUCCESS**.
- PostgreSQL Alembic Schema Certification `36205720590` — **SUCCESS**.
- Windows Build Dependency Contract `36205720419` — **SUCCESS**.
- Exact UI proof retained at 390×844 / 768×1024 / 1280×900 with zero horizontal overflow; no new 390 regression versus retained baseline.
- Real cabinet port 8005 was not mutated.

Pass 1 findings are classified, Pass 2 corrections are rechecked, and Pass 3 residual findings required for V1 are remediated on the certified exact head. No unresolved V1 BLOCKER/MUST-FIX is known on this PR head. V1-08 remains blocked until merge and post-merge master certification are complete.
