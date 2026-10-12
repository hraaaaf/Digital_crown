# LOT 06 — Imaging Acquisition Gateway — contract and safety gates

**Status: OPEN. Sub-lot 06A standalone laboratory hot-folder only.** Base master c0d47f4832e6da2211c6f94eb88f0db56fcaebb6. No clinical server ingestion, genuine Windows device or hardware certification has been executed.

## Existing system audit (no changes to these interfaces)

- Canonical Patient: backend/models.py Patient(id, employer_id, deleted_at), cabinet scoped, protected by assert_patient_access.
- Canonical Appointment: backend/models.py Appointment(patient_id nullable, employer_id, deleted_at); backend/routers/appointments.py enforces tenant when listing per patient.
- Canonical imaging: backend/models_media_core.py ClinicalAsset(encrypted storage, SHA-256, source_kind DEVICE_CAPTURE, parent_asset_id for derived thumbnails, provenance_json); backend/services/clinical_asset_ingestion.py content validation and encryption-bound storage.
- Existing POST /api/patients/{patient_id}/assets/import requires patient permission and validates content, but has **no durable device idempotency/receipt lookup**. Deduplication at blob storage is NOT logical asset idempotency. Unattended use is prohibited pending a separate server API.
- Hub component frontend/src/features/hub/ControlCenterTopologyPanel.tsx exists. No Control Center imaging UI has been changed; check the product's actual mobile surfaces before any later UI work.

## Implemented LOT06A boundary

Explicit-only Python hot-folder polling, stable file observations before bounded read, 50-MiB cap, PNG/JPEG/WebP/PDF magic/suffix preliminary detection. Unknown or mismatched formats, including raw DICOM, enter encrypted local QUARANTINED state. No clinical file deleted/renamed. Local SQLite WAL FULL-synchronous queue+audit, SHA-256 fingerprint and metadata-scoped dedup, AES-256-GCM encrypted spool with per-workstation/cabinet AAD; secret from DC_IMAGING_SPOOL_KEY_HEX, never committed. No source filenames or patient names/IDs in diagnostics. State PENDING_CONFIRMATION means **never integrated** and cannot be delivered by this module. RETRY_PENDING and BLOCKED are local retry bookkeeping, not verified upload attempts.

Known limits: preliminary magic detection is NOT complete content decoding; server must fully validate. Windows file locking, reparse points, spool NTFS ACL, key escrow/recovery and installation require genuine Windows verification. Local content-level dedup MUST NOT silently coalesce distinct patients or distinct clinical capture intent.

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
