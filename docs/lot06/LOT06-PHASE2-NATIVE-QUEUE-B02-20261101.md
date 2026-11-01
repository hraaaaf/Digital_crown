# Digital Crown LOT06 Phase2 B02 — Native Win32 peer probe + encrypted unassigned queue

Parent PR #1192 `59cc1e55a65c26bc4f0fa6c00f75402b5d14b7d5`. Single [Notion canonique](https://app.notion.com/p/3e677c66336281639beae2a946df1483).

## What this actually implements
- Extends the **existing disposable** Windows SCM LocalService restricted Service SID / custom DACL pipe fixture: a distinct authorized Windows client process sends **one byte Q**, receives **one byte U** (meaning read-only / unassigned data NOT returned, clinical NO-GO). Prior R write probe stays valid; unauthorized separate user still cannot open the pipe, nor create its own instance. It does **not** authenticate TPM or authorize capture transfer. The pipe sends no filenames, patient IDs, media bytes or capture count.
- Adds `tools/imaging_gateway/unassigned_queue_v15.py`: a **server-internal** read-only verified view of actual HotFolder AES-GCM ciphertext/SQLite queue. Only PENDING_CONFIRMATION appears, SHA256/length/MIME/AES integrity checked, basic state-race recheck, returned immutable items are opaque `id,digest,size,mime,category` and have **no patient, appointment, filename, original path, clinician, receipt, media bytes**.
- Linux tests exercise real encrypted storage, no patient fields, restart with verified queue, injected ciphertext tamper and fail-closed, retry state hidden. Windows tests execute real SCM + new other-user separate-process IPC round-trip. No schema or cabinet install; no new product endpoints, no changed patient media upload.

## Material limitations (do not relabel as product-ready)
- Native Q/U is **a live peer/ACL probe, not a spool-to-service data transport**. HotFolder and SCM service are not yet linked by a verified service-owned API; nothing in the real patient UI reads captures or preview. A readiness response of U **must never be treated as clinical authority**.
- The AES-GCM spool is real, but its encryption-key bootstrap/lifecycle, filesystem ACLs and installer binding have not been certified on the eventual cabinet computer.
- Hardware TPM CNG P-256, independent receipt-key pin, actual two-host Windows remote denial, real clinic scanner LOT10.4, real human review, crash/powercut staged storage/receipt reconciliation and external review remain OPEN.
- No use of the isolated HTTP LAB as product transport; B01 `NATIVE_IPC_NOT_CONNECTED` remains exactly as-is.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
No merge, deploy, cabinet installation or real patient data.
