# V1-10 — Real cabinet activation closeout

Date: **2026-09-29**

## Status

**Real cabinet activation: VERIFIED.**

This closeout records observed evidence for the installable-certified V1 activation on the cabinet workstation. It does not certify visual UX quality and does not replace the earlier pre-migration audit.

## Exact release

- Repository: `hraaaaf/Digital_crown`
- Certified source commit: `bce60b26059054ba43cf8ec13cd210098e648ea4`
- Release ID: `dc-cabinet-bce60b260590-run36628947897`
- Cabinet Certified Release run: `36628947897`
- CODE_CERTIFIED artifact: `code-certified-dc-cabinet-bce60b260590-run36628947897`
- INSTALLABLE_CERTIFIED: PASS for BASIC / GOLD / ELITE.
- Release verification observed with zero `.pyc` contamination after final restart.

## Safety / backup evidence

A fresh encrypted backup was created before the real activation:

- backup run: `bd4f5094d0d4`
- DB: `db_backup_20260929_213539.sql.enc`
- DB SHA256: `3ba34ad02539ebd0219a52a19d91100bad27c08d8ae828252861e3eae7198bb2`
- media: `media_backup_20260929_213539.zip.enc`
- media files: **2915**
- media SHA256: `2d0e15eb385409edc7893e756987677e14d951a7e3da4987cf8a81b54bd42f8c`

Historical rollback rehearsal was performed on an isolated scratch database, not on the live cabinet database, and restored revision `f7a8b9c0d1e2`.

## Real activation evidence

After resolving two fail-closed startup obstacles (bytecode contamination and the old V0 process occupying port 8005), the exact certified release started successfully.

Observed live endpoints:

- `/api/health` -> HTTP 200, `status=ok`, `database=ok`, `environment=cabinet`, `version=bce60b260590`
- `/api/health/db` -> HTTP 200, `status=ok`
- `/api/health/storage` -> HTTP 200, `status=ok`

The normal user launcher was then tested after stopping the running backend. It selected the exact certified release, restarted it, and the same health endpoint returned HTTP 200 with `version=bce60b260590`. Post-restart `.pyc` count: **0**.

## Patient/document/media preservation

Post-activation integrity snapshot:

- Alembic revision: `v7100000020`
- table count: **120**
- schema SHA256: `449befc3129adb475c216df9e1b599bdceaf85854e90db0f9f758ed71f240912`
- table-data SHA256: `d0155d5741348e36ea223600ca4bb5c2b8943b78132ca9d34e1145a24e716fae`
- historical-relations SHA256: `f96cf443afbf63170926529f14811238bd868b839464b567f413b13734e331ec`
- document archives proved: **434 / 434**
- archive proof SHA256: `b8eb0582618860e02ec8851e3cdbe9c6f9c3fcaa6e73413617113cbf233051fe`
- media files: **2915**
- media bytes: **372138855**
- media manifest SHA256: `e817aa9e598e56a8c4aa1f062d8afe32cd9c26ded7f722fa065756ea3e31325c`
- preservation result: **PASS**

## Known limitation

A Windows AFTER screenshot was created locally, but the remote connector did not provide an observable transferable rendering in the review session. Therefore **no comparative visual UX certification or visual score is claimed by this closeout**. The product owner explicitly accepted live operation as sufficient to proceed.

## Closeout decision

The installation/upgrade/runtime-safety scope of V1-10 is supported by direct runtime, restart, backup, migration and preservation evidence. The screenshot-transfer limitation is non-blocking for this technical closeout and remains outside the technical certification claim.
