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
