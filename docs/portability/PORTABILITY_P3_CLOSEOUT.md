# Portability P3 — Cabinet data portability — CLOSEOUT

Status: **CLOSED / VERIFIED**

## Goal
Make the Digital Crown cabinet portable between supported machines and OSes without copying machine-bound secrets.

## Success verified
- canonical encrypted `.dcbundle` created and preflighted;
- SQLCipher cabinet data exported independently of the source machine key;
- cabinet media included and re-encrypted for destination restore;
- manifest/version/integrity contract present;
- `.env`, `backup.key`, `license_vault.bin`, locks/logs/caches excluded;
- Guided Restore reused for prepare/apply/smoke/rollback;
- portability boundary respects `PlatformAdapter`;
- portability harness passes on Windows, macOS and Ubuntu.

## Exact proof
- candidate HEAD: `89708100838b85f3574674de21882684c98be9f6`;
- PR `#222` — merged;
- master merge: `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`;
- Portability Runtime Certification `32605929004` — SUCCESS, Windows/macOS/Ubuntu;
- Settings Guided Restore AFTER `32605928982` — SUCCESS;
- T2 Runtime Browser Certification `32605928994` — SUCCESS;
- Catalog Connected Truth Certification `32605928980` — SUCCESS;
- Patient P7 Final Certification `32605928983` — SUCCESS;
- CI `32605929015` — SUCCESS.

## Security boundary handed to P4
The cabinet bundle deliberately does not transport machine-local secrets or licence vault material. P4 owns re-activation/rebinding, local secret regeneration/storage and session/token invalidation semantics after inter-machine migration.

## Progress
Closed lots: P0, P1, P2, P3.

Credited effort: `5 + 13 + 13 + 13 = 44 EP` out of `162 EP` = **27.2%**.

## Next exact
P4 — Licence & local secrets cross-platform.
