# PC-08 — Secure Messaging — Architecture Map

Status: AUDIT COMPLETE — ARCHITECTURE LOCKED BEFORE IMPLEMENTATION
Date: 2026-09-22
Branch: `feature/patient-companion-pc08-secure-messaging`
Base audited: `master@f96f7abee2fb1994b3ac72ef00603a704961e59b`
Deployment: none

## Goal

Allow a Patient Companion access and the owning cabinet to exchange bounded text messages through the already-certified Patient Companion trust boundary, while keeping the cabinet database authoritative, relay-visible content opaque, local patient data encrypted, access isolation exact, retries idempotent, and delivery/read labels strictly evidence-based.

PC-08 is asynchronous secure messaging, not a realtime-chat claim.

## Verified existing primitives

### Patient Companion identity and authorization

Verified:
- `PatientCompanionAccess` binds exactly one external identity to one `employer_id + patient_id`;
- relationship types include `SELF`, `PARENT`, `GUARDIAN`, `CAREGIVER`;
- `principal_for_access()` fails closed for revoked access or deleted patient;
- staff Companion administration is limited by `require_companion_admin()` + `patients` permission;
- D2 exposes the Companion surface only to owner/admin-equivalent staff.

Decision:
**one secure message thread is scoped to one `PatientCompanionAccess`, not merely one patient.**
Different patient/parent/guardian/caregiver accesses MUST NOT share a thread implicitly.

### Access revocation

Verified:
- access revocation sets `PatientCompanionAccess.revoked_at`;
- active remote keysets become `REVOKED`;
- active relay binding becomes `REVOKE_PENDING`;
- relay worker later deprovisions both mailboxes and marks the binding revoked;
- already cached patient-device data is not remotely erased.

Decision:
PC-08 MUST reject new send/sync/receipt operations once access is revoked. Existing canonical cabinet messages remain cabinet records; PC-08 makes no remote-delete claim.

### Certified remote transport

Verified:
- ES256 JWS inside ECDH-ES+A256KW / A256GCM JWE;
- patient private keys remain device-side; cabinet private keys are OS-protected;
- relay outer envelope is opaque and carries no patient/tenant/access/operation plaintext;
- `RELAY_MAX_BLOB_BYTES = 256 KiB`;
- application command lifetime is at most 15 minutes;
- remote worker validates signature, access, keyset and freshness before domain code;
- durable `PatientCompanionRemoteReceipt` enforces replay/idempotency;
- signed/encrypted `command.result` ACK is authoritative;
- relay timeout remains pending and is never shown as accepted.

Decision:
PC-08 MUST reuse `message.*` operations through this worker. No second crypto protocol, public API gateway, Firebase clinical plane, WhatsApp transport or SaaS message store.

### Relay worker and outbox

Verified:
- cabinet owns READ capability for cabinet inbox and WRITE capability for patient inbox;
- patient owns WRITE capability for cabinet inbox and READ capability for patient inbox;
- current durable relay outbox is explicitly an ACK outbox tied to a source envelope;
- delivered ACK outbox rows are retained for 7 days then removed.

Decision:
PC-08 MUST NOT silently repurpose the ACK outbox as a generic message queue.

The minimal PC-08 transport is **patient-initiated encrypted synchronization**:
1. patient sends `message.sync` through the certified remote-command channel;
2. cabinet returns bounded canonical messages inside the signed/encrypted ACK;
3. patient stores them in its encrypted local vault;
4. patient sends explicit `message.received` / `message.read` commands later;
5. cabinet records receipt/read timestamps only after those commands are accepted.

This gives bidirectional messaging without inventing an unproved server-push engine.

### Remote idempotency

Verified:
- unique `access_id + message_id`;
- unique `access_id + idempotency_key`;
- duplicate message IDs are replay;
- repeated completed idempotency key returns original result;
- same key for a different operation is rejected.

Decision:
Every patient send/read/receipt retry keeps the same persisted local UUID/idempotency identity until terminal ACK. PC-08 also stores a domain-level `client_message_id` unique per access so a message cannot duplicate even if transport-ledger retention changes later.

### Patient local storage

Verified:
- Patient Companion vault is AES-GCM encrypted in IndexedDB;
- device AES key is non-extractable;
- state is scoped by access;
- PC-07 proves encrypted separate binary storage for media.

Decision:
PC-08 text and pending-send metadata live only inside the existing encrypted JSON vault. No plaintext localStorage/sessionStorage. No separate browser database is needed for bounded text.

### Notifications / OS push

Verified:
- staff M6-D2 Web Push is bound to staff `MobilePairedDevice + user + employer`;
- service worker ignores payload content and displays only a generic signal;
- PC-05 explicitly forbids reusing staff push identity as Patient Companion identity;
- no patient OS-push binding is currently certified.

Decision:
PC-08 initial slice has **no patient OS push claim**. No message text, patient name, treatment detail or thread metadata may enter generic OS push payloads.

### Connect Hub

Verified:
- Connect Hub is a cabinet-side read-only aggregation surface;
- current sources are ProactiveAlert and treasury;
- it is not a chat store or messaging inbox;
- it forbids a parallel convenience persistence engine.

Decision:
PC-08 does not turn Connect Hub into a message database. Initial staff messaging lives in the already-authorized Patient Companion panel inside the patient dossier. A future Connect Hub unread projection may read the canonical PC-08 message table without copying message content, but is outside the minimal slice.

### Attachments / PC-07

Verified:
- PC-07 is a purpose-built emergency-photo protocol;
- final photo truth is Media Core;
- it does not define a generic message↔asset attachment contract.

Decision:
**PC-08 initial slice is text-only.**
No attachment bytes, photo reuse, document copy or public link is added. A future attachment slice must reference canonical share/Media Core records and receive its own audit.

### Audit

Verified:
- remote worker already writes one `PATIENT_COMPANION_REMOTE_COMMAND` AuditLog entry per terminal remote command, without message body;
- D0/D2 staff actions use canonical AuditLog;
- message content must not be copied into audit-log details.

Decision:
PC-08 adds specific bounded audit events for staff send/read where useful, while message text remains only in the canonical message row. Transport failures that never reach the cabinet remain preserved in the encrypted patient pending queue rather than being falsely audited server-side.

### Rate limiting / abuse

Verified gap:
- generic `check_rate_limit()` is 5 attempts / 10 minutes keyed by scope + client IP;
- this policy is suitable for pairing/activation abuse protection but is too coarse to define usable messaging cadence;
- relay additionally limits active envelopes per mailbox but does not provide the PC-08 application abuse policy.

Decision:
do not reuse the 5/10-minute helper as the message-product limit.
PC-08 implements two distinct controls: a persistent per-access patient send bound of **60 new messages per rolling hour**, plus a transport-abuse ceiling of **240 authenticated PC-08 remote commands per 10 minutes per access + client IP** using the shared limiter with a PC-08-specific maximum. Idempotent retries of an already-stored `client_message_id` return the original result and do not consume an additional message-send slot. Existing domains keep the shared limiter default of 5 attempts / 10 minutes unchanged.

### Retention / deletion / evidence

Verified gap:
- no canonical secure-message retention period or medico-legal export policy exists in the current Patient Companion code;
- Evidence Pack is not a PC-08-certified export path.

Decision:
PC-08 initial slice exposes **no edit/delete/unsend/archive API** and makes no legal-retention-duration claim.
Canonical message rows remain part of cabinet truth under the existing cabinet DB lifecycle/backups. A later retention/export policy requires a separate explicit contract.

## Locked minimal product contract

### A. Thread identity

Thread key = one active `PatientCompanionAccess`.

Every query/mutation additionally matches:
- `employer_id`;
- `patient_id`;
- `access_id`.

No thread lookup may be authorized by patient ID alone.

### B. Canonical message record

Add one narrow cabinet model: `PatientCompanionMessage`.

Required fields:
- opaque `public_id` UUID;
- `access_id`;
- `employer_id`;
- `patient_id`;
- `client_message_id` UUID, unique per access;
- `sender_kind = PATIENT | STAFF`;
- nullable `sender_user_id` for staff attribution;
- immutable text `body`;
- `created_at`;
- nullable `staff_read_at` + `staff_read_by_user_id`;
- nullable `patient_received_at`;
- nullable `patient_read_at`.

No copied thread title, notification body, delivery-status enum or attachment blob.

Status is derived from evidence timestamps, not dual-written as an independent truth.

### C. Message body boundary

New PC-08 contract:
- text only;
- trim surrounding whitespace;
- reject empty body;
- maximum **4096 UTF-8 bytes** after normalization;
- no HTML interpretation; render as text;
- no LLM generation, analysis or summarization.

Rationale:
20 maximum-size messages remain safely below the 256 KiB encrypted-relay ceiling with JOSE overhead; exact envelope-size test is mandatory before closeout.

### D. Patient → cabinet send

Operation: `message.send`.

Encrypted payload:
- `client_message_id`;
- `body`.

Rules:
1. active access/keyset required;
2. validate body boundary;
3. unique access + client_message_id;
4. persist exactly one canonical row with `sender_kind=PATIENT`;
5. return opaque message id + canonical timestamp;
6. commit message + remote receipt atomically through the existing worker transaction;
7. only signed `ACCEPTED` ACK changes local state to “Reçu par le cabinet”.

Offline/timeout:
- encrypted vault keeps `local_queued` or `remote_pending`;
- retry reuses client/idempotency identity;
- no false success.

### E. Cabinet → patient send

Staff route is patient-dossier scoped and reuses D2 authorization:
- owner/admin Companion authority;
- `patients` permission;
- exact tenant/patient check;
- explicit target access when multiple accesses exist.

Staff supplies a generated `client_message_id` for idempotent retry.

Successful API response means only:
**stored by the cabinet**.

It MUST NOT be labelled delivered/read.

### F. Patient secure sync

Operation: `message.sync`.

Rules:
- encrypted remote command only when relay mode is used;
- default sync returns the latest 20 messages for this access in chronological order on every refresh, so receipt/read timestamps of already-known recent messages are reconciled truthfully;
- older history uses an optional opaque `before_message_id` cursor and returns up to 20 earlier rows;
- maximum 20 rows per response;
- body stays inside encrypted ACK;
- cross-access cursor is rejected;
- response includes only fields required by patient UI and receipt truth.

If older data exists, patient may continue backward with the returned opaque cursor. No forward-only cursor is used because it would miss later read/receipt state changes on already-synchronized messages. Envelope-size boundary is tested with 20 × 4096-byte bodies.

### G. Authoritative receipt/read semantics

No optimistic status.

For STAFF messages:
- `patient_received_at`: set only by accepted `message.received` command after the patient client has successfully decrypted and durably stored the message locally;
- `patient_read_at`: set only by accepted `message.read` command when the patient has actually opened/seen the thread.

For PATIENT messages:
- `staff_read_at`: set only by authenticated staff action when the thread is opened/marked read.

Labels:
- patient outbound before ACK: “En attente”;
- patient outbound after send ACK: “Reçu par le cabinet”;
- patient outbound after staff read timestamp: “Lu par le cabinet”;
- staff outbound after cabinet persistence: “Envoyé depuis le cabinet” or equivalent non-delivery wording;
- staff outbound after patient_received_at: “Reçu sur l’appareil”;
- staff outbound after patient_read_at: “Lu”.

No “delivered” wording without the corresponding authoritative receipt timestamp.

### H. Patient local queue/cache

Encrypted vault adds per-access secure-message state:
- canonical cached messages;
- pending outbound messages;
- queued receipt/read acknowledgements;
- last sync cursor.

Pending states are explicit:
- `local_queued`;
- `remote_pending`;
- `accepted`;
- `rejected`.

Failed sends remain locally visible until retry or explicit local discard. Local discard is not remote/canonical deletion.

### I. Staff UX

Insertion point:
`/patients/:id -> PatientDetails -> Companion -> PatientCompanionPanel`.

Initial staff UI:
- access selector only when >1 active access;
- relationship label visible;
- chronological thread;
- message composer;
- explicit non-realtime copy if patient has not synced;
- receipt labels derived only from canonical timestamps.

No global inbox is claimed in PC-08 initial slice.

### J. Patient UX

Add “Messages sécurisés” to Patient Companion home.

Requirements:
- usable at 360×800 and 390×844;
- message body wraps without horizontal overflow;
- composer/actions >=44 px;
- queued/offline state explicit;
- no clinical auto-reply;
- no presence/typing indicator;
- no “online” claim;
- no hidden background delivery claim.

### K. Revocation

After access revocation:
- patient send/sync/read/receipt fail closed;
- staff cannot send a new message to the revoked access;
- remote keyset/mailboxes follow existing revocation path;
- canonical historic messages remain cabinet records;
- already-cached device content is not remotely erased.

## Explicit non-scope

PC-08 initial slice does NOT add:
- realtime sockets/presence/typing;
- patient OS push;
- WhatsApp/SMS clinical messaging;
- attachments;
- voice/video;
- message edit/delete/unsend;
- group threads;
- employee/assistant delegation beyond existing Companion D2 RBAC;
- global Connect Hub inbox;
- medico-legal export/retention-duration certification;
- LLM-generated or LLM-interpreted messages;
- Vercel deployment.

## Goal / Success / Proof

### Goal

Deliver one access-isolated, asynchronous, bidirectional secure text thread between Patient Companion and the owning cabinet using the certified remote-command transport and cabinet-local canonical persistence.

### Success

Observable only when all are true:
1. patient send creates exactly one canonical message after verified remote command;
2. retry/replay cannot duplicate a message;
3. staff send is tenant/patient/access scoped and idempotent;
4. different accesses for the same patient cannot see each other's threads;
5. revoked access cannot send, sync or receive new staff messages;
6. patient cache/pending queue remains AES-GCM encrypted locally;
7. relay-visible envelopes contain ciphertext only;
8. 20 maximum-size sync messages remain below 256 KiB final JWE;
9. patient send is not “received” before signed cabinet ACK;
10. staff send is not “received/read” before explicit patient receipt/read commands;
11. patient message is not “read by cabinet” before authenticated staff read mutation;
12. failures remain retryable without false success or duplicate row;
13. no message content enters OS push or AuditLog details;
14. staff and patient UI remain usable with no overflow and >=44 px actions;
15. no attachment/WhatsApp/LLM path is introduced.

### Proof

Required before human gate:
- migration/schema tests on SQLite + PostgreSQL gate;
- backend tests for access/tenant/patient isolation, staff RBAC and revocation;
- send idempotency/replay tests;
- sync cursor and cross-access negative tests;
- explicit received/read truth tests;
- envelope-size boundary test using real JOSE signing/encryption;
- remote transport regression;
- encrypted local vault tests for cache/pending queue;
- frontend tests proving no optimistic received/read state;
- failed/offline retry tests;
- BEFORE → target → AFTER evidence;
- Patient Companion: Chromium + WebKit at 360×800 and 390×844;
- staff Companion surface: same selected baseline/AFTER viewports;
- target↔render comparison + severe visual score;
- exact-head CI/T2/relevant Patient Companion gates;
- independent double check;
- adversarial triple check;
- human visual approval before merge.

## Contradictions / gaps closed by this architecture

- **No existing chat engine** → add one narrow canonical message model only.
- **Connect Hub is read-only** → do not use it as persistence/inbox.
- **No patient push identity** → no push claim.
- **ACK outbox is ACK-specific** → use patient-initiated encrypted sync, not generic outbound repurposing.
- **Multiple relationship accesses** → isolate thread per access.
- **Generic rate limiter unsuitable for chat cadence** → do not equate it with PC-08 product abuse policy.
- **No retention policy** → no deletion/retention-duration claim in PC-08.
- **PC-07 is not a generic attachment contract** → text-only initial slice.

## Next exact

1. capture exact BEFORE baselines before any UI implementation;
2. add PC-08 migration + canonical message model;
3. implement `message.send/sync/received/read` handlers on existing remote worker;
4. implement staff patient-dossier endpoints with D2 RBAC;
5. extend encrypted patient vault + message transport;
6. implement patient/staff UI against locked truth states;
7. run targeted tests and real JOSE size boundary;
8. capture AFTER at identical viewports and compare;
9. exact-head CI + adversarial review;
10. stop at human visual approval gate.

No Vercel deployment.
