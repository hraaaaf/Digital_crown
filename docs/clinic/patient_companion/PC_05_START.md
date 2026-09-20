# Digital Crown — Patient Companion PC-05 — Patient notifications

Date: 2026-09-20
Base: master@`c9cd8e9b1220b7b98691d9889cbb856d0650e40b`
Branch: `feature/patient-companion-pc05-notifications`
PR: #643 — DRAFT
Deployment: none

## Canonical scope

PC-05 — Patient notifications.

Canonical Notion scope:
- appointment reminders;
- pending documents/signatures/questionnaires;
- Companion notifications;
- reuse existing channels when possible;
- success = notifications are idempotent, configurable, and traceable.

## Goal

Expose a patient-safe notification center inside Patient Companion that projects existing canonical domain state (agenda, shared resources, questionnaires, consent requests) without creating a second notification engine or transport.

Patient-side notification mutations (read/snooze/preferences) must reuse the existing encrypted Patient Companion remote-command transport and only become authoritative after a durable cabinet ACK.

## Success

1. One deterministic notification key per canonical source state; repeated reads never create duplicates.
2. Strict `employer_id + patient_id + access_id` isolation; revoked/expired access fails closed.
3. Sources are existing PC-02/PC-03/PC-04/share/agenda records; no duplicated business truth.
4. Read/snooze/preferences are scoped to the Patient Companion access and survive refresh/reload.
5. Remote mutation is idempotent through the existing Patient Companion receipt ledger.
6. UI never shows read/snoozed/configured as accepted before an `ACCEPTED` encrypted ACK.
7. Appointment reminders, newly shared documents, pending questionnaires and pending consents are represented without exposing unrelated staff alerts.
8. No PHI is introduced into OS notification payloads. No real-device delivery claim without physical proof.
9. No second generic notification table, no second crypto/relay protocol, no dual-write.
10. Browser UI remains usable at 360×800 and 390×844 with no horizontal overflow.

## Proof

Required before closeout:
- backend unit/contract tests for deterministic projection, tenant/patient/access isolation, read/snooze/preferences, revoked access and idempotent replay;
- remote-transport tests proving `ACCEPTED`/replayed ACK semantics;
- frontend tests proving pending state is not presented as acknowledged;
- BEFORE + target + AFTER evidence at 360×800 and 390×844, Chromium + WebKit if UI changes;
- exact-head CI;
- independent double check;
- independent adversarial triple check;
- canonical closeout;
- no Vercel deployment.

## Anti-duplication audit

### ProactiveAlert / M6-D1

Verified behavior in `backend/routers/mobile.py`:
- staff/mobile endpoint reads `models.ProactiveAlert`;
- source is tenant-scoped through `employer_id`;
- RBAC filters financial alerts;
- `is_read` and `snoozed_until` are stored on the alert itself.

Why it cannot be reused as the patient receipt store:
- read/snooze state is alert-global rather than per Patient Companion access;
- endpoint is authenticated as a paired staff/mobile user and requires staff `patients` permission;
- serialized alert content includes patient name/title/message and is designed for an authenticated staff cockpit.

Conclusion: reuse canonical business sources and notification policy concepts, but do not repurpose ProactiveAlert state for Patient Companion.

### M6-D2 Web Push

Verified `MobilePushSubscription` binding:
- one subscription belongs to a `MobilePairedDevice`, `user_id`, and `employer_id`;
- service worker renders a fixed generic OS signal and ignores push payload content;
- revoked staff device behavior is fail-closed.

Why direct reuse is unsafe:
- Patient Companion identity/access is not a `MobilePairedDevice` staff user;
- mapping a patient to a staff device/user would violate identity and tenant boundaries.

Conclusion: preserve the generic no-PHI OS-payload doctrine. Do not add patient OS push until a patient-device binding can reuse the same Web Push service safely without identity conflation. PC-05 certification does not claim real-device push delivery.

### Connect Hub

Inherited architecture remains authoritative:
- no second notification engine;
- no second transport;
- no generic parallel persistence;
- no dual-write;
- no simulated-delivered claim.

### Patient Companion remote transport

Verified `PatientCompanionRemoteCommandTransport` + remote worker:
- encrypted/signed commands;
- access binding;
- UUID/idempotency key;
- fresh ACK validation;
- relay pending remains pending;
- durable receipt ledger returns idempotent results.

Decision: all authoritative patient notification mutations will use this transport.

## Persistence boundary

A narrow Patient Companion notification receipt/configuration model is permitted only to store per-access interaction state that existing primitives cannot represent:
- deterministic `source_key`;
- read/snooze timestamps;
- access-scoped notification preferences.

It must not copy notification title/body/domain truth into a generic outbox table.

## UI protocol

UI impact is expected.

Mandatory:
1. BEFORE capture from current Patient Companion home.
2. Target/mockup documented before styling.
3. Implementation.
4. AFTER at the same viewports.
5. Compare + tests + severe visual score.

## Constraints

- ZERO LLM runtime V1.
- Fail closed on patient safety/access.
- Never display delivered/signed/confirmed/read-accepted before durable authoritative ACK where a mutation is involved.
- No Vercel deployment without explicit authorization.
- PC-FINAL remains mandatory after PC-10.


## Certification workflow

Exact-head technical gate: `.github/workflows/pc05-certification.yml`.
This targeted gate runs the PC-05 backend contract tests, frontend ACK truth-boundary tests, and the production frontend build. The PostgreSQL Alembic schema gate and Patient Companion remote transport gate remain complementary repo-wide proofs.


## Current review state

PR #643 is ready for review. Technical certification is required on the exact PR HEAD before visual approval and closeout. Vercel deployment remains forbidden without explicit product-owner authorization.
