# LOT06 Phase2 B06 — Integrating product boundary with a clinical acquisition FUE-I (candidate, 2026-11-04)

## Goal / scope

Single stacked candidate on B05-D1 GREEN LAB commit `705b9951d672d5776cbd22c3633623f4332018fa`, retaining the single [canonical LOT06 Notion](https://app.notion.com/p/3e677c66336281639beae2a946df1483).

**Target clinical journey:** native scanner capture → unassigned encrypted inbox → authenticated staff image preview → dual patient identity markers and explicit acknowledgement → Media Core encrypted ClinicalAsset → durable signed ACK with replay without duplicates.

**What this pass actually implements:** one real correction to the existing LAB review UI: the LAB image preview is fetched through the authenticated Digital Crown API (Bearer/cookies handled by the shared client), checked for exact byte length, PNG MIME and SHA-256 digest, then displayed from a short-lived local blob URL; the confirm button stays blocked until that exact image fires load for the *same capture, patient, hash, challenge and URL*. An external preview URL, preview load error, stale or rotated challenge, wrong dossier or DOB, absent explicit checkbox, expired context and failed server confirmation remain blocked. The LAB UI is NOT mounted in clinical product navigation.

One same-server SQLCipher/FastAPI FUE-I now exercises the ACTUAL product read-only patient endpoint side-by-side with existing isolated signed-media staff review, preview, two markers, encrypted ClinicalAsset and durable idempotent ACK. It asserts the product ingress is *still closed* before and after the LAB success, no auto-patient link, and no accidental POST/clinical confirm API. The CI additionally executes existing Windows real SCM restricted-SID spool verification, B05-D1 Authenticode ZIP negative cases and React review tests **on the same candidate SHA**.

## Proof required (not presupposed)

- `same-server-sqlcipher-product-fue`: real localhost HTTP JWT/workstation + SQLCipher positive/negative FUE + no duplicate asset/receipt/audit/outbox.
- `preview-review-ui`: React tests for wrong identity, missing preview, off-origin preview, load error, challenge rotation, server rejection, closed production state; no approval based only on filled fields.
- `windows-real-service-and-b05-package`: actual disposable Windows SCM service, ciphertext verification and bounded temporary Authenticode trust; reject different-but-Windows-valid signer and tampering.
- Check exact SHA, real job logs, expected collected/executed tests and absent unexpected skips; GREEN CI alone does not close B06.

## Explicit remaining blockers

1. **Native adapter:** the current B03 real Windows SCM fixture only returns `Q→U` (no usable image identity) and `S→S0..S9/E*` for **synthetic LAB count**; it has no product API handing a verified specific capture to the application. Product status is intentionally `NATIVE_IPC_NOT_CONNECTED`.
2. **Production staff review:** existing SQLCipher staff challenge/confirmation endpoints are LAB mounted only. No actual product authenticated preview/confirm transaction exists yet; an HTTP test client is NOT a human validation.
3. **Storage / ACK:** SQLCipher signed receipt/asset/audit/outbox is demonstrated in isolated fixtures, not reconciled under a common on-prem production schema with real device identity, power cut, backup and rollback.
4. **Windows release:** Authenticode CI certificate is self-signed and disposable. No actual approved publisher trust, full Python/runtime dependencies, hardened installer/upgrade, physical TPM/CNG lifecycle, second Windows machine, scanner or cabinet approval.
5. **UX:** no observed product AFTER browser screenshots at required viewports or 200% zoom; no human UAT. Do not claim FUE-G or release readiness.
6. **Security gap for eventual product image:** the LAB preview now uses the authenticated API client, exact byte-size/digest matching, and short-lived blob URL, but the product still needs a proven server-side native capture authority and session/preview token binding, an approved secure browser context for WebCrypto, and real human UX observation. A visual load event is NOT proof of human inspection.

## Release boundaries

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

No automatic patient association. No deployment, merge, release, clinic installation, data migration, production patient fixture or artificial approval of clinical controls. Next implementation on THIS consolidated product integration branch: adapt real Windows service and authenticated local API with per-capture identity and safe preview, then mount the verified staff review + durable receipt using a server-owned authority, followed by real FUE-G. Human authorization is separate for critical activation and cabinet operations.


## B06 continuation — native per-capture inventory (2026-11-04)

**Actual scope (candidate pending exact-head CI):** the real disposable SCM LocalService fixture gains an `I` command, separate from existing `Q→U` and `S→S0..S9`. Under its Windows service SID the helper reopens and AES-GCM-authenticates the HotFolder ciphertext; it validates digest/size/MIME, verifies the item is still pending and emits one fixed **86-byte** unassigned metadata frame `I1` + local item ID + size + SHA256 + MIME/category codes. It never emits bytes, filename, selected patient or appointment. Verified empty queue yields `N0`; corrupted/unauthorized/invalid read yields a DENY and must never masquerade as `N0`. The local item ID is **not** a cryptographic device/capture claim and is not sufficient to approve transfer.

The new backend `imaging_acquisition_native_inventory_v15.read_native_unassigned` speaks that pipe as the existing OS principal. It is guarded by Windows + GitHub-hosted disposable test flags and the observed ACL. **Not mounted into backend.main, not exposed as a patient API.** All wire fields have canonical fixed-length validation; deliberately no media bytes, patient selection, device signature, approval, TLS claim, ACK or write operations. CI runs real LocalService and approved Windows user, rejects a second user, corrupt ciphertext and wrong-key, validates stability across service restart, and reuses existing SQLCipher/HTTP/JWT human ceremony tests. All tests are synthetic; physical equipment NOT_RUN.

This is a concrete Windows→local-application metadata bridge, **not** a complete clinical ingestion path: the product still reports `NATIVE_IPC_NOT_CONNECTED`. To make it product-capable, next implement a service-owned per-capture authenticated transfer handle/preview protocol with strong device key attestation, bind short-lived staff review to the exact bytes, and atomically commit Media Core asset/receipt/outbox with crash/restore evidence, using a release-approved installer. No right to associate a patient from the returned numeric item ID.

**Gates:** `READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`. UI visual approval remains a separate human decision. No merge/deployment/cabinet action.

## B06 continuation — raw media transfer over restricted Windows SCM pipe (2026-11-04)

**Scope, pending exact-HEAD FUE:** experimental `M` opcode for *a single, still-unassigned, AES-GCM-verified* capture, requested by fixed ID/SHA256/offset/count on an ephemeral GitHub-hosted Windows runner, never cabinet. Wire: ASCII `M + id(10d) + sha256(64hex) + offset(8d) + count(4d)`, exactly 87 bytes; response `D + count(4d) + binary fragment`, or exact `E0000` refusal. The Windows pipe ACL continues to permit only the synthetic separately-created approved Windows account SID, service LocalService SID and SYSTEM. The service reads the encrypted spool and revalidates pending status, SHA256 and MIME before each fragment. The process does not log or store the cleartext on disk. Client checks original inventory and complete assembled byte count, digest and structural PNG validity, then checks inventory again. Media never gains any automatic patient/appointment association, ClinicalAsset, ACK or upload authority.

Deliberate bounded prototype: **PNG only, 16 KiB maximum synthetic image per capture, 2048-byte maximum fragment**, per-fragment LocalService subprocess; this is NOT performant for a real radiograph and MUST NOT be made a product endpoint. Host requires TEST, isolated runner and separate `DC06_B06_NATIVE_MEDIA_LAB=1` gate; no production or clinic paths. The service Windows account authorization is NOT sufficient clinical device or staff authentication (no hardware TPM/approved publisher/one-time staff-bound secret). The clinical product remains `NATIVE_IPC_NOT_CONNECTED`.

Negative FUE required on actual Windows: valid binary PNG readback and SHA256, forged id and digest refused **by the service**, service restart stable, wrong key / corrupted ciphertext rejected with explicit error, second Windows account cannot read, malformed frame and oversized range denied by parsers; re-run existing B03/B05 and HTTP SQLCipher/ack/UI regressions on exact candidate SHA. A test-only client invokes these probes and prints **fixed non-PHI markers**, never the media bytes. These are not human screenshot/UAT evidence and do not certify physical scanner, rollback, power-loss or cabinet restore.

Next true product work: replace per-chunk helper with performant persistent service protocol; use an approved service/device root of trust, SID and caller authentication, per-capture replay-safe staff-scoped capability, secure local app preview and explicit two-identifier patient binding, then atomic ClinicalAsset/receipt/outbox and real recovery/FUE-G. No merge/deployment without separate authorization.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## B06 staff preview / genuine multi-fragment Windows FUE — 2026-11-04

This candidate extends the real SCM Windows fixture from its previous 79-byte
PNG (one transport fragment) to a generated **synthetic, 6+ KiB valid PNG**
containing a benign ancillary tEXt chunk. It requires at least **four actual
2048-byte Win32 SCM pipe transfers**, not merely the preexisting two-fragment
Python protocol unit test. Every fragment is freshly AES-GCM verified under
the LocalService SID and the reassembled PNG must match the original SHA-256,
size and structural validation. Wrong capture ID, wrong digest, wrong AES key,
ciphertext corruption, wrong Windows user, restart and B05 signer/package
oracles remain REQUIRED on the exact changed HEAD.

Separate TEST-only staff preview hardening: the JWT + workstation + patient
preflight alone no longer permits the media GET. The isolated review server
requires the active, unexpired, unconsumed SQLCipher challenge of the same
staff, patient, workstation, capture digest and byte size. The UI supplies the
challenge as an authenticated `X-DC-Review-Challenge` request header, **not
a URL query parameter**. HTTP FUE denies absent/mismatched challenge, missing
review, expired review and post-confirm preview. This prevents previews from
remaining accessible beyond the current explicit staff review ceremony. It is
still a LAB authorization, **not** clinic device attestation or human approval.

CI must report the actual Windows four-fragment marker and all negative
oracles, HTTP/JWT/SQLCipher negatives and UI tests on the same HEAD; do not
promote code changes alone into a GREEN certification. Neither isolated
LAB review nor Win32 transport is mounted in production
`backend.main`: real product continues `NATIVE_IPC_NOT_CONNECTED`.

Remaining gates: approved publisher/service+device trust, secure
session-bound per-capture capability, real clinical media transport beyond
16 KiB, true on-prem patient selection/review + encrypted ClinicalAsset and
durable ACK, crash/replay/restore and second-host/scanner/TPM/human FUE-G.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.



## B06 continuation — server-held Ed25519 device proof × staff review challenge (2026-11-04)

The LAB review was already staff-JWT/workstation/challenge scoped, and the
separate signed upload/receipt verified a pinned Ed25519 device identity.
Previously the *preview* did not require that independently signed proof.
This pass reuses the **existing** test-only SQLCipher device enrollment:
`verify_pending_device_capture_proof(db, claim, device_proof)` validates
the registered, active Ed25519 device key and its generation/station,
the pending immutable capture ID, selected patient/staff/tenant, SHA-256,
byte count, and the test-device-only challenge. It refuses key substitution,
device revocation, expired or consumed pending capture and any invalid proof.
It runs at **LAB review begin, explicit confirmation and preview**. The
signature is supplied by a **server-owned test fixture closure**, never a
query parameter, browser header or automatic patient identifier.

The existing staff authority independently requires JWT + workstation cookie,
patient access, the selected dossier/DOB markers, an expiring one-use SQLCipher
challenge bound to the same capture and active staff, and explicit confirmation.
The media bytes passed to LAB mount must match the signed claim digest and
length. This is **two independent authorities for LAB**, not a certified
physical scanner enrollment or an authenticated Windows host/device bridge.
A browser's copied review challenge cannot replace the device proof, and a
device signature cannot act as a staff confirmation.

Exact-head FUE required: real SQLCipher/localhost HTTP refusing preview,
begin or confirm after pinned key substitution, generation change or device
deactivation; the underlying proof rejects wrong staff, workstation, patient,
capture ID, digest, byte count, generation, foreign key; successful prior
LAB review + encrypted Media Core signed ACK and Windows multi-fragment
SCM/Authenticode must regress on SAME SHA. Product `backend.main` still
does not mount the LAB preview/transfer and patient status stays
`NATIVE_IPC_NOT_CONNECTED`.

**Still OPEN:** verified signed capture issued by the *actual* Windows
service instead of a disposable fixture closure; TPM/hardware enrollment,
release signer and physical scanner; scalable real DICOM/JPEG/PNG/PDF media;
actual staff login session-bound native capability in backend runtime,
one atomic on-prem media/receipt/outbox transaction with interruption/retry,
visual FUE-G and owner authorization.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## B06 — device-signed patient-unassigned manifest before human selection (2026-11-04)

**Architectural correction (pending exact-HEAD proof):** the LAB test-device
Ed25519 signature previously covered a staff-/patient-bearing `claim` even
for preview. This is the wrong authority for a physical scanner, which must
never decide the eventual patient. The new **independent, immutable and
patient-free signed capture manifest** contains exactly: enrolled tenant,
device, station, generation, opaque capture ID, verified media SHA-256,
byte length, image/png MIME, random nonce, issuance and expiry. Its
canonical JSON includes domain-separated purpose, no staff, patient,
dossier, DOB, appointment or asset ID. The private signing key stays in
the disposable synthetic device fixture; server SQLCipher stores the
manifest and signature, checks the enrolled pinned Ed25519 public key
and rejects key substitution, changed digest/size, expiry and reused
nonces. No browser/device client gets to submit the proof while reviewing.

The LAB review now validates this **unassigned** signature when starting,
previewing and confirming. Confirmation consumes the manifest **inside
the same SQLCipher transaction** that marks the staff review consumed,
records independent device-review approval and its audit. A rollback
restores the manifest for safe retry; replay after confirmation cannot
reopen preview or bind the same capture to another patient. The separate
legacy 03M laboratory upload/receipt STILL uses its prior patient-/staff-
coupled signed claim: the end-to-end production authority is therefore
**not yet migrated**. This change only corrects the *pre-patient* proof
and staff review boundary, not the clinical publisher.

**FUE required on final SHA**: independent SQLCipher tests for signature
byte fields excluding patient/staff, forged device key, crossed device,
capture, station, generation, size/digest, duplicate nonce, expired and
revoked manifest, transaction rollback and one-time consumption, plus
existing localhost JWT + review + patient double-markers + encrypted
ClinicalAsset/ACK replay, Windows real SCM multi-fragment/Authenticode,
and React tests. The actual product endpoint must remain
`NATIVE_IPC_NOT_CONNECTED` and the human visual workflow cannot be
bypassed. Existing Windows child process 15-second timeout was observed
on the prior PR HEAD despite an identical-SHA successful retry; keep
CI reliability as an open risk.

**Clinical gaps:** real scanner-signed manifest via service-owned pinned
device key/TPM, native staff session capability, non-test enrollment,
full-size radiography, independent authorization/transaction receipt,
crash/recovery/second host, visual human approval. No physical hardware
test was performed.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## B06 implementation block 1/5 — product backend ↔ Windows SCM unassigned inventory (2026-11-04)

**This is LOT06 software implementation, NOT a physical LOT10 test.**

Product route `GET /api/imaging/acquisition/unassigned` is now mounted
in **actual `backend.main`**. The endpoint is GET-only, served on loopback,
and requires actual authenticated JWT permission `patients` and a valid
current tenant's enrolled workstation cookie (station-locked mode DENIED).
The response contains **only one unassigned record's canonical opaque ID,
SHA-256, byte count, MIME and category**. No patient/dossier/appointment,
raw image, filesystem path, pipe name or per-patient suggestion; no POST,
ClinicalAsset or receipt. No-store/no-sniff response headers. With no
trusted local native bridge explicitly attached to the server, it responds
`NATIVE_IPC_NOT_CONNECTED` and an empty queue — with no false claim that
the service is installed or trusted. Failed native inventory reads return
503, **not** a fake empty queue.

`backend/services/imaging_acquisition_native_bridge_v15.py` encapsulates a
tenant/workstation-bound backend service adapter with real Win32 functions
`read_native_unassigned` and `read_native_capture_bytes`. The latter is
**server-side only** in block 1: it refuses changed inventory before/after
read, mismatched hash, byte length or MIME, and exceeds neither the currently
certified 16 KiB Win32 LAB limit nor its PNG-only media scope. No raw bytes
are exposed by any B06-1 HTTP endpoint. The actual Windows SCM CI fixture
now calls the same backend inventory adapter under the separate authorized
Windows account, verifying real AES-GCM spool metadata and rejecting foreign
tenant ID at the product service boundary.

**Mandatory fail-closed bootstrap separation:** product `backend.main`
does not automatically install, attach or discover an IPC pipe from a
browser, HTTP request, environment toggle, filename or untrusted installer.
The trusted object must be supplied via
`app.state.dc06_unassigned_bridge` **only after future verified
service installation and attestation**, not by front-end callers. The
existing Win32 wire client remains explicitly LAB-gated to an approved
GitHub-hosted Windows test environment. Thus this step **connects
the software APIs and proves data flow with mocks and the genuine Windows
SCM test**, but does **not** activate a real cabinet native service. The
existing patient-scoped status remains `NATIVE_IPC_NOT_CONNECTED` and
`clinical_receipt_authorized=false` intentionally until staff-bound
preview and patient confirmation in block 2/5 and durable integration in
block 3/5.

**B06-1 FUE required** at exact SHA: no JWT 401/403, missing or wrong
station 423, no attached bridge returns non-authorizing disconnected
status, tenant/station mismatch denied, canonical inventory with no
patient fields, actual SHA/size/MIME byte checks, race/swapped capture
denied, malformed/failed peer gives 503, GET no-store, POST 405, raw
media URL 404, zero receipt/asset writes. Real Windows SCM/LocalService
unassigned read & multi-fragment SHA, wrong key/corruption/second user,
Authenticode signer/ZIP and React must remain GREEN.
No hardcoded theme styles. Do not merge/deploy/install on this pass.

**LOT10 ONLY:** scanner physical, TPM hardware, true second workstation,
power interruption and cabinet human acceptance; these are NOT LOT06
feature-development blockers. LOT06 remains responsible for testable
production integration plus automated CI and non-physical UI review.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.
