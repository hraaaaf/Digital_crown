# P9 — Backup, Recovery & Disaster Recovery

**Status:** ACTIVE — implementation candidate. **0 EP credited.**

## Goal

A complete loss of the workstation must not imply loss of the cabinet.

## Existing verified foundation

- The historical daily database backup remains enabled and keeps local encrypted restore points.
- That path uses `backup.key`, which is **machine-local**. A copy stored only beside the workstation is not disaster recovery.
- Portable `.dcbundle` already provides inter-machine/inter-OS cabinet export with DB + media, AES-256-GCM, scrypt, integrity manifests and machine-bound secrets excluded.
- Guided Restore already provides preflight, safety point, detached apply, smoke verification and rollback.

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
8. applies retention only to verified bundle + sidecar pairs, so crash leftovers/orphans never evict a valid generation;
9. stores only non-secret status in `backups/last_dr_status.json` using an atomic write.

`DIGITALCROWN_DR_DESTINATION` may be a removable disk, NAS mount or independently synchronized filesystem. A path outside Digital Crown user-data is necessary but **does not prove physical off-machine redundancy**.

## Engine truth

- Local daily backup already has SQLite/SQLCipher and PostgreSQL implementations.
- Portable `.dcbundle` DR is currently a **cabinet SQLite/SQLCipher path**.
- If the active runtime is PostgreSQL, P9 returns `DR_PORTABLE_ENGINE_UNSUPPORTED` instead of pretending a portable DR snapshot exists.
- Extending `.dcbundle` to PostgreSQL is not silently claimed by this lot.

## Failure behavior

- no destination/secret → `CONFIGURATION_REQUIRED`, no snapshot;
- invalid/local destination → `DR_CONFIGURATION_INVALID`;
- unavailable mount/write probe → `DR_DESTINATION_UNAVAILABLE`;
- insufficient space (`ENOSPC`) during probe/export → `DR_DISK_FULL`, partial bundle removed;
- hard interruption before sidecar → orphan/`.partial` is never counted by verified-retention logic;
- unsupported PostgreSQL portable path → `DR_PORTABLE_ENGINE_UNSUPPORTED`;
- corruption/tampering during restore-path verification → snapshot rejected and deleted;
- retention metadata is updated only after a verified snapshot exists.

## CI evidence in this candidate

The P9 workflow executes:

- DR service tests for configuration, unavailable destination, disk full, corruption cleanup, sidecar and retention;
- the existing real `.dcbundle` round-trip tests, including DB + media, wrong secret and tampering;
- the existing Guided Restore safety/rollback suite.

That gives a deterministic **fresh-directory simulation**, not a real packaged clean-machine certification.

## Explicit non-claims

- A local directory on the same physical disk is not certified disaster recovery merely because its path differs.
- Cloud-provider durability is not claimed by Digital Crown.
- CI temporary directories are not equivalent to a real removable disk/NAS and clean packaged workstation.
- P9 does not close until a real external destination is exercised, the produced bundle is restored on a clean packaged target, and Windows ↔ macOS recovery is evidenced where applicable.

## Required final evidence

- scheduled snapshot to a real external destination;
- verified bundle SHA-256 + sidecar and portable round-trip;
- restore on a clean packaged target via Guided Restore;
- corruption/tamper rejection;
- interrupted/unavailable destination behavior;
- insufficient disk-space behavior;
- retention behavior;
- Windows ↔ macOS recovery proof where applicable.
