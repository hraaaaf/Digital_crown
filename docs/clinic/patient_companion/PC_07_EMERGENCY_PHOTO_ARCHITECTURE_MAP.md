# PC-07 — Emergency Photo — Architecture Map

Status: AUDIT COMPLETE — IMPLEMENTATION PATH LOCKED
Branch: feature/patient-companion-pc07-emergency-photo
Base audited: master@b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2

## Goal
Allow a Patient Companion user to capture and send one emergency photo to the exact cabinet/patient record without creating a second media store, exposing a public URL, or claiming delivery before a durable cabinet ACK.

## Verified existing primitives

### Media Core
Canonical model: `ClinicalAsset`.

Verified properties:
- tenant authority = `employer_id`;
- exact patient binding = `patient_id`;
- `PHOTO` + `DEVICE_CAPTURE` already supported;
- encrypted content-addressed storage with AES-GCM;
- opaque tenant-scoped storage key;
- no patient-identifying filename in physical storage;
- authenticated reads are `private, no-store`;
- storage integrity rechecked with AES-GCM + SHA-256;
- ingestion generates a controlled thumbnail;
- no public media URL is required.

### Existing clinical-photo normalization
M6-A already provides a proven normalization boundary:
- JPEG/PNG/WebP only;
- raw input <= 12 MiB;
- <= 50 MP;
- parser validation through Pillow;
- EXIF orientation normalized;
- output rewritten as JPEG;
- metadata removed by rewrite;
- generated server-side filename;
- Media Core source kind `DEVICE_CAPTURE`.

Important: generic Media Core import validates but preserves original image bytes. PC-07 MUST reuse equivalent M6-A normalization before canonical ingestion so EXIF/location metadata cannot persist accidentally.

### Patient Companion Remote Transport
Verified:
- commands are signed then JWE encrypted;
- relay sees only opaque blob;
- patient private keys are non-extractable;
- durable idempotency receipts exist;
- duplicate retry with same idempotency key returns stored result instead of replaying the domain mutation;
- ACK is signed/encrypted and bound to request operation/message/idempotency key;
- access/key revocation fails closed.

### Relay limit
Verified protocol limit:
- `RELAY_MAX_BLOB_BYTES = 256 * 1024`.
Therefore the relay is a command/control channel, not a generic 12–50 MiB media pipe.

## Rejected architectures

### New media/SaaS object store
REJECTED.
Would introduce a second clinical media data plane and violate local/on-prem doctrine.

### Public/presigned clinical-media URL
REJECTED.
Would create a new bearer-media exposure surface and is unnecessary.

### Send original camera file unchanged through relay
REJECTED.
Typical phone images can exceed the 256 KiB opaque-envelope limit; EXIF may also be retained.

### Chunked multi-envelope photo protocol
DEFERRED / REJECTED for PC-07 V1.
Possible but adds assembly state, ordering, partial-upload cleanup and many new failure modes. The Emergency Photo use case can stay intentionally bounded to a compact single image.

## Locked PC-07 V1 architecture

1. Patient chooses/captures one image from Patient Companion.
2. Browser decodes and redraws the image to a canvas:
   - orientation rendered visually;
   - metadata is not carried into the new JPEG;
   - long edge is bounded;
   - JPEG quality is reduced iteratively when needed.
3. Client builds the normal remote command payload with base64 JPEG.
4. The final signed+encrypted compact JWE size is checked against the relay 256 KiB hard limit before push.
5. If too large, client recompresses and retries preparation locally; no remote mutation has occurred yet.
6. Remote operation: `emergency_photo.submit`.
7. Cabinet remote worker resolves the exact active `PatientCompanionAccess` and dispatches only this allow-listed handler.
8. Handler base64-decodes strictly and re-runs server-side clinical-photo validation/metadata-free JPEG normalization.
9. Handler ingests into canonical `ClinicalAsset`:
   - `asset_type=PHOTO`;
   - `source_kind=DEVICE_CAPTURE`;
   - `source_ref=PATIENT_COMPANION_EMERGENCY_PHOTO`;
   - `created_by=None`;
   - provenance includes Patient Companion channel/access public id, but no diagnosis.
10. Asset creation + idempotency receipt complete in one remote-command transaction.
11. Only the signed/encrypted cabinet ACK allows the UI to show `Photo reçue par le cabinet`.
12. Timeout/network failure remains `Envoi en attente / non confirmé`; never optimistic success.

## Why single-envelope compact photo
This is the shortest architecture that satisfies:
- no second storage plane;
- no public media URL;
- end-to-end encrypted remote transport;
- existing replay/idempotency protection;
- existing Media Core storage/encryption;
- existing server-side photo normalization;
- bounded failure surface.

## Data contract — proposed minimal V1
Request payload:
- `image_b64`: compact JPEG bytes encoded base64;
- `captured_at`: optional ISO timestamp from device, informational only.

Do NOT accept:
- patient_id;
- employer_id;
- storage key;
- filename path;
- diagnosis/clinical interpretation;
- arbitrary MIME type.

ACK result:
- `asset_id`: canonical ClinicalAsset id;
- `received_at`: cabinet receipt time;
- `status`: stable accepted marker.

No media bytes are returned in ACK.

## Truth states
Allowed UI states:
- `À envoyer`
- `Envoi sécurisé…`
- `En attente de confirmation du cabinet`
- `Photo reçue par le cabinet`
- `Échec — réessayer`

Forbidden:
- `Reçue`, `Archivée`, or equivalent before authoritative ACK.

## Security gates
- exact active PatientCompanionAccess;
- exact tenant/patient derived server-side;
- remote keyset active and not revoked;
- strict base64 decode;
- image parser validation;
- server-side metadata stripping;
- Media Core encrypted storage;
- no public URL;
- idempotent retry;
- bounded relay envelope;
- no LLM/vision interpretation.

## Offline behavior
The selected/normalized photo may remain only in transient in-memory UI state for V1 until send succeeds or the user leaves the flow.
PC-07 V1 will NOT introduce a durable offline media queue unless required by implementation testing, because durable binary queueing expands vault/storage lifecycle scope.

If connectivity fails after relay push but before ACK:
- preserve the idempotency key while the page/session remains active;
- retry using the same key;
- server receipt prevents duplicate asset creation.

## Visual target
Mobile-first:
- CTA `Photo d’urgence`;
- capture/picker;
- clear preview;
- `Reprendre` / `Envoyer au cabinet`;
- explicit privacy note: photo sent securely to the cabinet;
- explicit pending and confirmed states;
- no diagnostic wording.

Required evidence:
- 360x800 + 390x844;
- Chromium + WebKit;
- capture/preview/pending/confirmed states;
- controls >=44px;
- zero horizontal overflow.

## Goal / Success / Proof — locked

Goal:
A patient can send one compact emergency photo to the exact cabinet record through the already-certified encrypted remote channel, with canonical Media Core persistence only after cabinet processing.

Success:
- no second ledger/media store;
- no public URL;
- exact tenant/patient binding;
- relay envelope remains <=256 KiB;
- server strips metadata and validates bytes;
- one canonical ClinicalAsset created per idempotency key;
- ACK gates visible success;
- retry cannot duplicate the asset;
- revoked access fails closed;
- mobile UX passes target viewports.

Proof:
- backend handler + idempotency tests;
- invalid/base64/oversize/image tests;
- tenant/revocation tests;
- remote JOSE path test;
- frontend compression/envelope-size tests;
- pending/ACK truth tests;
- BEFORE/AFTER Chromium + WebKit evidence;
- exact-head CI + T2/Remote Transport;
- adversarial review;
- human visual gate.

## Next exact
Implement only this bounded single-envelope V1. Do not add chunking, persistent offline media queue, public uploads, diagnosis or image analysis.
