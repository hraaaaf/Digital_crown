# PC-07 — Emergency Photo — Adversarial Review

Status: IMPLEMENTATION CANDIDATE — MACHINE GATES PENDING
Branch: feature/patient-companion-pc07-emergency-photo
PR: #648 DRAFT
Deployment: none

## Review question
Can Patient Companion accept an emergency photo without creating a second media source of truth, exposing clinical plaintext outside the trusted cabinet boundary, misbinding tenant/patient ownership, duplicating assets on retry, or claiming receipt before durable cabinet acknowledgement?

## Verified by code inspection

### 1. Canonical media truth
PASS by inspection.
- final persisted media uses `ClinicalAsset` / Media Core;
- no PC-07 canonical media table or public object store exists;
- final asset uses `PHOTO` + `DEVICE_CAPTURE`;
- Media Core encrypted storage remains the final clinical storage boundary.

### 2. Remote transport architecture
PASS by inspection.
- relay v1 limit remains 256 KiB;
- PC-07 uses `begin/chunk/finalize`, not one oversized command;
- every chunk still travels inside the existing signed + encrypted remote envelope;
- remote worker dispatch is allow-listed by `emergency_photo.*`;
- success remains cabinet-authoritative.

### 3. Tenant / patient binding
PASS by inspection.
- patient/tenant are derived from active `PatientCompanionAccess`;
- remote payload does not accept patient_id/employer_id;
- temporary uploads are scoped by access + employer + patient.

### 4. Image safety and privacy
PASS by inspection.
- client redraws/re-encodes to JPEG before local queueing;
- server revalidates and normalizes with shared M6-A clinical-photo rules;
- JPEG/PNG/WebP source validation remains bounded;
- EXIF/location metadata is removed before canonical persistence;
- no LLM or image interpretation exists.

### 5. Local patient-device storage
PASS by inspection.
- image bytes do not enter the monolithic JSON wallet;
- dedicated IndexedDB media store is AES-GCM encrypted with the device key;
- AAD binds access_id + upload_id;
- queue metadata remains bounded in the main encrypted state;
- wallet sync preservation was corrected so normal sync does not erase PC-07 queue metadata.

### 6. Cabinet temporary assembly
PASS by inspection after hardening.
- temporary chunks are encrypted at rest with AES-GCM;
- assembly key is HKDF-derived from cabinet key material;
- AAD binds access + upload + chunk index;
- stored chunk DB bytes are not plaintext;
- expired unfinished uploads are purged globally on PC-07 activity;
- active unfinished uploads are capped per access.

Residual limitation:
- cleanup is opportunistic on PC-07 activity; there is no separately scheduled garbage-collector job in this lot. Expired objects are unusable after expiry checks, but physical deletion during complete inactivity is not independently scheduled.

### 7. Ordering / retry / idempotency
PASS by inspection.
- out-of-order chunks are accepted safely;
- duplicate identical chunks are idempotent;
- conflicting duplicate chunks are rejected;
- resume reports only the contiguous received prefix;
- missing chunks block finalization;
- object size + full SHA-256 must match before image processing;
- finalized upload stores asset_id and returns the same authoritative result on repeat finalization.

### 8. Receipt truth
PASS by inspection.
Allowed states:
- local_pending;
- remote_uploading;
- remote_pending_ack;
- received;
- rejected.

`received` is set only after `finalize` returns signed cabinet ACK with a committed canonical asset.
A relay/network timeout remains pending/unconfirmed.

## Automated proofs present in candidate
- exact patient binding + metadata stripping;
- out-of-order reconstruction;
- duplicate chunk idempotency/conflict;
- missing chunk rejection;
- object digest mismatch rejection;
- cross-access isolation;
- repeated finalization idempotency;
- injected contract rejection;
- contiguous-prefix resume;
- real JOSE size proof for 96 KiB raw chunk under relay 256 KiB limit;
- temporary chunk ciphertext != plaintext;
- active-upload quota;
- global expiry purge;
- M6-A normalizer regression;
- frontend pending/ACK truth tests;
- production build gate;
- Alembic graph gate.

## Visual proof plan
BEFORE:
- master base, PC-07 surface absent;
- Chromium + WebKit;
- 360x800 + 390x844.

AFTER:
- idle;
- preview;
- pending/unconfirmed;
- same browsers/viewports;
- >=44px controls;
- no horizontal overflow;
- no false receipt claim.

Success state is not fabricated by visual harness. It is covered by the authoritative-ACK frontend test.

## Machine gates still open
At this review revision, exact-head results are still pending for:
- PC-07 Emergency Photo Certification;
- PostgreSQL Alembic Schema Certification;
- Patient Companion Remote Transport Gate;
- CI;
- PC-07 BEFORE Visual Evidence;
- PC-07 AFTER Visual Evidence;
- triggered regression workflows.

No numeric visual score and no merge readiness are claimed before those proofs are green and artifacts inspected.

## Human gate
Human visual approval remains mandatory before READY/merge.

## No deployment
No Vercel deployment is authorized or claimed.
