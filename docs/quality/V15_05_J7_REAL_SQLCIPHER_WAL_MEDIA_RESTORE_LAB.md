# Digital Crown — LOT05 J7 — genuine SQLCipher / WAL / media restore FUE (fake only)

**Date:** 2026-11-09. **Owner decision:** « Go for it », after LOT05 J1–J7 seven-lane synthetic lab merged and exact-merge PostgreSQL/Windows certification successful.

## Scope and threat model

The actual product has **two distinct mechanisms**:
- \`backend/services/backup_service.py\`: SQLCipher database snapshots via \`sqlcipher_export\`, verification, then Fernet archive. \`restore_backup(..., verify_sqlcipher=False)\` is a generic/legacy helper and its default **must never be interpreted as a verified clinical restore**.
- \`backend/services/guided_restore.py\` and \`guided_restore_worker.py\`: preflight, staged package verification, owner approval & prepared current-cabinet backup, then separate detached worker and DB/media rescues. Guided Restore is **not** the LOT05 legacy SQL importer, and its existing tests mostly exercise plain SQLite.
- SQLCipher write-ahead log (WAL) and media/vault state can be jointly inconsistent if the process dies between several filesystem changes. This lab checks genuine SQLCipher recovery semantics, **not** full power-loss or multi-disk transactional atomicity.

The active J7 question is therefore: **will the real code read committed WAL after simulated process death, produce a decryptable and integrity-checked SQLCipher backup, restore a local clone, and recover original DB+media when Guided Restore fails its smoke check?**

## Test source and proof requirements

New exact test: \`backend/tests/test_lot05_j7_real_sqlcipher_wal_media_fue.py\`; new separate two-OS workflow: \`.github/workflows/v15-05-j7-real-sqlcipher-wal-media-restore.yml\`.

- SQLCipher **native** \`sqlcipher3==0.6.2\` is mandatory (not mocked and not skipped), on GitHub-hosted Windows 2022 / Ubuntu 24.04. Fails closed when dependency unavailable.
- A real subprocess opens a **test-only on-disk** encrypted SQLite DB, selects WAL, commits fabricated \`users\`, \`patients\`, \`truth\`, then exits via \`os._exit(0)\` with uncheckpointed WAL. No actual patient or dental file.
- The real \`BackupService.backup_active_database()\` is exercised with its database-engine import replaced **only** by an in-process engine pointer to a \`pytest.tmp_path\` test DB. Real \`_export_sqlcipher_snapshot\`, SQLCipher \`integrity_check\`, \`_encrypt_file_atomic\`, \`restore_backup(..., verify_sqlcipher=True)\`, real Fernet format and source/restore logical row comparison are used.
- Genuine \`GuidedRestoreService.preflight_file\` and \`prepare\` run against a real encrypted DB+media archive created from fictitious SQLCipher data and ZIP-then-Fernet protected artificial radio/note bytes. The real rescue copy and worker DB/media swap/rollback are exercised.
- **Important test-only exclusions:** no \`request_apply\` on a frozen cabinet executable (it must refuse in test environment); no real patient/owner credentials; no actual app termination/restart or health check (those are mocked); no physical machine migration, real encryption-key transfer, tenant mapping or clinical import.
- Positive case: two real SQLCipher rows (including WAL-only committed content) and both fake media survive the new snapshot and restored clone.
- Negative cases: wrong SQLCipher key cannot publish clone; package hash tampering rejected before apply; wrong owner denied; simulated failed app smoke rolls back to the original SQLCipher DB and original media; no real process launched.
- Cross-OS **SUCCESS of both real native jobs + final aggregate** at the *exact PR SHA* is required before declaring **native fake-only FUE verified**. A running/queued CI or skipped native job is **not green**.

## Do not overclaim

- Previous [LOT05 7-jalon fake-only suite #42635141846](https://github.com/hraaaaf/Digital_crown/actions/runs/42635141846): 7/7 + aggregate PASS, merged [#1245](https://github.com/hraaaaf/Digital_crown/pull/1245) in master \`98055c56c0af2017b18cb13f0a0aef51844f530d\`.
- Previous [post-merge #42641743678](https://github.com/hraaaaf/Digital_crown/actions/runs/42641743678): PostgreSQL 18 + Windows PowerShell both SUCCESS exact merged SHA.
- This new J7 native lab **does not** authorize a clinical import, deploying a new installer, accepting an EULA, changing live media, changing the installed local database, or claiming real cabinet recovery.
- The existing default \`restore_backup(..., verify_sqlcipher=False)\` remains an **audit finding**: it allows a decrypted file to be written without SQLCipher structural verification. The current branch deliberately has **no live runtime change** pending native proof and independent review. Before a production-oriented fix, first confirm all in-repo callers and backward compatibility with plain SQLite. An isolated, verified-copy-only restore is the minimum safe operation; never overwrite active DB via this generic helper.
- Crash testing using \`os._exit\` does **not** prove atomic durability under physical power loss or transactional consistency across independent DB and media filesystems. These require a separate elevated/isolated workstation exercise with backup restore drill, app restart and physical I/O witness (later HUMAN GATE).

## GOAL / SUCCESS / PROOF / NEXT

**GOAL:** real native SQLCipher+WAL crash and full DB/media restore proof on disposable fake-only systems.

**SUCCESS:** all positive and adversarial test cases pass on Ubuntu and Windows at the exact HEAD; no skipped tests, no unmocked app launch; tests leave zero data behind beyond temporary VM lifetime.

**PROOF:** completed Actions run, per-OS logs and privacy-safe JSON artifacts, source SHA and filename inventory.

**NEXT after real proof:** independent review for vulnerabilities, evaluate whether the generic backup restore should require integrity verification by default for SQLCipher, decide a separately authorized product implementation of a clone-first recovery path with full SQLCipher/WAL/media rollback and human gates. Existing clinical LOT05 Import remains disabled.
