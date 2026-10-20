# LOT05 / 05.7-J10D — existing local recovery inventory and synthetic Windows test plan

Reviewed baseline: fe18f45c78b07dd4ff04c3ead74edd193d35c701, 2026-10-20. Static source inspection, not installed runtime proof. Strict J10D scope, no clinical changes.

## Verified code paths
- backend/routers/admin.py: backup endpoint calls BackupService.backup_active_database(); guided restore API exposes preflight, prepare, status, apply.
- backend/services/backup_service.py: SQLCipher uses sqlcipher_export snapshot plus PRAGMA integrity_check, Fernet encryption, temp file and os.replace. SQLite uses sqlite3.backup. Local backup.key generated if missing; DB-only backups retain seven.
- backend/services/guided_restore.py: manifest and file SHA-256 checks, decrypted DB validation, ownership checks, rescue DB preparation, explicit confirmation. request_apply has an unconditional RuntimeError denying clinical restore authority.
- backend/services/guided_restore_worker.py: run immediately raises RuntimeError denying unattested worker. Subsequent rescue/rollback implementation is dormant, not validated runtime behavior.
- backend/services/guided_restore_archive.py: encrypted media extraction and archive path/entry validation primitives.
- backend/scripts/scheduled_backup.py: scheduled DB backup explicitly supports PostgreSQL only; SQLite/SQLCipher yields SKIPPED_UNSUPPORTED_ENGINE. Offsite copy optional.
- backend/scripts/backup_db.py: legacy SQLite backup reads live DB file directly; may omit WAL state if invoked during active writes. Installed reachability unverified.
- backend/scripts/restore_db.py: legacy SQLite restore overwrites DB bytes after --yes; installed reachability unverified.
- installer/DigitalCrown.iss: no direct backup/restore command observed. This does not establish actual Task Scheduler state.

## REQUIRED gaps / test design (none executed)
1. Keep both unconditional restore DENY gates. Original independently attested authority and privileged full-state rollback protection remain unsatisfied. Local-only product direction is not an automatic security waiver.
2. Prove encrypted backup set binding and trusted manifest authenticity: modify manifest, swap DB/media, use wrong/missing key, truncate archive and assert DENY with original data preserved.
3. Synthetic installed Windows: concurrent SQLCipher WAL writes, process termination and physical power cut at staging/DB/media/vault boundaries; verify recovery, media consistency, ACL/SCM identity and no silent data loss.
4. Inspect actual Windows scheduled tasks and installed call graph for legacy scripts, as well as backup.key portability when the original PC is destroyed.
5. Record exact tested SHA, Windows build, disk/cache mode and logs; independent security/reliability review. No patient data.

Internal adversarial perspectives only: security 4/10, reliability 3/10. OPEN / NO-GO / NOT CONVERGED. No cloud, second PC, merge or deployment.
