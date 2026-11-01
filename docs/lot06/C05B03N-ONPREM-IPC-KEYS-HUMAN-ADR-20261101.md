# ADR — Digital Crown V1.5 LOT06 C05B-03N · On-prem Windows local trust boundary

**Status**: DESIGN DECISION PROPOSED/INTERNALLY SELECTED, NOT CLINICALLY AUTHORIZED  
**Date**: 2026-11-01  
**Parent**: [C05B-03M DRAFT #1183](https://github.com/hraaaaf/Digital_crown/pull/1183) pinned at `597233e064ce80f54168e9b446e6d74263fd618e`  
**Canonical**: https://app.notion.com/p/3e677c66336281639beae2a946df1483  
**Scope**: one-machine Windows clinic deployment candidate; NO deployed product route, service or real patient.

## Decision: single-machine Windows named pipe first

**Chosen for first V1 on-prem Windows cut:** Windows Named Pipe **only on the same host** between supervised acquisition bridge and the local trusted backend. **No HTTP server opening, even on 127.0.0.1, for the clinical ingestion boundary in this cut.** The current 03L localhost HTTP remains a synthetic interoperability test and is *not* the chosen product transport.

Server must create one fixed, versioned, non-discoverable-by-name-as-security pipe under `\\.\pipe\DigitalCrown-LOT06-<install-binding>` with a custom DACL and `PIPE_REJECT_REMOTE_CLIENTS`, including protection against clients from other logon sessions. Require unique verified service SID, installation-bound authorized client Windows logon SID(s), deny Everyone/Anonymous; don't rely on the permissive default pipe security descriptor. Separate name squatting protection (`FILE_FLAG_FIRST_PIPE_INSTANCE`), bounded instance count, max message size, per-request deadline, audit on denial. Verify OS security token with checked Win32 APIs before any parsing of untrusted metadata; check return value of impersonation and always `RevertToSelf` in `finally`. A pipe path, PID, source filename or claimed SID in JSON is never identity.

**Why over localhost HTTP?** Avoids promoting a testing-only bearer-token web endpoint to an actual cabinet network service and allows Windows-native peer + DACL gates. This is a V1 scope reduction, not a claim that Named Pipes automatically secure data: DACL, service SID, first-instance, secure token inspection, Windows DACL tests and installer are **not yet implemented**.

**Deferred**: if devices or clinic PCs require cross-host ingestion, create a separate explicitly owner-approved V1.x/V2 LAN mode with TLS 1.3 + mTLS, enrollment certificates, private CA, certificate pinning and revocation; never quietly enable SMB remote named pipes or use raw HTTP. Office Wi-Fi and loopback alone do not authenticate a client. Single-machine operator workflow is the explicit acceptance boundary now.

### Windows references verified (Microsoft Learn)

- [Named Pipe Security and Access Rights](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights) — custom descriptor and client/server access checks; permissive defaults and FILE_CREATE_PIPE_INSTANCE/GENERIC_WRITE overlap.
- [CreateNamedPipeW](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createnamedpipew) — `PIPE_REJECT_REMOTE_CLIENTS`.
- [ImpersonateNamedPipeClient](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-impersonatenamedpipeclient) — check return value; failure means requests continue as server identity; revert after checks.
- [SERVICE_SID_INFO](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-scmr/ea1a9acd-4bb2-473f-ae5b-55969c5960fc) — service SID types and restrictions.
- [NCryptCreatePersistedKey](https://learn.microsoft.com/en-us/windows/desktop/api/ncrypt/nf-ncrypt-ncryptcreatepersistedkey), [Signing Data with CNG](https://learn.microsoft.com/en-us/windows/win32/seccng/signing-data-with-cng) — persistent keys, ECDSA P-256 sample. Compatibility with actual clinic OS/TPM not certified.

## Key policy — no silent Ed25519 LAB → production conversion

**Product candidate:** ECDSA P-256/SHA-256, Windows CNG persisted key, prefer/require Microsoft Platform Crypto Provider (TPM-bound) for the initial security bar. No exporting private signing key; admin enrollment with local workstation and tenant binding; distinct keys for (a) acquisition device credential and (b) server-issued receipt. Distinct fingerprint, generation, purpose, algorithm, status, creation/revocation/expiry and signer's policy revision in SQLCipher. A replacement public key is not supplied by a client in the upload. Never reuse the staff JWT, device bearer token or old signed reply as enrollment proof. NO fallback to software KSP when TPM is absent without a separately documented owner-approved exception + independent security review and re-run FUE.

**Critical compatibility:** existing C05B-03L/M Ed25519 signatures are ephemeral disposable LAB cryptography; Microsoft's documented CNG sample explicitly uses ECDSA P-256. Their wire format cannot be silently reinterpreted as P-256. Version and algorithm ID must be bound in the signed envelope, and clients must reject unknown or downgraded algorithms. Probe actual Windows PC/TPM support before finalizing any installer; if unsupported, the entire ingest path is disabled, not downgraded implicitly.

**Lifecycle:** `UNENROLLED → PENDING_ADMIN_APPROVAL → ACTIVE(generation N) → ROTATING(N+1) → REVOKED/RETIRED`. Only admin + trusted local peer can provision and rotate. New signatures must use active generation. Prior key may validate **historical immutable receipts in a read-only audit context**, never authorize a new upload after rotation or revocation. Identity change or owner key loss triggers administrative recovery and a new enrollment, not silent key generation by collector. Server receipt key pin is independently pre-provisioned, not accepted from same server response.

## Human confirmation: clinical invariant and target UX

1. **Capture arrival**: queue shows only opaque capture/device ID, media type, time and safe thumbnail from authenticated encrypted spool. No automatic patient lookup from file, nearest appointment, EXIF or DICOM tag; no visible dossier insertion.
2. **Patient selection**: authenticated staff using the actual cabinet session chooses a patient inside correct tenant. UI displays **at least two independent identifying data points** visible to operator (e.g. patient name + date of birth or cabinet patient number), and, if available, linked RDV; any contradiction blocks.
3. **Explicit clinical context**: staff sees media preview and capture source/device + hash summary; chooses a coded reason (clinical photo, transfer, corrected link), confirms an explicit checkbox/action. No auto-check on import. Must use accessible keyboard/focus and 200% zoom; test at 390/768/1280 where UI is applicable, plus desktop Windows at 100/200%.
4. **Server-authenticated approval**: server generates a one-time context bound to `tenant|staff|JWT JTI|Windows station identity|patient|device|capture|version|sha256|length|device key generation|timestamp|reason|nonce` with expiry <=120 seconds and server-owned audit event. UI cannot issue its own proof. Permission/revocation, patient active/scope and station version are rechecked in same DB writer transaction as receipt.
5. **Commit**: only when storage is cryptographically verified and transaction receipt+audit+outbox succeeds may the review be consumed. Dossier becomes visible only after server committed and client ACK signatures/scope validated; no partial publication. Sensitive patient identity stays out of bridge logs.
6. **Reconciliation**: if ACK is lost or client crashes after server commit, agent uses **authenticated read-only GET_RECEIPT** bound to immutable capture and current active authorities, returning pinned signed receipt (never new POST media when review expired). If server lacks committed receipt, require fresh staff review; never silently reuse expired approval.

### Minimal operator acceptance (manual FUE not yet executed)

- Wrong patient or mismatched RDV → explicit conflict, no clinical document.
- Session expired / station locked / staff permission revoked → denied before review or receipt.
- Media tamper or wrong device generation → denied, original source retained.
- Two competing staff confirmers → exactly one successful consent bound to capture/version.
- Crash at (1) encrypted spool, (2) SQLCipher media staging, (3) receipt before ACK, (4) ACK before publish → no orphan shown in patient record; recovery without duplicate clinical receipt/audit/outbox.
- 200% text zoom, keyboard focus, screen-reader labels, patient identity always legible; cancellation never grants authorization.

## Crash-safe storage design, unresolved P1 requiring proof

The existing 03L flow commits ClinicalAsset encrypted storage **before** the receipt transaction. Product must implement a private `STAGED_ENCRYPTED` area that is never published until matching SQLCipher receipt+audit+outbox commit, plus restart/GC handling for orphan encrypted blobs with tenant-scope and retention limits. Database commit cannot atomically commit filesystem bytes without a crash protocol. Use digest authentication, durable fsync of temp files and directory, write-ahead durable journal, then database transaction and signed read-only ACK reconciliation; do not claim cross-DB/storage atomicity. Power-cut and power-resume need actual hardware failure injection.

## Machine-checkable guard & evidence restrictions

- `isolated_fue_lot06c/c05b03n_onprem_policy_contract.py`: pure Python **SIMULATION** accepting synthetic `LocalIpcEvidence`, `KeyPolicyEvidence`, `StaffReviewEvidence`, `ReceiptReconciliation`. It rejects HTTP, open/default DACL, remote enabled, anonymous client, weak/software keys, implied patient selection, expired review, unsigned receipt and media reupload on ACK loss. Does NOT verify Windows OS calls, secure UI or cryptographic signatures.
- `isolated_fue_lot06c/test_c05b03n_onprem_policy_contract_v15.py`: negative matrix on Linux + Windows at same HEAD.
- `isolated_fue_lot06c/windows_pipe_smoke_c05b03n.ps1`: disposable Windows OS named-pipe **creation/disposal only** using `PipeOptions.CurrentUserOnly` (no client connected); is NOT proof of data exchange, restricted service SID/DACL, `PIPE_REJECT_REMOTE_CLIENTS`, different-account denial, impersonation, SCM or TPM. A previous same-user round-trip smoke deadlocked on the hosted Windows runner and was **withdrawn** rather than mislabelled green; an independently supervised IPC handshake FUE remains OPEN in C05B-03O. No installed service or policy mutation.
- 03M 22/22 and 03L 16/16 remain regression targets; 03N doesn't activate any new production path.

## Independent review packet / acceptance gates before any later product implementation

Security reviewer must receive this ADR, PR hierarchy (#1180→#1181→#1183→03N), risk register from C05B03M, signed envelope schema and key lifecycle, Windows DACL/SDDL and runtime token capture evidence, service SID and SCM manifest, CNG TPM non-exportability proof, Windows impersonation negative tests using an **unprivileged other account**, actual staff UI human FUE, power-kill/recovery matrix, SQLCipher + AES orphan reconciler, and clinic data-handling/restore procedure. Reviewer must produce signed independent PASS/FAIL against **an exact Git SHA**; GitHub CI green alone is insufficient.

**NO GO:** product bridge remains blocked. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. No merge, no deployment, no clinical data, no Windows installer, no database migration. Next **C05B-03O** only after owner decision: real Win32 SID/pipe + CNG probe in disposable Windows test environment, followed by separate human UI FUE and security review; clinical GO only when independent review and owner approves.
