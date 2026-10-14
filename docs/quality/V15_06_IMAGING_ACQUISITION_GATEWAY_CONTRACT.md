# LOT 06 — Imaging Acquisition Gateway — contract and safety gates

**Status: OPEN. Sub-lot 06A standalone laboratory hot-folder only.** Base master c0d47f4832e6da2211c6f94eb88f0db56fcaebb6. No clinical server ingestion, genuine Windows device or hardware certification has been executed.

## Existing system audit (no changes to these interfaces)

- Canonical Patient: backend/models.py Patient(id, employer_id, deleted_at), cabinet scoped, protected by assert_patient_access.
- Canonical Appointment: backend/models.py Appointment(patient_id nullable, employer_id, deleted_at); backend/routers/appointments.py enforces tenant when listing per patient.
- Canonical imaging: backend/models_media_core.py ClinicalAsset(encrypted storage, SHA-256, source_kind DEVICE_CAPTURE, parent_asset_id for derived thumbnails, provenance_json); backend/services/clinical_asset_ingestion.py content validation and encryption-bound storage.
- Existing POST /api/patients/{patient_id}/assets/import requires patient permission and validates content, but has **no durable device idempotency/receipt lookup**. Deduplication at blob storage is NOT logical asset idempotency. Unattended use is prohibited pending a separate server API.
- Hub component frontend/src/features/hub/ControlCenterTopologyPanel.tsx exists. No Control Center imaging UI has been changed; check the product's actual mobile surfaces before any later UI work.

## Implemented LOT06A boundary

Explicit-only Python hot-folder polling, stable file observations before bounded read, 50-MiB cap, PNG/JPEG/WebP/PDF magic/suffix preliminary detection. Unknown or mismatched formats, including raw DICOM, enter encrypted local QUARANTINED state. No clinical file deleted/renamed. Local SQLite WAL FULL-synchronous queue+audit, SHA-256 fingerprint with secret-keyed source path and stable source file identity/stat metadata (distinct capture generations stay distinct); state directory bound to one cabinet/workstation; AES-256-GCM encrypted spool with per-workstation/cabinet AAD; secret from DC_IMAGING_SPOOL_KEY_HEX, never committed. No source filenames or patient names/IDs in diagnostics. State PENDING_CONFIRMATION means **never integrated** and cannot be delivered by this module. RETRY_PENDING and BLOCKED are local retry bookkeeping, not verified upload attempts.

Known limits: preliminary magic detection is NOT complete content decoding; server must fully validate. Windows file locking, reparse points, spool NTFS ACL, key escrow/recovery and installation require genuine Windows verification. Local dedup MUST NOT silently coalesce distinct patient identities or clinical capture intent. File-stat source identity is only a LAB replay heuristic: future server receipts require stable source capture IDs and patient-scoped idempotency.

## Server contract for next sub-lot (DESIGN ONLY, not implemented)

1. Administrative enablement by cabinet/workstation/hot-folder connector with short-lived credentials confined to acquisition operations; LAN HTTPS + authenticated device.
2. POST acquisition proposal: opaque capture_id, device + cabinet scope, SHA-256, bytes, MIME, one of PHOTO_CLINICAL/RVG/PANORAMIC/CEPHALOMETRY/OTHER, source metadata. No filename, time proximity or most recently opened chart as an authoritative patient match.
3. Patient/appointment resolve exclusively on server from active, explicitly authorized, tenant-scoped capture context. Zero/ambiguous/conflicting matches, null Appointment.patient_id, other tenant, soft-deleted patient -> AWAITING_HUMAN_LINK; no clinical media write.
4. Staff confirmation with exact patient identity preview & audited actor for ambiguous cases, including explicit audit-correctable reassignment.
5. One-use TTL upload ticket bound to tenant, device, patient/RDV, SHA and capture id. Server validates bytes again, writes original ClinicalAsset source_kind DEVICE_CAPTURE + separate derived assets and records audit.
6. Database-backed unique logical acquisition identity + receipt lookup by idempotency key (atomic ledger and asset binding), not just SHA-blob dedup. After timeout agent queries the receipt; reply must contain receipt_id, patient_id, asset_id, server_computed_sha256, state CONFIRMED. Absence or mismatch -> retry/blocked, never success.
7. Audit minimal structured events: source, cabinet, workstation, approved patient/RDV, digest, timestamps, transitions and corrections; device health + queue counts surfaced in Control Center, UX adapted after checking existing mobile feature behavior. No PHI in logs or CI artifacts.
8. Wi-Fi camera: configured watch/drop folder or separately documented authenticated protocol. TWAIN, DICOM, manufacturer SDK behind independent adapter boundary only when necessary. Hardware certification is a later gate.

## Stop/gates and evidence

BLOCKER: no server consent/idempotent ledger/receipt/API/negative tenant and misattachment tests, no genuine patient folder E2E.
BLOCKER: no Windows runtime/NTFS ACL/key recovery/locked-file race tests, no actual Wi-Fi/RVG/panoramic/cephalometric hardware acquisition evidence.
Never mark full LOT06, cabinet release, or acquisition device certified based on the synthetic CI.
Do not touch LOT04.7/04.8, LOT05, station/printing, SQL migrations or master. No Vercel deployment.
Synthetic suite: python -m unittest discover -s tools/imaging_gateway/tests -v.


## LOT06-C — Optional producer-ready handshake (lab hardening, independent of schema)

A producer can close/flush an image and then atomically rename a complete sidecar to the exact sibling name **`photo.png.ready`**. Start the opt-in local agent with **`--require-ready-manifest`**. The manifest must be UTF-8 JSON with **exactly** these fields (lowercase 64-hex SHA-256; no patient name or identifier):

```json
{"version":1,"sha256":"<sha256 of image bytes>","size":123456}
```

The sidecar must be a distinct regular file with a single hard-link, at most 256 bytes, not a symlink. It must remain unchanged across the media read. The agent verifies both the original source file signature before/after bounded read and the sidecar's immutable fingerprint and SHA/size, before encrypting/spooling the original. Missing, premature, invalid, replaced, large or linked sidecars do not stage any media, nor do sidecar files themselves create quarantined items. A mismatched digest is not a clinical event. The original and sidecar are never deleted or renamed by the agent.

**Important safety limits:** This is a **producer file-completion handshake**, not a signed trusted manufacturer event, not evidence that the device is medically certified, and not a human identity or patient confirmation. A malicious actor who can write the watched folder can fabricate both image and manifest. Default legacy two-stable-stat observation remains unchanged when opt-in is off; that mode can still read a briefly stable partial image and MUST NOT be called completion-safe. The strict flag is deployment configuration, not an irreversible persisted policy; operators must consistently enforce it. Hard-link/reparse-point behavior under a real Windows cabinet remains unverified. The spool decryption path also bounds ciphertext size to max_bytes + AES-GCM header/tag overhead to avoid allocation from an oversized local file.

**Contract tests** execute on Linux/Windows GitHub-hosted runners. No SQL model, backend, frontend/mobile, driver, patient upload or receipt was changed. The global LOT06 end-to-end success criteria remain unfulfilled.

## LOT06-D — Local capacity, disk-full backpressure and recovery (synthetic only)

The watcher now enforces a **local** budget, independently of the future clinical database: default encrypted spool limit **2048 MiB**, queue limit **1000 rows**, and disk free reserve **64 MiB**. Operators can adjust them explicitly with --max-spool-mib, --max-queue-items, --min-free-mib. Programmatic Config(max_spool_bytes, max_queue_items, min_free_bytes) checks strict bounded integer arguments; this is a cabinet/workstation *local* configuration. No production DB migration.

Before creating a new encrypted spool item, a BEGIN IMMEDIATE SQLite writer transaction checks logical row count, actual bytes present in the spool directory, and remaining free filesystem space. Actual bytes includes encrypted registered objects and unregistered partial/orphan files after interrupted transactions. The status is surfaced in scan_once().deferred, **never** as staged or CONFIRMED; the source is retained for another scan and the transaction rolls back on capacity errors. Existing valid captures still count as duplicates rather than new reservations while at quota. A recoverable ENOSPC/EDQUOT/Windows disk-full failure is reported as deferred and the agent can retry on the next scan once capacity returns. Unexpected IO errors propagate (fail-closed), not treated as successful acquisition.

Use --health with the normal explicit paths/credentials to print a no-PHI operational snapshot instead of scanning: state (READY/BACKPRESSURE), counts grouped by local state, queued_items, spool_bytes, orphan_files, orphan_bytes, free_bytes and configured limits. The latest capacity error is process-local only. It does not contain names, source paths, patient identifiers or blob digests; error counters are **not** a durable incident history when SQLite is itself unavailable. The already-existing SQLite audit continues recording successful queue transitions.

**Crash reconciliation**: after ciphertext durable rename but before SQLite commit, the orphan is included in the real disk-byte budget. The next scan with the same immutable local identity can verify/reuse the matching orphan ciphertext without double-counting its bytes, then record the row once. An orphan belonging to a *different* capture remains counted until an explicit, auditable operator cleanup process (not implemented in this lot). This feature never automatically deletes originals, quarantine items, or unknown .partial files. Two processes against the same local queue serialize the capacity decision through the SQLite writer lock, but other OS processes and free-space competition can still exhaust physical storage.

**Non-goals/limits**: scanning reads bounded media bytes into memory; it does not guarantee atomic reservation with OS free space or a manufacturer SDK. Spool limits do not include SQLite WAL/database allocation, temp files or unrelated files outside the spool; min-free reserve and handling ENOSPC limit risk but cannot mathematically prevent it. No automatic redrive on schedule, no on-screen cabinet alerts, no disk ACL/NTFS/key custody certification, no device upload, no full patient timeline or server receipt. If the watched source is externally deleted before capacity returns, the agent cannot recover it. Keep capture devices configured to preserve originals until explicit server-confirmed receipt in later LOT06 integrations.

**Proof scope**: Linux/Windows hosted GitHub Actions synthetic cases cover byte quota, item limit, disk reserve mocking, forced ENOSPC, encrypted orphan replay after interruption, untracked partial spool, restart on capacity increase, aggregate no-PHI health, misconfiguration, and unsafe entries. No physical full-disk test was run. Other LOTs, shared SQL models, backend and UI remain untouched.
