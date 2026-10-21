# Digital Crown — V1.5-06 / LOT06-B — Server acquisition receipt & recovery ADR

**2026-10-21 · PROPOSAL / DESIGN-ONLY / HUMAN GATE OPEN / NO-GO clinical.** This is a concrete decision packet, **not an accepted architecture, implemented API, deployable migration or proof of clinical success**. The user's GO authorizes this design step only. No runtime code, service, DB model, workflow, installation, clinic data, SCM or hardware changes are allowed in this PR.

**Immutable starting point:** stacked draft [PR #999](https://github.com/hraaaaf/Digital_crown/pull/999), SHA `fd870a8c54f2f2aa45e065e3260f98f97c613ac2` (itself based on #998 → #909; #996 is a sibling documentation PR). The existing synthetic fixture receipt `LAB_RECEIPT_COMMITTED` is **not** a receipt issued by the clinical backend.

## 0. Canonical basis: what exists versus what is proposed

| Existing source on starting SHA | Verified current contract | Proposed change, **not implemented** |
| --- | --- | --- |
| `tools/imaging_gateway/gateway.py` | Locally encrypted, restartable HotFolder, `.ready` producer manifest and `read_verified`, but no patient inference, server write or ACK | Device-authenticated capture identity and read/transfer handshake; preserve local original until verified backend receipt |
| `backend/routers/imaging_acquisition_preflight_v15.py` + service | TEST-only, bearer/staff/workstation-gated *candidate* resolution; response always `upload_permitted=false`, `server_confirmed=false`, `receipt_id=null` | New explicitly authorized staff confirmation and upload reservation boundary; never elevate this preview to an upload permission |
| `backend/routers/media_core.py` | `POST /api/patients/{patient_id}/assets/import` imports bytes through existing staff WEB_API, returns asset metadata; no logical capture receipt lookup | Separate acquisition-specific endpoint/service with durable capture identity, authorization, receipt and audit. **Do not reuse legacy import as a device ACK.** |
| `backend/services/clinical_asset_ingestion.py` | Validates actual content; `ingest_clinical_asset_bytes` uses SQL nested transaction and returns asset+derivatives; caller commits | Reuse vetted byte validation/storage only *after* authoritative device and staff gates |
| `backend/services/clinical_asset_storage.py` | Tenant-scoped encrypted content-addressed blobs, writes before DB commit; SQL rollback can leave ciphertext orphan | Bounded provisional blob lifecycle + reconciliation, never a fictitious filesystem+SQL atomic transaction |
| `backend/models_media_core.py` | `ClinicalAsset` has tenant, patient, source_kind including `DEVICE_CAPTURE`, SHA, storage binding, provenance; **no unique (tenant, source device, capture) key** | Add separately reviewed acquisition ledger/approval/ticket/receipt schema with unique logical capture identity |
| `tools/imaging_gateway/staff_receipt_lab.py` | TEMP/TEST-only mock staff and capture authority; SQLite receipt+audit atomic in one fixture DB | Provides negative/positive *algorithm* hypotheses only. Not reusable credentials or proof of trusted server ACK |

**Immediate provenance hazard to resolve before a real rollout:** the existing manual import route accepts a client-provided `source_kind` and the ingestion service allows `DEVICE_CAPTURE`. That value **does not attest a device**; a staff-authenticated legacy upload may be labeled as a device capture without cryptographic device proof. Do not infer provenance from `source_kind`. Proposed gate: accept authoritative `DEVICE_CAPTURE` only through the new device-verified acquisition service; evaluate backward compatibility and existing asset labels before restricting the legacy route. No silent reclassification of historical data.

## 1. Trust boundaries and non-negotiable invariants (R)

**R1 — independent principals.** Distinguish (A) *producer device/connector* enrolled and revocable under a scoped tenant/workstation identity, (B) *staff* with a fresh authenticated cabinet session and `patients` access, and (C) *backend* as the only authority for patient/RDV binding, durable asset and receipt. A cookie-only `dc_workstation` pairing is **not** a device certificate. The operator action must originate in a real authenticated UI request; a client boolean `explicit_staff_action=true` is **not** consent.

**R2 — authoritative association.** No implicit “nearest appointment”, filename, source path, last-open chart, empty RDV identity or device-supplied patient claim. Backend must resolve active tenant-scoped `Patient` and active `Appointment`; the appointment must refer to the same patient, or the UI must explicitly record a separately approved patient-only case. Present patient identity/context in an authorized operator UI; reject ambiguity, mismatches, soft deletes, cross-tenant references, revoked staff, revoked station and invalid scope *again* inside the final write transaction. Manual reassignment requires a **new audited correction operation** that never rewrites a committed historical receipt.

**R3 — stable capture identity.** Device/connector produces an **unpredictable immutable capture_id per distinct source generation**, scoped by `tenant_id + enrolled_device_id + source_epoch`. The server binds it to a **server-calculated** SHA-256 of actual verified plaintext bytes, validated media type/length and current capture scope. Two captures with same bytes are distinct when capture IDs differ. Same capture ID with different digest, patient, RDV, device, epoch or approval intent is **409 CONFLICT**, not “duplicate success”. A SHA or `.ready` manifest alone is **not authentication**. Never disclose source path, original filename or PHI in logs, device health or traces.

**R4 — operator and device cannot impersonate each other.** Enrollment requires approved device identity, key rotation/revocation, mTLS/approved LAN transport or equivalent with proof of possession; credential theft, same-SID spool edits, replay and device replacement are separate gates. Staff JWT permission + anti-CSRF/same-site design as appropriate. Narrow request actor: device may submit its own proposed capture or query its own receipt, **not choose/confirm patient**. Staff confirms a server-presented proposal but **cannot invent device attestation**.

**R5 — idempotency and durable ACK.** Within authoritative tenant/capture namespace, exactly one **logical committed acquisition** can bind to one asset and one immutable receipt, regardless of retries, concurrent workers or lost HTTP responses. Blob dedup by digest is not logical capture dedup. Never return `CONFIRMED` on HTTP 200, preflight, an upload ticket, a file rename, an SQLite local receipt or an uncommitted DB row.

**R6 — recovery is fail-closed.** Backend receipt may say `CONFIRMED` only after the SQL transaction atomically persists acquisition ledger status `COMMITTED`, canonical `ClinicalAsset` pointer, approval reference, immutable receipt record, auditable transition and an outbox event; encrypted blob must have already been fsynced/durably renamed and verified, with continuity assumptions independently tested. If verification fails later, mark `BLOCKED_INTEGRITY` / incident instead of returning bytes or fabricating a repaired receipt. A missing or restored-old DB is not “first boot”; cross-node anti-rollback is **separate LOT06-M/N** and not solved by this ADR.

## 2. Proposed authority and API phases — *all endpoints below are design names, NOT deployed routes*

| Phase / conceptual endpoint | Authenticating principal | Durable state / returned capability | Invalid case |
| --- | --- | --- | --- |
| **P0** enrollment / revoke | Cabinet admin (separate ceremony) | Device identity, tenant, source epoch, allowed modalities, credential expiry, revocation audit | Unknown or revoked device → deny, no upload |
| **P1** `POST /api/imaging-acquisitions/proposals` | Device proof-of-possession + transport security | Unique `tenant/device/epoch/capture_id`, digest claim and metadata; status `AWAITING_STAFF`. Proposal is **not** a server-verified image | ID collision with changed digest/scope → 409; malformed / DICOM parser missing → reject |
| **P2** `GET /.../{capture}/review` | Staff session, patients permission, tenant+workstation access | Server-issued short-lived review challenge binding capture revision, proposed patient/RDV and digest. Displays authorized exact identity; no “auto-link” | Missing/ambiguous/deleted/foreign patient or RDV → `AWAITING_HUMAN_LINK`; no ticket |
| **P3** `POST /.../{capture}/confirm` | Real staff action + fresh authenticated session + reviewed challenge; anti-CSRF as appropriate | Commit approval record with actor, patient/RDV, tenant/device/capture/digest, expiry and revision. Mark `APPROVED`. Generate *opaque, narrow, short-lived* ticket bound to same tuple | Replay challenge, wrong actor, changed patient/RDV, privilege loss → deny. Multi-approver collision → 409 |
| **P4** `PUT /.../{capture}/content` | Enrolled device with scoped, single-capture ticket; bounded retries/resume | Stream into **non-public provisional** encrypted staging; server rehashes plaintext, validates full parser/MIME/limits; status `STAGED_VERIFIED` only on durable verified data | Ticket misuse, digest/mime/size mismatch, partial stream, revoked device, expired approval → cleanup/quarantine; no asset |
| **P5** internal `finalize_acquisition` | Backend service, no exposed mutable client flags | Under DB writer/row lock recheck authorization and revision; one SQL transaction for ledger `COMMITTED`, `ClinicalAsset` `DEVICE_CAPTURE`, provenance, receipt, audit, outbox | DB failure → rollback SQL; encrypted staged blob becomes bounded, reconcilable orphan, **not ACK** |
| **P6** `GET /.../{capture}/receipt` | Same enrolled device within tenant/capture scope or authorized staff | `CONFIRMED` only for persisted verified receipt with `receipt_id, tenant_id, capture_id, device/epoch, patient_id, asset_id, server_sha256, revision, state`. Authenticated device must verify expected values before marking local delivery | Not committed → `PENDING/RETRY_LATER/BLOCKED` with opaque non-PHI reason. Never forge a receipt from a blob or local SQLite state |

**Design boundary:** server shall not accept `source_kind=DEVICE_CAPTURE` as caller-authoritative. The acquisition service itself, after verification, sets `DEVICE_CAPTURE` and `ingestion_channel=ENROLLED_DEVICE`, immutable actor/approval/capture revision references. Existing WEB_API stays separate until an explicit compatibility migration plan passes review.

**Ticket semantics:** ticket is a bearer capability scoped to one tenant/device/epoch/capture/digest/review version, short TTL, stored only hashed, bound to authenticated device principal; consumption is **idempotent**, not a second logical commit. Do not hand a permanent upload secret to the staff UI, and do not permit approval/receipt creation by guessing a ticket. Expiry and revocation must be evaluated at the point of **final commit**, not only ticket minting.

## 3. Conceptual schema / required uniqueness (not a migration)

Proposed authoritative DB tables, keys and invariants, *names illustrative*:

- `enrolled_capture_devices`: `(tenant_id, device_id, source_epoch)` primary identity; status, principal fingerprint/version, modality ACL, revocation counter. **Never include private keys in SQL metadata.**
- `acquisition_intents`: unique `(tenant_id, device_id, source_epoch, capture_id)`, immutable `server_intent_fingerprint` (canonical serialized tuple of digest/size/type and proposed association revision), `state`, bounded attempt count, dates. Unique `request_id` within tuple (request_id alone is not enough).
- `capture_staff_approvals`: approval id, immutable tenant/capture key, operator id, patient/RDV, server review nonce hash+version, approval expiry, actor session identity/revocation epoch, explicit event timestamp. Unique consumed review nonce and per-capture active approval version.
- `acquisition_staged_objects`: opaque staging locator, digest, byte size, canonical validated MIME, durability/verification marker and retention deadline; no mutable user-supplied `storage_key` accepted. Separate authorization for cleanup.
- `acquisition_receipts`: unique `(tenant_id, device_id, source_epoch, capture_id)`, unique `asset_id` within committed acquisition, server-generated receipt id, verified server digest, patient/RDV, approval id/version, persisted commit event. **Receipt immutable once committed.**
- `acquisition_audit` + `acquisition_outbox`: append-only event key unique `(tenant_id, capture_id, event_type, revision)`, committed alongside the asset+receipt; consumer delivery may be **at least once**, so outbox consumer must dedup by event id.

**Atomic boundary:** A single SQL transaction can cover acquisition ledger, `ClinicalAsset`, approval consumption, audit and outbox. **There is no atomic transaction across SQL + encrypted media filesystem + workstation spool + remote client.** Blob must be written/verified and parent directory fsync semantics proven before claiming a durable asset. A rollback after blob write may leave an unreferenced encrypted blob; a subsequent reconciler must identify and quarantine/garbage-collect it **only after proving no committed ref**, with retention and restore safeguards. An SQL COMMIT does not by itself prove media durability after power loss.

**Database-specific gate:** SQLite cabinet and PostgreSQL production need separate concurrency/unique/transaction/durability proofs, including SQLCipher if applicable. A unique constraint plus proper serialized transaction is mandatory; application-level “SELECT then INSERT” without a DB uniqueness fence is unsafe.

## 4. State machine — no false success

`NEW → AWAITING_STAFF → APPROVED → RECEIVING → STAGED_VERIFIED → COMMITTED`

Additional terminal/suspension outcomes: `QUARANTINED` (invalid content), `REJECTED` (invalid rights/scope), `CANCELLED` (staff abort), `BLOCKED_INTEGRITY`, `NEEDS_RECONCILIATION`. These are **proposed** status names only. Only the backend's persisted `COMMITTED` plus the exact matching authenticated receipt can transition **the separate local spool** from `PENDING_CONFIRMATION` to a future `SERVER_ACK_VERIFIED` state (not implemented). Any `RECEIVING` / `STAGED_VERIFIED` / `APPROVED` response is **PENDING**, never a media receipt.

Conflict rules:
- Identical request and same immutable intent: return the existing proposal/approval/receipt stage, never create a second.
- Same capture key with different digest, modality or authorized patient/RDV: **409 CONFLICT**, flag incident; a corrected association is a separately authenticated correction flow with history and no silent patient swap.
- Different capture IDs with identical content: **distinct clinical acquisitions**, no logical collapse; content-addressed storage may reuse encrypted bytes under its tenant-specific guarantees.
- Multiple devices/staff race to confirm: writer/unique constraint chooses one approved revision; losing actor receives conflict, not a second asset.

## 5. Crash/timeout/replay recovery algorithm

| Fault boundary | Authoritative evidence after restart | Required next action / NO-GO |
| --- | --- | --- |
| Proposal HTTP response lost, DB insert succeeded | Query capture key under enrolled device identity | Return exact proposal if fingerprint matches; conflict otherwise |
| Staff reviewed candidate, RDV reassigned / patient deleted / staff revoked before final commit | Latest DB patient/appointment/permissions and approval revision | Refuse finalization, invalidate approval/ticket, require new human confirmation; no asset |
| Transfer interrupted before encrypted staging durable | Ticket state + bounded server progress and verified digest | Resume same capture within authorized window or restart staging safely; no asset/receipt |
| Ciphertext staged+verified but SQL fails before COMMIT | Orphan encrypted object, no receipt/asset ledger | Quarantine/reconcile with retention; never count source delivered; prevent use of orphan as authority |
| SQL committed, HTTP ACK lost | Immutable receipt and linked `ClinicalAsset` in DB | `GET receipt` with device auth; return **same** server receipt. Source agent retains local spool until the receipt matches expected scope/digest/patient |
| Process died during SQL transaction | Durable SQL ledger after rollback/commit recovery | If committed, lookup same receipt; if not, resume same capture under valid approval (or reconfirm). Never synthesize receipt from local audit |
| Two concurrent retries / two staff approvals | DB unique index + serializable/locked finalization | Exactly one logical acquisition, one receipt, one commit audit event; other operation 409 or replay of same intent |
| Blob missing/corrupt following a committed DB entry | Verified content read fails, SQL receipt may exist | **BLOCKED_INTEGRITY** and incident; do not return content or claim restored clinical availability; controlled restore with verification |
| Disk-full / permission denied / SQLCipher key unavailable | No verified staging or transaction proof | Fail closed; bounded retry/backpressure; no delete of original, no reset/empty fresh DB |
| Restore old DB but spool/blob state newer, or authority B/C conflict | Cross-store versions + independent trusted checkpoint (not currently implemented) | STOP and human-gated recovery; do not replay old receipt as freshness. LOT06-M/N independent witness/anti-rollback remains separate |
| Ticket expired/revoked during transfer | Current principal, staff/session, tenant, approval and ticket revocation state | Never finalize until renewed authoritative approval/ticket; partial bytes remain quarantined/bounded |
| Manual correction after committed patient misattachment | Immutable original and audited correction chain | Separate privileged operation with review; no destructive rewrite of original receipt; prevent cross-patient access while disputed |

### Deterministic recovery procedure (DESIGN, not runbook approval)

1. Open authoritative DB under approved service identity; **verify continuity marker and key availability**. Refuse creating a fresh ledger when old evidence indicates a prior installation.
2. Scan `PENDING/RECEIVING/STAGED_VERIFIED` within bounded scopes and verify staged ciphertext/metadata against server-side hashes. Query SQL receipt uniqueness *before* resending/rewriting an asset.
3. For committed rows, verify referenced media and link to immutable approval/audit/outbox, and serve **only** authenticated matching receipt. For noncommitted rows, re-evaluate expired approvals and reconcile orphans; no automatic patient assignment.
4. On conflict, missing evidence, rollback, incorrect tenant or unavailable independent trust root: `BLOCKED/NEEDS_RECONCILIATION` plus restricted operational notice; no “success” by timeout or duplicate metadata.
5. Outbox consumers may retry; deduplicate exact event key. Workstation advances its local state **only** after receipt verification and local durable acknowledgement; both sides keep history until recovery invariants and retention are proved.
6. Require separately authorized, evidence-backed backup/restore, corruption, cancellation and disk-full tests **before any clinical feature gate**. No spontaneous GC or clinical deletion during testing.

## 6. Exact negative / proof matrix for a future scoped implementation

| Test ID | Class | Required observed result |
| --- | --- | --- |
| B-S01 | REQUIRED RPG-C/F | Unenrolled/revoked/wrong-tenant device cannot propose, read other device's receipt, mint or use ticket |
| B-S02 | REQUIRED RPG-J/F | Staff without `patients` permission / wrong cabinet / no explicit actual UI action cannot approve |
| B-S03 | REQUIRED RPG-J/F | Patient soft-deleted, RDV null/cross-tenant/reassigned; ambiguous match always HUMAN_REQUIRED, no asset |
| B-S04 | REQUIRED RPG-C/F | Fake SHA, tampered `.ready`, mismatched bytes/MIME/size and spoofed `source_kind=DEVICE_CAPTURE` do not create authoritative provenance |
| B-S05 | REQUIRED RPG-C/F | Staff approval challenge replay/stale revision/expired capability or revoked session refused at **commit** |
| B-S06 | REQUIRED RPG-X/F | Two independent authenticated producer/receiver processes on isolated network; actual bytes delivered, server validates SHA-256 and stores encrypted ClinicalAsset for correct fictitious patient |
| B-S07 | REQUIRED RPG-C/F | 12+ concurrent same capture retries give exactly one asset/receipt/audit commit; different capture same bytes remains separate |
| B-S08 | REQUIRED RPG-X/F | Lost ACK after SQL COMMIT returns **same** immutable receipt on authenticated lookup; local spool not dropped before match |
| B-S09 | REQUIRED RPG-F | Crash after staged blob/before SQL; no false receipt; orphan reconciled under authorized retention |
| B-S10 | REQUIRED RPG-F | Crash after SQL/response lost, restart receiver and sender, verify bytes and receipt; no duplicate |
| B-S11 | REQUIRED RPG-F | Disk full / key unavailable / blob corrupt / DB+spool skew cause bounded `BLOCKED`, no silent reset or altered patient |
| B-S12 | REQUIRED RPG-C/F | Unauthorized correction, cross-patient browse, old token, duplicate device ID, epoch rollback all rejected with no PHI leak |
| B-S13 | REQUIRED RPG-C | SQLite+SQLCipher and PostgreSQL-specific uniqueness, transaction & rollback semantics verified separately when applicable |
| B-S14 | REQUIRED RPG-J | Staff screen AFTER demonstrates exact patient/RDV and actual human approval, no FUE pass inferred from `skipped-non-ui` |
| B-P01 | **DIFFÉRÉ LOT10/10.4** | Real camera/RVG/vendor hardware, LAN and recovery with controlled fictitious patient, human witness |

**RPG limitations:** backend `TestClient` sharing a SQLite fixture is neither a separate device nor a real networked server; a green syntax job is neither SQLCipher/NTFS SCM evidence nor clinical user acceptance. Physical hardware proof stays LOT10/10.4 under the separate HOLD. W01–W12 Windows SCM tests remain **NOT_TESTED**; no "certified" label while missing.

## 7. Decision record / acceptance gate (HUMAN PENDING)

**Proposed direction, not accepted:** acquisition-specific server boundary, deny-by-default, independent staff/device principals, server-calculated bytes digest, durable SQL receipt and outbox, orphan-safe reconciliation, local ACK only from authenticated matching server receipt. Do **not** bolt this on the existing manual import without protecting the provenance and idempotency invariants.

**Human/architecture decisions still OPEN (must be made before migrations or runtime code):**
1. Who issues/revokes actual device credentials, root of trust and key custody; LAN mTLS/pinning, certificate renewal and failure policy? The `dc_workstation` cookie is not enough.
2. Which supported backend DBs and SQLCipher migration/recovery/backup expectations are in scope for cabinet vs production? What unique constraints, schema upgrade rollback and protected encrypted media staging scheme?
3. What exactly constitutes an operator-confirmed Patient/RDV UI event, role, delegation, cancellation and retrospective reassignment? Confirm `DESKTOP_ONLY` product surface; inspect actual mobile exposure only for shared security behavior.
4. Is an RDV mandatory for all modalities or can staff explicitly approve a Patient-only capture with recorded justification?
5. What is the authoritative per-device capture_id/epoch issuer when adapters or a Wi-Fi producer cannot natively sign? No implicit device trust from unprotected `.ready` files.
6. What retention/quarantine/orphan GC and offline mode are acceptable when WAN/LAN/device credentials are unavailable? How to handle misattachment and audit complaints without rewriting history?
7. How do LOT06-M/N's A/B/C durable witness and anti-rollback HUMAN GATE interact with this receipt without pretending SQLite uniqueness supplies independent freshness? No automatic coupling until that architecture is approved.

**Release decision:** `DESIGN REVIEW PENDING / NO IMPLEMENTATION AUTHORIZATION / LOT06 PRODUCT NO-GO`. This ADR is sufficient as a reviewable **design artifact**, not sufficient to claim an integrated sender→receiver journey. The next authorized move is a narrow human acceptance of these decisions and a separate implementation/test PR with real negative tests; explicitly preserve #909/#998/#999 DRAFT and the LOT10/SCM HOLD. No merge, Vercel, clinic update or clinical feature flag.
