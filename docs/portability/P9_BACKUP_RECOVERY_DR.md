# P9 — Backup, Recovery & Disaster Recovery

**Status:** CLOSED ✅ — **8 EP credited.**

## Goal

A complete loss of the workstation must not imply loss of the cabinet.

## Success criterion — PROVED

P9 technical closure requires all of the following on the same candidate:

1. production DR snapshot creation with a real SQLite/SQLCipher cabinet DB and media;
2. exact `.dcbundle` SHA-256 + `.sha256` sidecar verification;
3. persistence outside the source runner, followed by deletion of the source runner transfer copy;
4. retrieval on a distinct fresh runner with no shared source filesystem;
5. Windows → macOS and macOS → Windows recovery;
6. conversion through the production portable → Guided Restore path using destination-local keys;
7. apply by the real **frozen packaged executable**, not a Python-only simulation;
8. post-restore `/health`, DB truth, `PRAGMA user_version` and media-byte verification;
9. wrong migration secret and tampered ciphertext rejected fail-closed;
10. existing interruption, unavailable destination, disk-full and retention tests remain green.

All ten gates are proved by the final candidate below.

## Existing verified foundation

- The historical daily database backup remains enabled and keeps local encrypted restore points.
- That path uses `backup.key`, which is **machine-local**. A copy stored only beside the workstation is not disaster recovery.
- Portable `.dcbundle` provides inter-machine/inter-OS cabinet export with DB + media, AES-256-GCM, scrypt, integrity manifests and machine-bound secrets excluded.
- Guided Restore provides preflight, safety point, detached apply, smoke verification and rollback.
- The Guided Restore apply gate requires a **frozen packaged executable** in cabinet mode.

P9 therefore does **not** introduce another archive or cryptographic format.

## DR contract

Scheduled DR is opt-in and fail-closed:

- `DIGITALCROWN_DR_DESTINATION`: absolute writable destination outside Digital Crown's local user-data directory;
- `DIGITALCROWN_DR_SECRET`: migration secret, minimum 16 UTF-8 bytes, never persisted by the DR service;
- `DIGITALCROWN_DR_KEEP`: verified snapshot retention, default 14, accepted range 1–90.

The recovery phrase must be escrowed independently from the workstation. Keeping the only copy in the cabinet `.env` defeats machine-loss recovery.

Each scheduled cycle:

1. preserves the existing local daily DB backup;
2. creates a portable `.dcbundle` in the configured DR destination;
3. recomputes and compares SHA-256 with the export result;
4. converts the bundle back through the production portable → Guided Restore path;
5. writes the candidate as `<bundle>.dcbundle.partial`, verifies it, then atomically promotes it to `.dcbundle`;
6. rejects and deletes the candidate if verification fails;
7. writes and re-reads a standard `<bundle>.sha256` sidecar only after promotion;
8. applies retention only to verified bundle + sidecar pairs;
9. stores only non-secret status in `backups/last_dr_status.json` using an atomic write.

`DIGITALCROWN_DR_DESTINATION` may be a removable disk, NAS mount or independently synchronized filesystem. A path outside Digital Crown user-data is necessary but does not alone prove off-machine redundancy.

## Technical off-machine storage boundary — CERTIFIED

The deterministic CI certification uses an **independently persisted off-runner artifact boundary**:

- the source job creates the production DR snapshot in an isolated staging destination;
- bundle + sidecar + non-secret proof are uploaded to the GitHub Actions artifact service;
- the source staging copy is deleted and deletion is asserted;
- the target job is a distinct fresh runner of the opposite OS;
- the target transfer path is asserted absent before artifact download;
- the target can recover only from the persisted artifact bytes.

This proves a machine-loss-style storage separation for the technical CI boundary: the target runner has no shared filesystem or process state with the source runner.

It does **not** certify GitHub Actions as the cabinet's operational backup provider, nor does it certify the durability, permissions or physical handling of a specific USB disk, NAS or synchronized filesystem. Real cabinet operational media/NAS setup remains a P13 real-cabinet validation.

This replaces the earlier device-specific wording that required CI itself to attach a “real removable disk/NAS”. The security goal is preserved: **independent persistence outside the failed workstation**, not a particular storage vendor or connector.

## Final certification evidence

Final candidate HEAD: `4590e2975e71ca89fc404e96e717646155b8fc14`.
Workflow: `Portability P9 Backup Recovery DR` #11, run `33276520623` — **5/5 jobs SUCCESS**.

### macOS source → Windows target

- fresh macOS 15 ARM64 source snapshot: SUCCESS;
- bundle SHA-256: `b1ec767990c3dba5dbd36ecf86fc31610cee7e6b3248e5413070a19d3de9374b`;
- source artifact `9721663479`, ZIP digest `sha256:ba53eca01ef063407cb1315daf129fba065ff3cc420ea6aa383a4ed41c0ef024`;
- source transfer copy deletion asserted;
- fresh Windows Server 2025 target downloaded the persisted artifact;
- real Windows PyInstaller frozen target built;
- package self-test proved frozen runtime and fail-closed scientific policy;
- wrong migration secret and tampered ciphertext rejected;
- production portable → Guided Restore conversion succeeded;
- frozen packaged executable ran the restore worker;
- final log: `P9_OFFMACHINE_PACKAGED_RESTORE=SUCCESS source=macos target=windows`;
- target proof artifact `9721759555`, digest `sha256:18d897632b8ee9381b9eec4ca865cdf419164b1950cf83294f06c86075f0830f`;
- restored `/health`, SQLCipher integrity, marker, `PRAGMA user_version` and media hash verified.

### Windows source → macOS target

- fresh Windows Server 2025 source snapshot: SUCCESS;
- bundle SHA-256: `65394c59e3a77e5ea76f36a82c0fe7bb319cc072cc666f9894307ba286e17a58`;
- source artifact `9721671848`, ZIP digest `sha256:1faab98bd6d785f2d5b07fd69620b5ea865e02d51217a92fbfcc49bc8a5aae1c`;
- source transfer copy deletion asserted;
- fresh macOS 15 ARM64 target downloaded the persisted artifact;
- real macOS PyInstaller frozen target built and strict ad-hoc codesign integrity verified;
- package self-test proved frozen runtime and fail-closed scientific policy;
- wrong migration secret and tampered ciphertext rejected;
- production portable → Guided Restore conversion succeeded;
- frozen packaged executable ran the restore worker;
- final log: `P9_OFFMACHINE_PACKAGED_RESTORE=SUCCESS source=windows target=macos`;
- target proof artifact `9721742568`, digest `sha256:d62d1e0e6d69fbff7b5e3e58d877e932fd53ea2b5ee04c42d05cd98199ddfc09`;
- restored `/health`, SQLCipher integrity, marker, `PRAGMA user_version` and media hash verified.

## Engine truth

- Local daily backup has SQLite/SQLCipher and PostgreSQL implementations.
- Portable `.dcbundle` DR is currently a **cabinet SQLite/SQLCipher path**.
- If the active runtime is PostgreSQL, P9 returns `DR_PORTABLE_ENGINE_UNSUPPORTED`.
- PostgreSQL portable DR is not silently claimed.

## Failure behavior retained

- no destination/secret → `CONFIGURATION_REQUIRED`, no snapshot;
- invalid/local destination → `DR_CONFIGURATION_INVALID`;
- unavailable mount/write probe → `DR_DESTINATION_UNAVAILABLE`;
- insufficient space (`ENOSPC`) → `DR_DISK_FULL`, partial bundle removed;
- hard interruption before sidecar → orphan/`.partial` is never counted by verified-retention logic;
- unsupported PostgreSQL portable path → `DR_PORTABLE_ENGINE_UNSUPPORTED`;
- corruption/tampering → snapshot or restore rejected;
- wrong migration secret → restore conversion rejected;
- retention metadata is updated only after a verified snapshot exists.

## Explicit non-claims

- A local directory on the same physical disk is not DR merely because its path differs.
- A same-job CI temporary directory is not an off-machine proof.
- GitHub artifact persistence is used only as the technical off-runner certification boundary.
- Cloud-provider durability is not claimed by Digital Crown.
- No removable disk/NAS product is certified by this workflow.
- P13 still owns actual cabinet operational setup and human recovery ceremony.

No Vercel.
