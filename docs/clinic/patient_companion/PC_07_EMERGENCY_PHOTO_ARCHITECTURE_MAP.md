# PC-07 — Emergency Photo — Architecture Map

Status: AUDIT COMPLETE — ARCHITECTURE LOCKED BEFORE IMPLEMENTATION
Branch: feature/patient-companion-pc07-emergency-photo
Base audited: master@b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2
Deployment: none

## Goal
Allow a Patient Companion user to capture and transmit an emergency clinical photo without creating a second media source of truth, without leaking clinical plaintext to the relay, and without claiming delivery before durable cabinet acknowledgement.

## Verified existing primitives

### Canonical clinical media store
`ClinicalAsset` / Media Core is the canonical patient media registry.

Verified:
- tenant authority = `employer_id`;
- patient binding = `patient_id`;
- `PHOTO` and `DEVICE_CAPTURE` already exist;
- physical bytes are AES-GCM encrypted;
- storage keys are opaque and tenant-scoped;
- no public storage URL is required;
- integrity is verified on read with AES-GCM + SHA-256.

Decision:
PC-07 MUST persist the final cabinet copy into Media Core. No second media table or storage plane.

### Secure image validation
Generic Media Core ingestion validates signature/parser, MIME consistency, byte/dimension limits and derives a clean thumbnail.

Important limitation:
generic Media Core ingestion preserves the original validated image bytes. The original EXIF metadata can therefore survive.

### Proven clinical-photo normalization
Mobile M6-A already proves the stricter boundary needed for PC-07:
- JPEG / PNG / WebP only;
- max raw payload 12 MiB;
- max 50 MP;
- parser verification;
- EXIF orientation normalization;
- conversion to RGB;
- rewrite to JPEG quality 95;
- original metadata removed;
- final Media Core source kind `DEVICE_CAPTURE`.

Decision:
extract/reuse this normalization behavior as a shared service. PC-07 must never persist the patient-device original with EXIF/location metadata.

### Patient Companion Remote Transport
Verified:
- sign-then-encrypt: ES256 JWS inside ECDH-ES+A256KW / A256GCM JWE;
- relay stores opaque ciphertext only;
- replay/idempotency receipts exist;
- active access/key checks fail closed;
- cabinet signed/encrypted ACK is the only authoritative result.

### Relay hard limit
`RELAY_MAX_BLOB_BYTES = 256 * 1024`.

The canonical Remote Transport gate explicitly states:
**future large media transfer (PC-07) requires a separate chunked encrypted-object design; do not raise the message limit casually.**

Decision:
PC-07 MUST NOT send a full photo through the ordinary one-envelope `sendRemoteCommand()` path and MUST NOT increase the relay limit.

### Current Patient Companion local vault
Current vault is one AES-GCM encrypted JSON state envelope rewritten as a whole on mutation.

Verified gap:
there is no dedicated binary/media object store.

Decision:
do not base64 multi-megabyte media into `PatientCompanionVaultState`.
PC-07 needs separate encrypted IndexedDB media-object/chunk storage; the main vault keeps only bounded metadata/state.

## Rejected architecture

### Single-envelope compressed photo
REJECTED.

Reason:
- contradicts the already-approved Remote Transport gate for PC-07;
- couples clinical image quality to an arbitrary 256 KiB relay ceiling;
- encourages aggressive browser-side compression as a transport workaround;
- leaves little safety margin for JOSE/base64 overhead;
- does not generalize cleanly to reliable retry/resume.

### New SaaS/public object storage
REJECTED.

Reason:
would introduce a second clinical media data plane and violate local/on-prem doctrine.

### Public/presigned clinical-media URL
REJECTED.

Reason:
creates a bearer-media exposure surface and bypasses the approved opaque-relay architecture.

## Locked architecture

### A. Capture
Patient selects camera/picker using mobile browser capabilities.

Flow:
1. select/capture;
2. local preview;
3. explicit confirmation;
4. enqueue secure upload.

No diagnosis, LLM, computer vision or clinical interpretation.

### B. Local pending object
Generate opaque `upload_id` UUID.

Main vault stores bounded metadata only:
- upload_id;
- access_id;
- state;
- created_at / updated_at;
- byte size;
- MIME;
- retry/error code;
- canonical cabinet asset reference only after ACK.

Binary bytes live in a dedicated encrypted IndexedDB media store.

Required states:
- `local_pending`
- `remote_uploading`
- `remote_pending_ack`
- `received`
- `rejected`

No transition to `received` before signed cabinet ACK.

### C. Local privacy normalization
Before durable local queueing/transmission:
- decode image;
- apply visual orientation;
- redraw/re-encode to a metadata-free JPEG;
- keep image quality clinically usable;
- do not optimize merely to fit one relay envelope.

This is a privacy/preparation layer only.
Server-side validation and normalization remain mandatory.

### D. Chunked encrypted-object protocol
PC-07 adds a media-object protocol separate from ordinary remote commands.

Every relay-visible envelope remains the existing opaque object:
- envelope_id;
- blob;
- relay timestamps/expiry.

All clinical routing/object metadata stays inside JWE.

Inside encrypted payload, chunks carry at minimum:
- protocol/version;
- upload_id;
- chunk index;
- total chunk count;
- plaintext object byte size;
- object digest;
- chunk digest;
- chunk payload;
- idempotency identity;
- access binding.

Requirements:
- every final compact JWE stays below 256 KiB;
- exact plaintext chunk size is derived/tested from real JOSE overhead, not guessed;
- chunks may arrive out of order;
- duplicate chunks are idempotent;
- missing chunks cannot finalize;
- malformed/digest-mismatched chunks fail closed;
- partial assemblies expire and are garbage-collected;
- relay never sees patient/tenant/access/media identifiers in plaintext.

### E. Cabinet assembly
Cabinet maintains bounded temporary assembly state keyed by opaque upload/idempotency identity and access scope.

Before accepting a chunk:
- access active;
- remote keyset active;
- signature/decryption valid;
- chunk metadata structurally valid;
- declared limits bounded.

Finalization happens only when:
- all expected chunks exist;
- chunk digests validate;
- reconstructed byte count matches;
- full object digest matches.

No partial ClinicalAsset is created.

### F. Canonical commit
After complete authenticated reconstruction:
1. derive tenant/patient from active `PatientCompanionAccess`;
2. run shared M6-A-grade image parser/normalizer;
3. ingest into canonical Media Core:
   - `asset_type=PHOTO`
   - `source_kind=DEVICE_CAPTURE`
   - `source_ref=PATIENT_COMPANION_EMERGENCY_PHOTO`;
4. record bounded provenance;
5. commit canonical asset + idempotent final result transactionally where possible;
6. clear temporary assembly;
7. return signed/encrypted ACK.

### G. ACK truth
Relay upload completion is not clinical receipt.

Only a signed cabinet ACK after successful Media Core commit may set UI state:
`received` / “Photo reçue par le cabinet”.

Timeout/network loss:
- remains pending/unconfirmed;
- retry uses same upload/idempotency identity;
- duplicate finalization returns original authoritative result where safe;
- no second ClinicalAsset.

### H. Revocation
If access is revoked:
- reject new chunks/finalization;
- do not create new canonical asset;
- local pending bytes cannot be remotely erased;
- already-created Media Core asset follows cabinet lifecycle, not Patient Companion revocation.

## Security constraints
- no patient_id/employer_id in relay-visible metadata;
- no public media URL;
- no raw cabinet filesystem exposure;
- no Firebase/SaaS plaintext media plane;
- no WhatsApp photo transport;
- no LLM/image analysis;
- no optimistic receipt state;
- strict parser validation after reassembly;
- EXIF/location metadata stripped before canonical storage;
- chunk/object limits bounded;
- temporary assemblies expire;
- final asset idempotent.

## Goal / Success / Proof

### Goal
Transmit one emergency patient photo from Patient Companion to canonical cabinet Media Core through the approved opaque relay while preserving privacy, ownership, idempotency and truthful delivery state.

### Success
Observable when:
1. capture/preview/confirm works on mobile;
2. local queued bytes are encrypted separately from the main JSON vault;
3. relay sees ciphertext only;
4. every envelope stays under 256 KiB;
5. out-of-order/missing/duplicate chunks cannot create partial/duplicate assets;
6. cross-patient/cross-tenant attempts fail;
7. revoked access fails closed;
8. EXIF/location metadata does not persist in canonical stored bytes;
9. exactly one canonical Media Core asset exists after successful finalization;
10. UI says received only after signed cabinet ACK;
11. interrupted upload is resumable/pending without false success;
12. target mobile viewports have no overflow and >=44px actions.

### Proof
Required:
- chunk protocol unit tests;
- real JOSE envelope-size boundary tests;
- assembly ordering/missing/duplicate tests;
- assembly expiry/cleanup tests;
- idempotent finalization tests;
- tenant/patient/revocation tests;
- malformed/oversize/invalid image tests;
- EXIF/GPS stripping test on canonical stored bytes;
- local encrypted media-store tests;
- frontend pending/received truth-state tests;
- BEFORE / target / AFTER on Chromium + WebKit, 360x800 and 390x844;
- exact-head CI + Remote Transport regression;
- adversarial review;
- human visual approval before merge.

## Next exact
1. extract M6-A clinical-photo normalization into a shared service;
2. define encrypted local media-object store;
3. define/test chunk sizing under actual JOSE overhead;
4. implement cabinet temporary assembly + finalization;
5. implement Patient Companion capture/queue/status;
6. certify exact-head + visual.

No Vercel deployment.
