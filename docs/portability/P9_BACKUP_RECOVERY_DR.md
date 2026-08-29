# P9 — Backup, Recovery & Disaster Recovery

**Status:** ACTIVE — cross-OS off-machine certification prepared. **0 EP credited.**

## Goal

A complete loss of the workstation must not imply loss of the cabinet.

## Success criterion

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

No partial EP is credited.

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

## Technical off-machine storage boundary

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

## Cross-OS packaged certification design

Workflow: `Portability P9 Backup Recovery DR`.

### Windows → macOS

1. fresh Windows source runner creates a real SQLCipher cabinet fixture with `users`, `patients`, a valid owner + `CabinetConfig`, deterministic P9 probe table and media sentinel;
2. production `DisasterRecoveryService.create_verified_snapshot()` creates and verifies the `.dcbundle`;
3. exact bundle SHA + sidecar are persisted off-runner and the local transfer copy is removed;
4. a fresh Apple Silicon target runner downloads those bytes;
5. the target builds the real PyInstaller macOS package and applies ad-hoc codesign integrity;
6. package self-test must report `frozen=true`;
7. the package starts a clean target cabinet and passes `/health`;
8. wrong secret + tampered bundle are rejected;
9. production portable conversion + Guided Restore preflight/prepare run with destination-local keys;
10. the **frozen packaged executable** runs `--guided-restore-worker`;
11. worker smoke check and an independent `/health` pass;
12. restored SQLCipher DB marker/user_version and media hash match the Windows source.

### macOS → Windows

The same proof is repeated from a fresh Apple Silicon source to a fresh `windows-2025` target and the restore worker is executed by `dist/DigitalCrown/DigitalCrown.exe`.

P6/P7 own distribution signing/notarization truth. P9 reuses the certified packaging boundary and does not make a new SmartScreen, Developer ID or notarization claim.

## Engine truth

- Local daily backup has SQLite/SQLCipher and PostgreSQL implementations.
- Portable `.dcbundle` DR is currently a **cabinet SQLite/SQLCipher path**.
- If the active runtime is PostgreSQL, P9 returns `DR_PORTABLE_ENGINE_UNSUPPORTED`.
- PostgreSQL portable DR is not silently claimed.

## Failure behavior

- no destination/secret → `CONFIGURATION_REQUIRED`, no snapshot;
- invalid/local destination → `DR_CONFIGURATION_INVALID`;
- unavailable mount/write probe → `DR_DESTINATION_UNAVAILABLE`;
- insufficient space (`ENOSPC`) → `DR_DISK_FULL`, partial bundle removed;
- hard interruption before sidecar → orphan/`.partial` is never counted by verified-retention logic;
- unsupported PostgreSQL portable path → `DR_PORTABLE_ENGINE_UNSUPPORTED`;
- corruption/tampering → snapshot or restore rejected;
- wrong migration secret → restore conversion rejected;
- retention metadata is updated only after a verified snapshot exists.

## Evidence before final run

Existing P9 targeted tests cover configuration, unavailable destination, disk full, corruption cleanup, sidecar, retention, bundle round-trip, wrong secret/tamper and Guided Restore rollback.

The new cross-OS workflow adds the missing independently persisted storage boundary and frozen clean-target restore proof. **It is not credited until both cross-OS target jobs complete SUCCESS on the final candidate.**

## Explicit non-claims

- A local directory on the same physical disk is not DR merely because its path differs.
- A same-job CI temporary directory is not an off-machine proof.
- GitHub artifact persistence is used only as the technical off-runner certification boundary.
- Cloud-provider durability is not claimed by Digital Crown.
- No removable disk/NAS product is certified by this workflow.
- P13 still owns actual cabinet operational setup and human recovery ceremony.

No Vercel.
