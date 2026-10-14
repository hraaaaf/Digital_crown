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

**Portability caveat**: Windows directory-entry metadata can omit the true NTFS hard-link count, while a full os.stat(path, follow_symlinks=False) returns usable information on the hosted test runner. The scanner uses that full non-following stat and rejects reported multi-link objects (st_nlink > 1) and symlinks. A physical cabinet NTFS/ACL/reparse-point and filesystem race test is still mandatory. Intermediate Windows runs #38551094032 (metadata mismatch) and #38551519020 (DirEntry.stat underreports hardlinks) failed; both informed the final implementation. Do not call this hardware certification.

**Proof scope**: Linux/Windows hosted GitHub Actions synthetic cases cover byte quota, item limit, disk reserve mocking, forced ENOSPC, encrypted orphan replay after interruption, untracked partial spool, restart on capacity increase, aggregate no-PHI health, misconfiguration, and unsafe entries. No physical full-disk test was run. Other LOTs, shared SQL models, backend and UI remain untouched.

## LOT06-E — Synthetic-only imaging adapter capabilities

The dedicated tools/imaging_gateway/adapters.py defines a small, isolated interface for future HOT_FOLDER, DICOM, TWAIN and VENDOR_SDK adapters. It does not import manufacturer libraries or open any capture hardware. HOT_FOLDER is **SIMULATED** (metadata proposal only); DICOM and TWAIN are **NEEDS_DRIVER**; VENDOR_SDK is **UNSUPPORTED**. All four explicitly report supports_live_capture=false, supports_patient_link=false, certified_hardware=false.

propose_capture accepts only strict opaque capture ID, workstation ID, SHA-256, size, MIME and modality category. It rejects unknown/disabled adapters, unrecognized media metadata, malformed hashes/IDs, zero or out-of-limit size and radiology MIME/category combinations lacking a reliable parser. Proposal has no patient ID, appointment, upload permission or canonical receipt; it is not a scan, a device trust contract, a clinical upload, or an authorization to attach an image to a patient. DICOM is never treated as safely parsed just because a file suffix or protocol name mentions DICOM. Vendor SDK integration remains separate explicitly authorized manufacturer mini-lot.

Synthetic tests (tests/test_adapters.py) are discovered by the existing Windows/Linux unittest workflow; no backend, shared database, SQL migrations, frontend/mobile, hardware driver or external service changes. Activation, DICOM parser, TWAIN device discovery, manufacturer certification and full patient timeline are not part of 06-E.

## LOT06-F — Operator observability and confirmation journey (offline/read-only)

**Audited existing UI surfaces (2026-10-14)**: `frontend/src/features/hub/WorkstationExperiencePage.tsx` wraps Control Center responsively using mobile/tablet paddings; `ControlCenterTopologyPanel.tsx` is an existing network/topology diagnostic, not an imaging console. `frontend/src/features/patients/components/PatientMediaTimeline.tsx` already has responsive mobile-size image previews, but it only displays actual ClinicalAssets attached to a patient. It is NOT proof of an imaging capture review or confirmation feature. No device acquisition UI (desktop or mobile) was added to those shared cross-lot routes in 06F. This keeps UI scope isolated while other branches merge; no BEFORE/AFTER screenshot certification is claimed.

**Local operational projection**:
- `HotFolder.storage_health()` continues returning aggregate counts; any unknown/corrupt DB state is now sanitized to the fixed `UNRECOGNIZED_STATE` counter and forces `BACKPRESSURE`, never leaking a DB string into a report.
- New pure `tools/imaging_gateway/operations.py` transforms only aggregate health into finite French notices: `LOCAL_BACKPRESSURE`, `UNKNOWN_QUEUE_STATE`, `ORPHAN_SPOOL`, `RETRY_EXHAUSTED`, `QUARANTINE_REVIEW`, `RETRY_PENDING`, `HUMAN_LINK_REQUIRED`, and unconditional `CLINICAL_INTEGRATION_PENDING`. Corrupt/inconsistent totals, metrics, codes and unknown statuses are rejected rather than displayed.
- Operator status is **always** `mode=READ_ONLY`, `clinical_status=NOT_CONNECTED`, `upload_permitted=false`, `patient_confirmation_permitted=false`, `server_confirmed=false`. A local PENDING_CONFIRMATION is not proof of patient confirmation, and retry state is not proof of server receipt. Never infer patient from filename, chronology or workstation.
- CLI on an authorized local machine with existing watch-dir/state-dir/cabinet/workstation and spool key: `--operations` prints a narrow terminal French checklist; `--operations-json` prints fixed-contract sanitized JSON for a *future* authenticated UI; `--operations-html` prints a static **offline** responsive HTML mock suitable for redirecting to a local file with an operator-controlled shell. HTML includes a mobile viewport and single-column CSS for <=600px; it has NO JavaScript, API calls, forms, buttons, auto-downloads or remote images. It is **NOT** mounted in Control Center, not a backend API, and does not send PHI. Do not publish a generated report to web storage.
- UI proposal for later licensed integration: on desktop show capacity, queue breakdown and priority remediation; on mobile stack cards vertically. An explicit red safety boundary remains visible: **"Lecture seule · Association patient et envoi clinique en cours de construction"**. Actual patient selection and approval must live in an authenticated backend-mediated workflow with identity proof, durable human decision and atomic server receipt, not client-only controls.

**Testable states**: empty spool; waiting patient association; quarantined file; retries pending/exhausted; hard quota; disk full; orphan ciphertext; corrupt local state; unknown metrics; report XSS escaping; HTML 390px responsive stylesheet and wide 1440px grid contract, no submit/button, no patient metadata. Synthetic Linux/Windows tests, no frontend visual BEFORE/AFTER or device certification.

**Blocking conditions for activation**: backend device identity, session-bound capture/patient verification, persisted human confirmation, server upload/idempotent receipt, genuine physical Windows and instrument tests. Local projection is read-only, never a way to override these gates. Mobile product surfaces exist but this imaging workflow remains en cours de construction.

## LOT06-G — Windows installation safety read-only gate

**Current status: inspection prototype only. No installation, ACL repair, Windows service, DPAPI provisioning, production activation or physical hardware validation.** The cross-platform hot-folder collector currently receives a 256-bit spool key from environment variable DC_IMAGING_SPOOL_KEY_HEX. This is not a certified Windows secret delivery mechanism (environment leak/dump, backup, rotation and operator boundary remain unresolved). Never type, paste or print a real key into a shell transcript or CI job. A DPAPI-bound key lifecycle (identity, provisioning, escrow/recovery, rotation, revocation, service account) requires a separate authorized gate; the present script explicitly reports DPAPI_DEVICE_KEY_AND_RECOVERY_VERIFIED=false and cannot report READY for installation.

To examine an **already-provisioned test directory** on Windows (PowerShell 5.1 or later; no spool key required, and no changes to any file):

~~~powershell
powershell.exe -NoProfile -NonInteractive -File .\tools\imaging_gateway\windows\preflight.ps1 -WatchDir "C:\DC-TEST\watch" -StateDir "C:\DC-TEST\state"
~~~

The script returns **stable JSON codes only** (no actual path, patient, file name, SID, ACL identity, digest or key) with contract DC06G-WINDOWS-PREFLIGHT-V1, status BLOCKED, ready_for_install=false, clinical_activation_permitted=false. It inspects:
- required existing directories; watch and private/state directories must be disjoint;
- directory reparse points and ancestor links, including private/spool;
- the state volume must be reported NTFS by Get-Volume (unavailable/inconclusive becomes a blocker);
- Windows ACLs on state/spool and existing acquisitions.sqlite3, rejecting allow-write ACE for Everyone, Authenticated Users, Users, Guests, Interactive and Anonymous by invariant **SID**, not localized account names; explicit deny entries do not justify accepting broad allow entries;
- presence of a valid local key protection/escrow strategy and genuine physical NTFS validation **remain UNSATISFIED by construction**, even if the runner reports directory ACLs safe.

**Read-only exit semantics**: exit code 0 means the diagnostic completed and returned JSON, NOT installation approval; inspect status and every check.ok. Inspection failure returns a generic INSPECTION_FAILED code without leaking exception text. The script performs NO Set-Acl, New-Item, Remove-Item, DPAPI decrypt, driver install, service start or upload.

GitHub-hosted Windows runners execute synthetic native PowerShell self-tests, path/ACL inspection, missing-path, nested-path and no-key proof alongside existing 06A-F tests. The native runner verifies that the inspector can be executed, not that a cabinet machine is configured correctly. Before any real installer/driver approval, check dedicated Windows account, NTFS ACL/reparse and file ownership, DPAPI user/machine scope and recoverability, antivirus lock contention, backup/restore and fresh-key procedure, genuine camera/RVG/pano/ceph devices, and server Patient/RDV identity and receipt gate. The operational clinical gate is still NO-GO.
